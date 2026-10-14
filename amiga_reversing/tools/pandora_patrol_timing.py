"""Bounded call-by-call interpreter for Pandora's admitted patrol scripts.

This models world-script update calls, not PAL frames or accepted player moves.
Original bytes and captured counters are inputs; no target state is written.
"""
from dataclasses import dataclass, field, replace
import hashlib


@dataclass
class PatrolState:
    pc: int
    xy: tuple[int, int]
    delay: int
    counters: dict[int, int] = field(default_factory=dict)
    flags: int = 0


def tick(data, state, base, opcodes, *, script_start, script_size=200, max_commands=64):
    """One eligible outer object-loop call, including entry delay decrement.

    The outer loop skips flags &0x42 before decrementing. Once eligible, a
    nonzero countdown dispatches on the call that decrements it to zero.
    """
    s = replace(state, counters=dict(state.counters))
    if s.flags & 0x42:
        return s
    if s.delay:
        s.delay -= 1
        if s.delay:
            return s
    names = {v: k.removeprefix('WORLD_CMD_') for k,v in opcodes.items()}
    def word(p):
        if not script_start <= p <= script_start+script_size-2 or p+2 > len(data):
            raise ValueError('patrol operand outside admitted script')
        return s.counters.get(p, int.from_bytes(data[p:p+2], 'big'))
    def signed(p):
        v = word(p); return v-65536 if v & 32768 else v
    for _ in range(max_commands):
        pc = s.pc; name = names.get(word(pc))
        if name == 'SET_POSITION':
            s.xy = (word(pc+2), word(pc+4)); s.pc += 6
        elif name in {'ADD_X','ADD_Y'}:
            axis = int(name == 'ADD_Y'); xy = list(s.xy); xy[axis] += signed(pc+2)
            if not 0 <= xy[axis] < 65536:
                raise ValueError('patrol coordinate wrap is outside model')
            s.xy = tuple(xy); s.pc += 4
        elif name == 'SET_DELAY':
            s.delay = word(pc+2); s.pc += 4
        elif name == 'COPY_RELATIVE_WORD':
            dest = pc+4+signed(pc+2)
            word(dest)
            if word(dest-4) != opcodes['WORLD_CMD_REPEAT_BRANCH_OR_RELOAD']:
                raise ValueError('patrol write is not a repeat counter')
            s.counters[dest] = word(dest-2); s.pc += 4
        elif name == 'REPEAT_BRANCH_OR_RELOAD':
            if word(pc+4):
                s.counters[pc+4] = word(pc+4)-1; s.pc += signed(pc+6)
            else:
                s.counters[pc+4] = word(pc+2); s.pc += 8
        elif name == 'JUMP_ABSOLUTE':
            s.pc = (word(pc+2)*65536+word(pc+4))-base
        elif name == 'SET_NODE_FOR_FLAG3_CLEAR':
            s.pc += 6
        elif name == 'SET_NODE_SEQUENCE_FOR_FLAG3_CLEAR':
            s.pc += 10
        else:
            raise ValueError(f'unmodelled patrol command {name} at {pc:#x}')
        if s.delay:
            return s
    raise ValueError('patrol command budget exhausted')


def repeat_counter_offsets(data, start, opcodes, *, size=200):
    """Decode original straight-line script storage, accepting only this subset."""
    names = {v: k.removeprefix('WORLD_CMD_') for k,v in opcodes.items()}
    lengths = {'SET_POSITION':6, 'ADD_X':4, 'ADD_Y':4, 'SET_DELAY':4,
               'COPY_RELATIVE_WORD':4, 'REPEAT_BRANCH_OR_RELOAD':8,
               'SET_NODE_FOR_FLAG3_CLEAR':6, 'SET_NODE_SEQUENCE_FOR_FLAG3_CLEAR':10,
               'JUMP_ABSOLUTE':6}
    pc, counters = start, []
    while pc < start+size:
        name = names.get(int.from_bytes(data[pc:pc+2], 'big'))
        if name not in lengths or pc+lengths[name] > start+size:
            raise ValueError('unknown original patrol layout')
        if name == 'REPEAT_BRANCH_OR_RELOAD':
            counters.append(pc+4)
        pc += lengths[name]
    return counters


def state_from_capture(phase, data, base, opcodes, *, actor_source, script_start,
                       fields, script_size=200):
    """Admit a canonical capture only if live script differs at repeat counters.

    Field offsets come from the native effective record schema. All required
    record/script bytes must be present; conflicting overlapping reads are refused.
    """
    identity = phase['payload']
    if (phase['status'] != 'hit' or identity['status'] != 'pc_matched'
            or int(identity['runtime_base'],0) != base):
        raise ValueError('patrol checkpoint has no canonical identity')
    if identity['payload_sha256'] != hashlib.sha256(data).hexdigest():
        raise ValueError('patrol checkpoint payload mismatch')
    memory = {}
    for read in phase['capture']['memory_reads']:
        address = int(read['address'],0)
        for i,v in enumerate(bytes.fromhex(read['bytes'])):
            if address+i in memory and memory[address+i] != v:
                raise ValueError('conflicting patrol capture')
            memory[address+i] = v
    def captured(address,size):
        try:
            return bytes(memory[address+i] for i in range(size))
        except KeyError as exc:
            raise ValueError('incomplete patrol capture') from exc
    def field(name):
        offset,size = fields[name]
        return int.from_bytes(captured(base+actor_source+offset,size),'big')
    counters = repeat_counter_offsets(data,script_start,opcodes,size=script_size)
    live_script = captured(base+script_start,script_size)
    mutable = {p-script_start+i for p in counters for i in range(2)}
    if any(v != data[script_start+i] for i,v in enumerate(live_script) if i not in mutable):
        raise ValueError('live patrol code differs outside admitted counters')
    if field('initial_behavior_script_ptr') != base+script_start:
        raise ValueError('actor has a different initial script')
    return PatrolState(field('behavior_script_ptr')-base,
                       (field('world_x'),field('world_y')),
                       field('behavior_script_delay_ticks'),
                       {p:int.from_bytes(live_script[p-script_start:p-script_start+2],'big') for p in counters},
                       field('world_object_flags'))


def assess_crossing(data, gate, base, opcodes, path, *, script_start,
                    max_calls_per_move, initial_input_lag=1):
    """Check all admitted actor times for each player pose, including pauses.

    The caller must establish its move/camera bound separately. This does not
    infer a frame rate, terrain clearance, other actors or runtime qualification.
    """
    if (type(max_calls_per_move) is not int or not 1 <= max_calls_per_move <= 64
            or type(initial_input_lag) is not int or not 0 <= initial_input_lag <= 64
            or not 1 <= len(path) <= 64):
        raise ValueError('crossing requires bounded route and timing inputs')
    future = [gate]
    for _ in range(max_calls_per_move*(len(path)+1)+initial_input_lag):
        future.append(tick(data,future[-1],base,opcodes,script_start=script_start))
    checks = []
    for i,(direction,pose) in enumerate(path,1):
        lo,hi = i-1,max_calls_per_move*(i+1)+initial_input_lag
        unsafe = [t for t in range(lo,hi+1)
                  if abs(pose[0]-future[t].xy[0]) < 24
                  and abs(pose[1]-future[t].xy[1]) < 16]
        checks.append({'move':i,'direction':direction,'pose':pose,
                       'actor_call_window':[lo,hi],'unsafe_calls':unsafe})
    return {'status':'conditional_clearance' if not any(c['unsafe_calls'] for c in checks)
            else 'unsafe', 'checks':checks,
            'max_loop_calls_per_move':max_calls_per_move,
            'initial_input_lag_calls':initial_input_lag}

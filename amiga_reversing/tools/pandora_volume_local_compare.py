"""Bounded CPU-only relocation comparison; never resumes or edits a game.

The donor is a canonical read-only Copperline checkpoint capture. Local calls,
stack return frames and guard/volume inputs are explicit modeled inputs. Results
establish neither normal gameplay reachability nor Paula hardware behaviour.
"""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path

from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.derived_artifact import validate_manifest
from amiga_reversing.tools.direct_payload_adapter import load_contract

ROOT=Path(__file__).resolve().parents[2]
BASE=0x10000
ENTRY=0x652fe
OLD=0x5dd00
NEW=0x65400
RETURN=0x800
MEMORY_SIZE=0x1000000

class Diag(C.Structure):
    _fields_=[('severity',C.c_uint32),('code',C.c_uint32),('message',C.c_char*512)]
class Diagnostics(C.Structure):
    _fields_=[('count',C.c_size_t),('dropped',C.c_size_t),('items',Diag*8)]
class State(C.Structure):
    _fields_=[('d',C.c_uint32*8),('a',C.c_uint32*8),('c',C.c_uint32*32),('pc',C.c_uint32),('sr',C.c_uint16)]
class Range(C.Structure):
    _fields_=[('start',C.c_uint32),('end',C.c_uint32)]
class Trace(C.Structure):
    _fields_=[('steps',C.c_size_t),('start_pc',C.c_uint32),('stop_pc',C.c_uint32),
              ('write_start',C.c_uint32),('write_end',C.c_uint32),('writes',C.c_size_t),
              ('range_count',C.c_size_t),('overflow',C.c_uint8),('reserved',C.c_uint8*7),
              ('ranges',Range*32),('stop_reason',C.c_int),('diagnostics',Diagnostics)]


def sha(data):return hashlib.sha256(data).hexdigest()


def load_context(path, original):
    donor=json.loads(path.read_text());o=donor.get('observation',{})
    phases=o.get('scenario',{}).get('phases',[])
    if len(phases)!=1:raise ValueError('one canonical routine-context capture required')
    p=phases[0];identity=p.get('payload',{})
    if (donor.get('status')!='ok' or p.get('status')!='hit'
            or identity.get('status')!='pc_matched' or identity.get('payload_offset')!='0x5ca'
            or int(identity.get('runtime_base','0'),0)!=BASE
            or identity.get('payload_sha256')!=sha(original)
            or o.get('checkpoint',{}).get('status')!='restored'
            or o.get('direct_payload_handoff',{}).get('status')!='verified'
            or o.get('direct_payload_handoff',{}).get('payload_sha256')!=sha(original)
            or o.get('reverse_boundary',{}).get('materialization',{}).get('status')!='verified'
            or o.get('reverse_boundary',{}).get('materialization',{}).get('copied_sha256')!=sha(original[:349040])):
        raise ValueError('requires verified original-checkpoint donor and canonical5CA identity')
    capture=p['capture'];memory={}
    for read in capture['memory_reads']:
        address=int(read['address'],0)
        for i,value in enumerate(bytes.fromhex(read['bytes'])):
            if address+i in memory and memory[address+i]!=value:raise ValueError('conflicting donor reads')
            memory[address+i]=value
    def read(address,size):
        try:return bytes(memory[address+i] for i in range(size))
        except KeyError as e:raise ValueError('donor is missing required routine input') from e
    for start,size in ((0x552de,146),(0x4d872,128)):
        if read(BASE+start,size)!=original[start:start+size]:raise ValueError('live routine code differs from original')
    regs=capture['registers'];a6=int(regs['a6'],0)
    for address,size in ((a6+0x33d,1),(0x5c21a,1),(0x5c352,4),(OLD,8)):
        read(address,size)
    return donor,memory,regs


def cpu(regs):
    s=State()
    for k in ('d','a'):
        for i in range(8):getattr(s,k)[i]=int(regs[f'{k}{i}'],0)
    s.sr=int(regs['sr'],0);s.pc=ENTRY
    s.a[7]-=4  # Explicit local call frame, never written to Copperline.
    return s


def load_engine(path):
    lib=C.CDLL(str(path.resolve()));run=lib.m68k_simulate_run_concrete
    run.argtypes=[C.c_uint8,C.POINTER(C.c_uint8),C.c_size_t,C.POINTER(State),C.c_size_t,
                  C.c_uint32,C.c_uint32,C.c_void_p,C.POINTER(Trace)]
    run.restype=C.c_int
    return run


def execute(run, image, donor_memory, regs, *, relocated, dead, armed, volume, xy=None):
    memory=bytearray(MEMORY_SIZE);memory[BASE:BASE+349040]=image[:349040]
    for address,value in donor_memory.items():memory[address]=value
    # The derived image changes only manifest bytes; never inherit original live
    # code over the derived code. Captured data cells stay identical otherwise.
    if relocated:
        memory[BASE+0x552de:BASE+0x55370]=image[0x552de:0x55370]
    a6=int(regs['a6'],0);actual_flags=memory[0x5c21a];actual_shared=memory[a6+0x33d]
    memory[0x5c21a]=(actual_flags&~2)|(2 if dead else 0)
    memory[a6+0x33d]=(actual_shared&~1)|(1 if armed else 0)
    if xy is not None:memory[0x5c352:0x5c356]=b''.join(v.to_bytes(2,'big') for v in xy)
    memory[OLD:OLD+2]=b'\x00\x40' if relocated else volume.to_bytes(2,'big')
    memory[NEW:NEW+8]=(volume.to_bytes(2,'big') if relocated else b'\xa5\x5a')+b'\xc3'*6
    s=cpu(regs);memory[s.a[7]:s.a[7]+4]=RETURN.to_bytes(4,'big')
    start=bytes(memory);buffer=(C.c_uint8*len(memory)).from_buffer(memory);pcs=[];writes=[]
    for _ in range(128):
        if s.pc==RETURN:break
        if not (0x652de<=s.pc<0x65370 or 0x5d872<=s.pc<0x5d8f2):raise ValueError(f'unadmitted local control flow {s.pc:#x}')
        pcs.append(s.pc);trace=Trace()
        rc=run(0,buffer,len(memory),C.byref(s),1,RETURN,RETURN+2,None,C.byref(trace))
        if rc or trace.steps!=1 or trace.overflow or any(d.severity>=3 for d in trace.diagnostics.items[:trace.diagnostics.count]):
            messages=[bytes(d.message).split(b'\0')[0].decode() for d in trace.diagnostics.items[:trace.diagnostics.count]]
            raise ValueError(f'generated CPU simulation refused: {messages}')
        for span in trace.ranges[:trace.range_count]:writes.append([span.start,span.end])
    else:raise ValueError('local instruction budget exhausted')
    if s.pc!=RETURN:raise ValueError('local routine did not return')
    changes=[[i,start[i],v] for a,b in sorted(set(map(tuple,writes))) for i,v in enumerate(memory[a:b],a) if start[i]!=v]
    address=NEW if relocated else OLD
    logical=int.from_bytes(memory[address:address+2],'big')
    if memory[NEW+2:NEW+8]!=b'\xc3'*6:raise ValueError('relocation lease guard changed')
    if relocated and memory[OLD:OLD+2]!=b'\x00\x40':raise ValueError('old-address guard changed')
    # Compare actual write ranges/values, including unchanged writes and stack,
    # with exactly the logical volume address normalized.
    effects=sorted(set((OLD+(i-NEW) if relocated and NEW<=i<NEW+2 else i,memory[i])
                       for a,b in writes for i in range(a,b)))
    return {'state':{'d':list(s.d),'a':list(s.a),'c':list(s.c),'pc':s.pc,'sr':s.sr},
            'logical_word':logical,'effects':effects,'pcs':pcs,'steps':len(pcs),
            'changes':changes,'BYTE_writer_executed':0x652f0 in pcs}


def compare_store(run, original, derived, regs, *, values=None):
    """Exhaustive word-domain check of the actual manifest BYTE instruction.

    This bypasses the routine's guard by explicit local PC selection. It is an
    instruction contract check, never an assertion that gameplay reaches it.
    """
    buffers=[]
    for image,address in ((original,OLD),(derived,NEW)):
        memory=bytearray(0x66000);memory[BASE:BASE+349040]=image[:349040]
        memory[OLD:OLD+8]=b'\x00\x40'+b'\xa7'*6
        memory[NEW:NEW+8]=b'\xa5\x5a'+b'\xc3'*6
        buffers.append((memory,(C.c_uint8*len(memory)).from_buffer(memory),address))
    outputs=[]
    for value in (range(65536) if values is None else values):
        states=[];words=[]
        for memory,buffer,address in buffers:
            memory[address:address+2]=value.to_bytes(2,'big')
            state=cpu(regs);state.a[7]+=4;state.pc=0x652f0
            trace=Trace();rc=run(0,buffer,len(memory),C.byref(state),1,0x652f8,0x652fa,None,C.byref(trace))
            if (rc or trace.steps!=1 or trace.stop_reason!=1 or trace.writes!=1
                    or trace.range_count!=1 or trace.ranges[0].start!=address or trace.ranges[0].end!=address+1):
                raise ValueError('BYTE instruction did not make exactly one byte write')
            word=int.from_bytes(memory[address:address+2],'big')
            if word!=(0x4000|(value&255)):raise ValueError('BYTE lane/low-byte preservation failed')
            if memory[OLD+2:OLD+8]!=b'\xa7'*6 or memory[NEW+2:NEW+8]!=b'\xc3'*6:raise ValueError('store guard changed')
            states.append(bytes(state));words.append(word)
        if states[0]!=states[1] or words[0]!=words[1]:raise ValueError('local BYTE state mismatch')
        outputs.append(words[0])
    return {'status':'exhaustive_local_BYTE_instruction_equivalence','initial_words_tested':len(outputs),
            'original_instruction':original[0x552f0:0x552f8].hex(),'derived_instruction':derived[0x552f0:0x552f8].hex(),
            'instruction_source_offset':'0x552f0','output_rule':'0x4000 | (input & 0xff)',
            'registers_CCR_PC_equal':True,'write_width':1,'guards_unchanged':True,
            'outputs_sha256':sha(b''.join(v.to_bytes(2,'big') for v in outputs)),
            'scope':'Modeled entry directly at the writer. Guard reachability, reset helper, Paula and game execution are excluded.'}


def compare(target, context, manifest_path, library):
    original=resolve_project_paths(target).binary_source.path.read_bytes()
    contract=load_contract('pandora')
    if target!=contract.target_id or sha(original)!=contract.payload_sha256:
        raise ValueError('local comparison supports the identified Pandora original only')
    manifest,derived_path=validate_manifest(manifest_path,target);derived=derived_path.read_bytes()
    if manifest['original_sha256']!=sha(original) or manifest['region']['runtime_address']!=OLD or manifest['placement']['runtime_address']!=NEW or manifest['region']['size']!=2:
        raise ValueError('requires the closed two-byte Pandora volume plan')
    ledger=manifest['rewrite_ledger'];changed=set()
    for entry in ledger:
        off=entry['source_offset'];before=bytes.fromhex(entry['before']);after=bytes.fromhex(entry['after'])
        if original[off:off+len(before)]!=before or derived[off:off+len(after)]!=after:raise ValueError('rewrite ledger mismatch')
        changed.update(range(off,off+len(before)))
    if len(original)!=len(derived) or any(a!=b and i not in changed for i,(a,b) in enumerate(zip(original,derived))):raise ValueError('unlisted image changes')
    donor,projection,regs=load_context(context,original);run=load_engine(library);cases=[]
    actual_dead=bool(projection[0x5c21a]&2);actual_armed=bool(projection[int(regs['a6'],0)+0x33d]&1)
    specs=[('captured_guard',actual_dead,actual_armed,0x40,None),('dead_unarmed',True,False,0x40,None),
           ('alive_far_armed',False,True,0x1234,None),('alive_near_armed',False,True,0x40,(808,154))]
    specs += [('dead_armed_'+hex(v),True,True,v,None) for v in (0x40,0x6,0x1ff,0xaa55,0xffff)]
    refusal=None
    for name,dead,armed,volume,xy in specs:
        a=execute(run,original,projection,regs,relocated=False,dead=dead,armed=armed,volume=volume,xy=xy)
        b=execute(run,derived,projection,regs,relocated=True,dead=dead,armed=armed,volume=volume,xy=xy)
        shared_effects=[e for e in a['effects'] if int(regs['a6'],0)+0x33d<=e[0]<int(regs['a6'],0)+0x33d+4]
        player=xy or (int.from_bytes(bytes(projection[0x5c352+i] for i in range(2)),'big'),
                      int.from_bytes(bytes(projection[0x5c354+i] for i in range(2)),'big'))
        distance=abs(player[0]-840)+abs(player[1]-168)
        expected_word=(0x4000|(volume&255)) if dead and armed else volume
        if not dead:expected_word=64-(distance>>2) if distance<256 else (64 if armed else volume)
        if len(shared_effects)!=1 or a['BYTE_writer_executed'] != bool(dead and armed) or a['logical_word']!=expected_word:
            refusal={'status':'refused_generated_simulator_bit_memory_width','case':name,
                     'expected_local_BYTE':bool(dead and armed),'observed_local_BYTE':a['BYTE_writer_executed'],
                     'shared_flag_write_effects':shared_effects,'expected_flag_write_width':1,'observed_flag_write_width':len(shared_effects),
                     'KB_rule':'size_by_ea_category: register=l, memory=b',
                     'gap':'Unsized bit-operation memory operands use instruction-size fallback=long for concrete reads/writes. The generated binding must consume the existing KB EA-category width rule.'}
            break
        if (a['state'],a['logical_word'],a['effects'],a['pcs'])!=(b['state'],b['logical_word'],b['effects'],b['pcs']):raise ValueError(f'local equivalence failed: {name}')
        cases.append({'name':name,'modeled_inputs':{'Feed_defeated':dead,'shared_armed':armed,'initial_volume':volume,'player_xy_override':xy},
                      'steps_per_layout':a['steps'],'BYTE_writer_executed_locally':a['BYTE_writer_executed'],
                      'logical_output':f'{a["logical_word"]:04x}','normalized_write_effects':a['effects'],
                      'normalized_effect_sha256':sha(json.dumps(a['effects']).encode()),'CPU_state_equal':True})
    return {'schema_version':1,'target_id':target,'status':'local_BYTE_equivalence_routine_comparison_refused' if refusal else 'bounded_local_routine_and_BYTE_equivalence','original_sha256':sha(original),'derived_sha256':sha(derived),
            'manifest_sha256':sha(manifest_path.read_bytes()),'context_sha256':sha(context.read_bytes()),'backend_sha256':sha(library.read_bytes()),
            'checkpoint_provenance':donor['observation']['checkpoint'],'cases_before_refusal':cases,'routine_comparison':refusal or {'status':'bounded_CPU_only_routine_equivalence'},
            'BYTE_instruction_comparison':compare_store(run,original,derived,regs),
            'local_call_context':{'entry_source_offset':'0x552fe','donor_source_offset':'0x5ca','return_pc':RETURN,'SP_adjustment':-4,'instruction_budget':128},
            'limits':['CPU-only projection, with explicit modeled call/guard/data inputs; no game snapshot or gameplay predicate was edited.',
                      'Uncaptured cells use original image or zero shadow. Modeled cases avoid audio initialization; reset helper writes are compared, including custom-register write intents.',
                      'No interrupts, Amiga set/clear register semantics, Paula/DMA timing, allocation or normal gameplay reachability proof.',
                      'Generated spec-driven CPU backend used; an independent machine68k oracle is unavailable in this environment.',
                      'Local BYTE execution is separate from the still-unobserved normal-gameplay BYTE path and original/relocated game comparison.']}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',required=True);p.add_argument('--context',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--library',type=Path,default=ROOT/'src/build/libamiga_backend.so');p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    result=compare(a.target,a.context,a.manifest,a.library);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'words':result['BYTE_instruction_comparison']['initial_words_tested'],'routine_status':result['routine_comparison']['status']}))
    return 2 if result['routine_comparison']['status'].startswith('refused_') else 0
if __name__=='__main__':raise SystemExit(main())

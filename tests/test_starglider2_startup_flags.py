"""The bounded observer must not shorten input holds or fabricate source identity."""
import pytest
from amiga_reversing.tools.starglider2_flight_probe import StartupFlagObserver, main


class Client:
    def __init__(self, events, *, wrong_filter=False, changed_code=False):
        self.base = 0x60000
        self.original = b'\x4e\x71' * 32
        self.events = list(events)
        self.wrong_filter = wrong_filter
        self.changed_code = changed_code
        self.armed = None
        self.runs, self.removed, self.inputs = [], [], []
        self.flags = bytearray(b'\xff\xff')
        self.pc = 0x1008

    def request(self, method, params=None):
        if method == 'break.add':
            self.armed = dict(params)
            return dict(id=7)
        if method == 'break.list':
            return dict(breaks=[dict(id=7, **{**self.armed,
                'len': 3 if self.wrong_filter else self.armed['len']})])
        raise AssertionError(method)  # No mem.write/register injection surface.

    def remove_breakpoint(self, ident):
        self.removed.append(ident)

    def registers(self):
        return dict(pc=self.pc, a6=self.base, sp=0x3370)

    def read_memory(self, addr, size):
        if addr == self.base + 0x205 and size == 2:
            return bytes(self.flags)
        if addr == self.pc and size == 16:
            return b'\x00' * 16 if self.changed_code else self.original[addr-0x1000:addr-0x1000+size]
        raise AssertionError((addr, size))

    def key(self, rawkey, *, pressed):
        self.inputs.append((rawkey, pressed))

    def run_until(self, params, *, timeout):
        self.runs.append((dict(params), timeout))
        event = self.events.pop(0)
        access = event.get('access')
        if access:
            self.pc = access['pc']
            for i in range(access['size']):
                offset = access['addr'] + i - self.base - 0x205
                if 0 <= offset < 2:
                    self.flags[offset] = (access['value'] >> (8 * (access['size'] - 1 - i))) & 255
        return event


def bus(addr, value):
    return dict(reason='mmio', frame=9, pc=0x100C,
                access=dict(access='write', addr=addr, size=2, value=value, pc=0x1008))


def test_split_bus_writes_keep_original_absolute_goal_and_input(tmp_path):
    c = Client([bus(0x60204, 0xAB00), bus(0x60206, 0x00CD), dict(reason='target', frame=25)])
    stages = []
    o = StartupFlagObserver(c, c.base, c.original, lambda n, v: stages.append((n, v)))
    o.key(64, pressed=True)
    assert o.run_until(dict(frame=25), timeout=10) == dict(reason='target', frame=25)
    o.key(64, pressed=False)
    assert len(o.hits) == 2 and o.cleared == {0x205: 0, 0x206: 1}
    assert c.flags == b'\x00\x00'
    assert all(h['original_bytes_match'] and h['source_offset'] == 8 for h in o.hits)
    assert [p for p, t in c.runs] == [dict(frame=25)] * 3
    assert all(0 < t <= 10 for p, t in c.runs)
    assert c.inputs == [(64, True), (64, False)]
    o.close_watch()
    assert c.removed == [7]  # Retired once, including later ExitStack cleanup.


def test_runtime_modified_instruction_is_not_claimed_as_static_source():
    c = Client([bus(0x60204, 0), bus(0x60206, 0), dict(reason='target', frame=25)], changed_code=True)
    o = StartupFlagObserver(c, c.base, c.original, lambda *a: None)
    o.run_until(dict(frame=25), timeout=10)
    assert all(not h['original_bytes_match'] and h['source_offset'] is None for h in o.hits)


def test_watch_filter_mismatch_stops_before_execution_and_removes_owned_watch():
    c = Client([], wrong_filter=True)
    with pytest.raises(ValueError, match='readback differs'):
        StartupFlagObserver(c, c.base, c.original, lambda *a: None)
    assert c.removed == [7] and not c.runs


def test_unrelated_trap_is_not_accepted():
    c = Client([bus(0x60300, 0)])
    o = StartupFlagObserver(c, c.base, c.original, lambda *a: None)
    try:
        with pytest.raises(ValueError, match='Unexpected memory trap'):
            o.run_until(dict(frame=25), timeout=10)
        assert not o.hits
    finally:
        o.close_watch()


def test_write_budget_is_a_failure_not_a_no_hit_success():
    c = Client([bus(0x60204, 0), bus(0x60206, 0)])
    o = StartupFlagObserver(c, c.base, c.original, lambda *a: None, max_hits=1)
    try:
        with pytest.raises(ValueError, match='budget exhausted'):
            o.run_until(dict(frame=25), timeout=10)
        assert len(o.hits) == 1
    finally:
        o.close_watch()


def test_startup_route_cannot_be_combined_with_another_observation_route():
    with pytest.raises(SystemExit) as exc:
        main(['--inputs', 'unused', '--rom', 'unused', '--copperline', 'unused',
              '--output', 'unused', '--answer-selected-protection-request',
              '--observe-startup-flags', '--observe-model-paths'])
    assert exc.value.code == 2


def test_source_binding_uses_coordinates_and_retains_alias_ambiguity():
    from amiga_reversing.tools.starglider2_flight_probe import _bind_instruction_windows
    data = bytes(range(64))
    hit = dict(triggering_pc=0x1010, instruction_window_hex=data[16:32].hex())
    row, = _bind_instruction_windows([hit], [('encoded', 0x1000, data), ('decoded', 0x1000, data)])
    assert row['status'] == 'ambiguous' and len(row['matches']) == 2
    assert {m['source_offset'] for m in row['matches']} == {16}
    row, = _bind_instruction_windows([hit], [('encoded', 0x2000, data), ('decoded', 0x1000, data)])
    assert row['status'] == 'matched' and row['matches'][0]['target_id'] == 'decoded'


def test_source_binding_never_promotes_changed_or_short_windows():
    from amiga_reversing.tools.starglider2_flight_probe import _bind_instruction_windows
    data = bytes(range(64))
    row, = _bind_instruction_windows([dict(triggering_pc=0x1010, instruction_window_hex='ff'*16)],
                                    [('source', 0x1000, data)])
    assert row['status'] == 'not_matched' and not row['matches']
    with pytest.raises(ValueError, match='16-byte'):
        _bind_instruction_windows([dict(triggering_pc=0x1010, instruction_window_hex='ffff')],
                                  [('source', 0x1000, data)])

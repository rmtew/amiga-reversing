"""Original countdown/formatter instructions with controlled RAM and service calls.

No asynchronous frames, DMA, ordinary UI admission or visible result is modeled.
The real compact renderer and status FIFO are retained; audio calls are observed
at their entry where the caller's programmed request is the question.
"""
import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, RETURN, TARGET, cpu_fixture
from tests.test_pandora_render_order import sequencer
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_message_queue import initialize, APP, HEAD, TAIL, CONTEXT

COUNTDOWN, FORMAT, BUFFER, AUDIO = 0x2D5A, 0x2E8A, BASE+0x2EE0, 0x4D330
PLAYER = BASE+0x4C322


def make_deadline(cpu_fixture, title_slots, oracle):
    cpu,memory,schemas,read,write,run=cpu_fixture
    if oracle:
        machine68k=pytest.importorskip('machine68k')
        machine=machine68k.Machine(machine68k.CPUType.M68000,len(memory)//1024)
        registers=[getattr(machine68k.Register,f'{bank}{i}') for bank in ['D','A'] for i in range(8)]
        class Stopped(Exception):pass
        boundary=[RETURN,0,0]
        def hook(pc):
            if pc==boundary[0]:raise Stopped
            boundary[1]+=1
            assert boundary[1]<boundary[2],hex(pc)
        machine.cpu.set_instr_hook_callback(hook)
        def run(source,stop=None,budget=512):
            cpu.a[7]=0x9000;write(0x9000,RETURN)
            machine.mem.w_block(0,bytes(memory))
            machine.cpu.w_sr(cpu.sr)
            for register,value in zip(registers,list(cpu.d)+list(cpu.a)):machine.cpu.w_reg(register,int(value))
            machine.cpu.w_pc(BASE+source);boundary[:]=[RETURN if stop is None else BASE+stop,0,budget]
            with pytest.raises(Stopped):machine.cpu.execute(budget*200)
            memory[:]=machine.mem.r_block(0,len(memory))
            for i in range(8):
                cpu.d[i]=machine.cpu.r_reg(registers[i]);cpu.a[i]=machine.cpu.r_reg(registers[i+8])
            cpu.sr=machine.cpu.r_sr();cpu.pc=machine.cpu.r_pc()
    else:
        def run(source,stop=None,budget=512):
            # The bounded write-summary may fill; guest bytes below are authoritative.
            trace=sequencer(cpu,memory,write)(source,stop=stop,budget=budget)
            assert trace.stop_reason==1,(hex(cpu.pc),trace.stop_reason)
    slots=title_slots
    slots.setdefault('app_four_digit_text_skip_mask',0x2C2)
    def put(name,value,size=1):write(APP+slots['app_'+name],value,size)
    def get(name,size=1):return read(APP+slots['app_'+name],size)
    def prepare(value=0x1234,divider=1,ui=0,events=0,player=0):
        initialize(cpu_fixture,slots)
        put('earth_orbit_countdown_bcd',value,2);put('earth_orbit_countdown_divider',divider)
        put('ui_flags',ui);put('game_event_flags',events);put('status_flags',0xF7)
        write(PLAYER+schemas['world_object_shared_prefix']['world_object_flags'],player,1)
        put('font_glyph_bitmap_table_ptr',0x85000,4)
        memory[0x85000:0x85800]=bytes((i*13+7)&255 for i in range(2048))
        put('text_cursor_ptr',0x80000,4);put('text_plane_mask',15)
        write(APP+CONTEXT,32,1)  # Queue real status messages without opening UI.
        return cpu,memory,read,write,run
    return cpu,memory,read,write,run,put,get,prepare


@pytest.fixture
def deadline(cpu_fixture,title_slots):return make_deadline(cpu_fixture,title_slots,True)


@pytest.fixture
def native_deadline(cpu_fixture,title_slots):return make_deadline(cpu_fixture,title_slots,False)


def bcd(number):return int(str(number),16)


def test_all_valid_bcd_values_decrement_and_zero_does_not_announce_again(deadline):
    cpu,memory,read,write,run,put,get,prepare=deadline
    prepare(ui=2)
    for number in range(10000):
        put('earth_orbit_countdown_bcd',bcd(number),2);put('earth_orbit_countdown_divider',1)
        stop=AUDIO if number>1 and (number-1)%100==0 else None
        run(COUNTDOWN,stop=stop,budget=256)
        assert get('earth_orbit_countdown_bcd',2)==bcd(max(0,number-1))
        assert get('earth_orbit_countdown_divider')==(4 if number else 0)
        assert read(APP+TAIL)==APP+HEAD
        if stop is not None:assert cpu.d[0]&65535==0x306


def test_every_divider_byte_wraps_and_only_old_one_decrements(deadline):
    cpu,memory,read,write,run,put,get,prepare=deadline
    prepare(ui=2)
    for divider in range(256):
        put('earth_orbit_countdown_bcd',0x1234,2);put('earth_orbit_countdown_divider',divider)
        run(COUNTDOWN)
        assert get('earth_orbit_countdown_bcd',2)==(0x1233 if divider==1 else 0x1234)
        assert get('earth_orbit_countdown_divider')==(4 if divider==1 else (divider-1)&255)


def test_whole_hundred_alarm_is_requested_on_each_service_until_the_next_decrement(deadline):
    cpu,memory,read,write,run,put,get,prepare=deadline
    prepare(value=0x101,ui=2)
    for divider in [4,3,2,1]:
        run(COUNTDOWN,stop=AUDIO)
        assert get('earth_orbit_countdown_bcd',2)==0x100
        assert get('earth_orbit_countdown_divider')==divider
        assert cpu.d[0]&65535==0x306
    run(COUNTDOWN)
    assert get('earth_orbit_countdown_bcd',2)==0x99
    assert get('earth_orbit_countdown_divider')==4


def test_expiry_announcements_require_the_decrement_and_post_draw_gates(deadline, cpu_fixture):
    cpu,memory,read,write,run,put,get,prepare=deadline
    for ui in range(256):
        for events,player in [(0,0),(32,0),(0,2)]:
            prepare(value=1,ui=ui,events=events,player=player)
            run(COUNTDOWN,budget=4096)
            admitted=not(ui&2 or events&32 or player&2)
            assert get('earth_orbit_countdown_bcd',2)==0
            assert read(APP+TAIL)==APP+HEAD+8*admitted
            if admitted:
                messages=[bytes(memory[p:memory.index(0,p)]) for p in [read(APP+HEAD),read(APP+HEAD+4)]]
                assert messages==[b'EARTH ORBIT ESTABLISHED, MUTANT SPORES RELEASED.',b'TOTAL DESTRUCTION OF HUMANITY IMMINENT.']
            before=bytes(memory[APP+HEAD:APP+HEAD+68])
            # A later zero visit never retries a skipped notification.
            put('ui_flags',0);put('game_event_flags',0);write(PLAYER+cpu_fixture[2]['world_object_shared_prefix']['world_object_flags'],0,1)
            put('earth_orbit_countdown_divider',1)
            run(COUNTDOWN)
            assert bytes(memory[APP+HEAD:APP+HEAD+68])==before


def test_countdown_writes_the_skip_mask_only_when_it_draws_and_flashes_with_low_frame_byte(deadline):
    cpu,memory,read,write,run,put,get,prepare=deadline
    metadata=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    layout=next(a for a in metadata.data_block_layouts if a.name=='nearby_distance_overlay')
    color=BASE+layout.source_start+next(f.offset for f in next(t for t in metadata.custom_structs if t.name=='ui_overlay_descriptor').fields if f.name=='text_color')
    for ui in range(256):
        prepare(value=0x1235,ui=ui);put('four_digit_text_skip_mask',0xA5)
        run(COUNTDOWN,budget=4096)
        assert get('four_digit_text_skip_mask')==(0xA5 if ui&2 else 8 if ui&0x14==0x14 else 0)
        if not ui&2:assert get('text_plane_mask')==read(color,1)
    for frame in [0,1,15,16,255,0x123456AB]:
        prepare(value=0x101);put('frame_counter',frame,4)
        run(COUNTDOWN,stop=AUDIO,budget=4096)
        assert get('text_plane_mask')==frame&255


def test_formatter_accepts_hex_nibbles_suppresses_leading_zero_and_preserves_saved_registers(native_deadline):
    cpu,memory,read,write,run,put,get,prepare=native_deadline
    prepare()
    for value in [0]+[digit<<(4*place) for place in range(4) for digit in range(16)]:
        put('text_cursor_ptr',0x80000,4);put('four_digit_text_skip_mask',0)
        cpu.d[0]=0xABCD0000|value
        cpu.d[1],cpu.d[2],cpu.d[7],cpu.a[0],cpu.a[1]=0x12345678,0x23456789,0x3456789A,0x456789AB,0x56789ABC
        saved=[cpu.d[i] for i in [0,1,2,7]]+[cpu.a[0],cpu.a[1]]
        write(BUFFER+5,0xA5,1)
        run(FORMAT,budget=4096)
        expected=f'{value:04X}'.lstrip('0').rjust(4).encode()
        assert bytes(memory[BUFFER:BUFFER+5])==expected+b'\0'
        assert read(BUFFER+5,1)==0xA5
        assert [cpu.d[i] for i in [0,1,2,7]]+[cpu.a[0],cpu.a[1]]==saved
        assert get('status_flags')==(0xF7|(8 if value else 0))


def test_all_skip_mask_bytes_emit_control_one_after_the_leading_digit_test(native_deadline):
    cpu,memory,read,write,run,put,get,prepare=native_deadline
    prepare()
    for value in [0,0x12,0x1000,0xF00A]:
        plain=f'{value:04X}'.lstrip('0').rjust(4).encode()
        for mask in range(256):
            put('text_cursor_ptr',0x80000,4);put('four_digit_text_skip_mask',mask)
            cpu.d[0]=value
            run(FORMAT,budget=4096)
            expected=bytes(1 if mask&(8>>i) else c for i,c in enumerate(plain))
            assert bytes(memory[BUFFER:BUFFER+5])==expected+b'\0'
            assert get('four_digit_text_skip_mask')==mask
            assert get('status_flags')==(0xF7|(8 if value else 0))


def test_explicit_post_sbcd_carry_branch_queues_without_storing_the_high_byte(deadline):
    cpu,memory,read,write,run,put,get,prepare=deadline
    for carry in [0,1]:
        prepare(value=0x1234,ui=2)
        cpu.d[0]=0x77;cpu.sr=0x2000|carry
        # Deliberate interior entry after the second SBCD, not evidence that
        # any valid countdown input produces this carry.
        run(0x2D88,budget=4096)
        assert get('earth_orbit_countdown_bcd',2)==(0x1234 if carry else 0x7734)
        assert read(APP+TAIL)==APP+HEAD+8*carry

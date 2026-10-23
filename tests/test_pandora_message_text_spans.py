"""Original message storage and supplied reader contexts, without activation claims."""
from tests.test_pandora_state_transitions import BASE, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_text_renderers import prepare, APP, FONT, DEST
from tests.test_pandora_render_order import sequencer

# Full stored text bounds, including terminators and embedded quote/CR bytes.
TEXT_CASES = [
    (0x9B18,0x9B59,'self_destruct_insert_cards_text'),
    (0x9B59,0x9B62,'self_destruct_card_number_labels'),
    (0x9B62,0x9BB8,'self_destruct_rejected_cards_text'),
    (0x9BB8,0x9C00,'self_destruct_accepted_cards_text'),
    (0x4CB22,0x4CB5D,'pandora_destroyed_earth_uncertain_message'),
    (0x4CB5D,0x4CB92,'escape_without_destroying_pandora_message'),
    (0x4CDC4,0x4CDEA,'robomechanic_breakdown_message'),
    (0x4CDEA,0x4CE00,'robomechanic_adjustments_response'),
    (0x4CE00,0x4CE20,'security_officer_sonicblaster_message'),
    (0x4CE20,0x4CE38,'security_officer_be_careful_response'),
    (0x4CE38,0x4CE5B,'thief_laughter_response'),
    (0x4CF72,0x4CF8E,'diabetic_syringe_request_message'),
    (0x4D040,0x4D063,'death_fly_die_human_message'),
    (0x4D063,0x4D07F,'priest_blessing_message'),
    (0x4D07F,0x4D096,'priest_thou_shalt_not_kill_response'),
    (0x4D0CA,0x4D0DC,'driffid_sunlight_message'),
    (0x4D1D6,0x4D1F9,'doctor_medic_messed_message'),
    (0x4D1F9,0x4D220,'hooligan_challenge_message'),
    (0x4D220,0x4D234,'hooligan_tool_response'),
    (0x4D234,0x4D24B,'bank_manager_money_message'),
]
# Message target, original world object, and the actual shared pointer member.
NPC_LINKS = [
    (0x4CDC4,0x4B39E,0x0C),(0x4CDEA,0x4B39E,0x10),
    (0x4CE00,0x4B82E,0x0C),(0x4CE20,0x4B82E,0x10),
    (0x4CE38,0x49908,0x10),(0x4CF72,0x4B728,0x0C),
    (0x4D040,0x4A5AC,0x0C),(0x4D063,0x49B32,0x0C),
    (0x4D07F,0x49B32,0x10),(0x4D0CA,0x4A694,0x0C),
    (0x4D1D6,0x4B4FE,0x0C),(0x4D1F9,0x4A028,0x0C),
    (0x4D220,0x4A028,0x10),(0x4D234,0x4B900,0x0C),
]


def test_original_message_bounds_keep_quote_bytes_carriage_returns_and_nul(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    assert len(TEXT_CASES)==20 and len(NPC_LINKS)==14
    for lo,hi,name in TEXT_CASES:
        data=bytes(memory[BASE+lo:BASE+hi])
        assert data[-1:]==b'\0' and b'\0'not in data[:-1]
        assert all(32<=b<127 or b in (0,13)for b in data)
        if lo>=0x4CDC4:assert data[0]==data[-2]==0x22
    for lo,hi in [(0x4CB22,0x4CB5D),(0x4CB5D,0x4CB92)]:
        assert b'EARTH\x22S' in memory[BASE+lo:BASE+hi]
    assert [bytes(memory[BASE+lo:BASE+hi]).count(b'\r')for lo,hi,_ in TEXT_CASES[:4]]==[4,2,2,3]


def test_original_object_field_loads_and_message_producers_select_exact_roots(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    for target,obj,field in NPC_LINKS:
        assert read(BASE+obj+field)==BASE+target
        cpu.a[5]=BASE+obj
        entry=0x839E if field==0x0C else 0x2F30
        run(entry,stop=entry+4)
        assert cpu.a[0]==BASE+target
    for entry,target,reg in [(0x9E26,0x9B18,3),(0x9E34,0x9B59,3),
                             (0x9E7A,0x9BB8,3),(0x9EB0,0x9BB8,3),(0x9E98,0x9B62,3),
                             (0x4C9C6,0x4CB22,0),(0x4C9CC,0x4CB5D,0)]:
        run(entry,stop=entry+4)
        assert cpu.a[reg]==BASE+target


def test_original_compact_reader_consumes_each_full_span_and_exact_control_bytes(cpu_fixture,title_slots):
    cpu,memory,read,write,run=prepare(cpu_fixture,title_slots,mask=5)
    for code in range(256):
        memory[FONT+8*code:FONT+8*code+8]=bytes((code+row)&255 for row in range(8))
    for lo,hi,name in TEXT_CASES:
        text=bytes(memory[BASE+lo:BASE+hi])
        memory[DEST-4:DEST+8196]=bytes([0xA5])*8200
        expected=bytearray(memory[DEST-4:DEST+8196])
        origin=live=DEST
        for byte in text[:-1]:
            if byte==13:
                origin+=1280;live=origin
            else:
                glyph=byte-32 if byte>=97 else byte
                for row in range(8):
                    for plane in range(4):expected[4+live-DEST+160*row+40*plane]=(glyph+row)&255 if 5&(1<<plane)else 0
                live+=1
        cpu.a[6],cpu.a[3]=APP,BASE+lo
        write(APP+title_slots['app_text_cursor_ptr'],DEST)
        trace=sequencer(cpu,memory,write)(0x6056,budget=30000)
        assert trace.stop_reason==1 and cpu.a[7]==0x9004,name
        assert memory[DEST-4:DEST+8196]==expected,name
        assert cpu.a[3]==BASE+hi and cpu.a[1]==read(APP+title_slots['app_text_cursor_ptr'])==live,name
        assert memory[BASE+lo:BASE+hi]==text,name

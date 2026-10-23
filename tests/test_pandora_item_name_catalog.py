"""Original catalog bytes through original lookup and text consumers.

RAM/MMIO shadows establish CPU reads, writes and packets, not display or DMA.
Injected offset-table bytes are explicit; they do not establish ordinary mutation.
"""
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from tests.test_pandora_state_transitions import BASE, TARGET, cpu_fixture
from tests.test_pandora_title_data import title_slots
from tests.test_pandora_render_order import sequencer

pytestmark=pytest.mark.parametrize('cpu_fixture',[0x1000000],indirect=True)
CATALOG=json.loads((Path(__file__).parent/'fixtures/pandora_item_name_catalog.json').read_text())
APP,DEST=0x39fc,0x88000


@pytest.fixture
def catalog(cpu_fixture,title_slots):
    cpu,memory,schemas,read,write,run=cpu_fixture
    metadata=effective_target_metadata(resolve_project_paths(TARGET).target_dir)
    names={a.name:BASE+a.addr for a in metadata.seeded_entities if a.name}
    names.update({a.name:BASE+a.addr for a in metadata.seeded_code_labels if a.name})
    names.update({a.name:a.addr for a in metadata.absolute_code_labels if a.name})
    def app(name,value,size=4):write(APP+title_slots['app_'+name],value,size)
    def call(name,budget=12000):
        result=sequencer(cpu,memory,write)(names[name]-BASE,budget=budget)
        assert result.stop_reason==1 and result.steps<budget
    def prepare(address):
        cpu.a[3],cpu.a[6]=address,APP
        app('text_cursor_ptr',DEST);app('text_plane_mask',5,1)
        app('font_glyph_bitmap_table_ptr',names['compact_font_index_origin'])
        app('font_glyph_layout_table_ptr',BASE+0xaafe)
        app('proportional_text_word_cursor_ptr',DEST);app('proportional_text_pixel_shift',8,1)
        write(0xdff01e,0x40,2)
        memory[DEST-8:DEST+1304]=bytes([0xa5])*1312
    return cpu,memory,read,write,names,title_slots,app,call,prepare


def test_original_catalog_has_103_strings_114_slots_and_a_shared_final_terminator(catalog):
    cpu,memory,read,write,names,slots,app,call,prepare=catalog
    strings=CATALOG['strings'];table=BASE+CATALOG['offset_table_start'];base=BASE+CATALOG['pool_base']
    assert len(strings)==103 and sum(len(s['ids']) for s in strings)==114
    assert strings[0]['text']=='' and strings[0]['ids']==[0]
    assert strings[1]['text']=='     NOTHING' and strings[1]['ids']==[1]
    assert {tuple(s['ids']) for s in strings if len(s['ids'])>1}=={(14,15,16,17,18),(20,21,22,23),(85,86,87),(90,91),(92,93)}
    for s in strings:
        start,end=BASE+s['source_offset'],BASE+s['source_end']
        expected=s['text'].encode('ascii')+(b'\0' if s['terminator_offset']<CATALOG['pool_end'] else b'')
        assert memory[start:end]==expected
        assert memory[BASE+s['terminator_offset']]==0
        for item in s['ids']:assert base+read(table+2*item,2)==start
    last=strings[-1]
    assert last['text']=='Amiga Computing' and last['ids']==[113]
    assert last['source_end']==last['terminator_offset']==CATALOG['pool_end']
    assert read(table,2)==1  # Its high byte terminates the preceding name.


def test_all_catalog_names_render_with_the_original_compact_font_and_stop_at_actual_nul(catalog):
    cpu,memory,read,write,names,slots,app,call,prepare=catalog
    for s in CATALOG['strings']:
        start=BASE+s['source_offset'];prepare(start)
        before=bytes(memory[DEST-8:DEST+1304]);expected=bytearray(before)
        for column,code in enumerate(s['text'].encode('ascii')):
            folded=code-32 if code>=97 else code
            glyph=names['compact_font_index_origin']+8*folded
            for row in range(8):
                for plane in range(4):expected[8+column+row*160+plane*40]=read(glyph+row,1) if 5&(1<<plane) else 0
        call('draw_compact_text_string')
        assert cpu.a[3]==BASE+s['terminator_offset']+1
        assert cpu.a[1]==read(APP+slots['app_text_cursor_ptr'])==DEST+len(s['text'])
        assert memory[DEST-8:DEST+1304]==expected
        assert cpu.a[7]==0x9004


def test_all_catalog_names_feed_original_proportional_map_and_cursor_with_no_plane_enabled(catalog):
    cpu,memory,read,write,names,slots,app,call,prepare=catalog
    for s in CATALOG['strings']:
        prepare(BASE+s['source_offset']);app('text_plane_mask',0,1)
        cursor,phase=DEST,8
        for code in s['text'].encode('ascii'):
            index=read(BASE+0xaf3e+code-32,1);assert index<68
            width=read(BASE+0xaafe+16*index,2)&255
            summed=(phase+width)&255;cursor+=2 if summed>=16 else 0;phase=summed&15
        before=bytes(memory[DEST-8:DEST+1304]);write(0xdff058,0x1234,2)
        call('draw_proportional_ui_text_string')
        assert cpu.a[3]==BASE+s['terminator_offset']+1
        assert read(APP+slots['app_proportional_text_word_cursor_ptr'])==cursor
        assert read(APP+slots['app_proportional_text_pixel_shift'],1)==phase
        assert memory[DEST-8:DEST+1304]==before and read(0xdff058,2)==0x1234


def test_final_name_terminator_depends_on_adjacent_offset_word_not_its_15_byte_extent(catalog):
    cpu,memory,read,write,names,slots,app,call,prepare=catalog
    last=CATALOG['strings'][-1];table=BASE+CATALOG['offset_table_start']
    prepare(BASE+last['source_offset']);call('draw_compact_text_string')
    assert cpu.a[3]==table+1
    # Change data, not instructions: ID113's own lookup slot is untouched.
    write(table,0x5859,2)
    prepare(BASE+last['source_offset']);call('draw_compact_text_string')
    assert cpu.a[3]==table+3
    assert read(APP+slots['app_text_cursor_ptr'])==DEST+17
    assert read(table+2,2)==2


def test_inventory_refresh_preserves_shared_display_aliases_and_all_114_name_mappings(catalog):
    cpu,memory,read,write,names,slots,app,call,prepare=catalog
    expected={i:BASE+s['source_offset'] for s in CATALOG['strings'] for i in s['ids']}
    cpu.a[6]=APP
    for first in range(0,114,4):
        carried=[(first+i)%114 for i in range(4)];pockets=[113-item for item in carried]
        for slot,item in enumerate(carried):write(APP+slots['app_carried_item_ids']+slot,item,1)
        for slot,item in enumerate(pockets):write(APP+slots['app_pocket_item_ids']+slot,item,1)
        cpu.d[7]=0x12345678;cpu.a[2],cpu.a[3],cpu.a[4],cpu.a[5]=0x11111111,0x22222222,0x33333333,0x44444444
        before=(cpu.d[7],tuple(cpu.a[2:6]));call('refresh_inventory_panel')
        assert [read(names['backpack_inventory_overlay_line_0_ptr']+4*i) for i in range(4)]==[expected[i] for i in carried]
        assert [read(names['pocket_inventory_overlay_line_0_ptr']+4*i) for i in range(4)]==[expected[i] for i in pockets]
        assert (cpu.d[7],tuple(cpu.a[2:6]))==before
        assert [read(APP+slots['app_carried_item_ids']+i,1) for i in range(4)]==carried
        assert [read(APP+slots['app_pocket_item_ids']+i,1) for i in range(4)]==pockets

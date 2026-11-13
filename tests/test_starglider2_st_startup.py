"""Original ST startup/dispatch witnesses; no chipset or FDC behavior is invented."""
import os
from pathlib import Path
import pytest
from amiga_reversing.disasm.game_catalog import load_family, materialize
from amiga_reversing.disasm.mapped_execution import MappedExecution
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend

ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.skipif(not os.getenv('SGII_LINKED_FIXTURES'),reason='bind private SGII artifacts and set SGII_LINKED_FIXTURES=1')

DISK_ROLES=('select_disk_surface_a','select_disk_surface_b','deselect_disk_backend',
    'advance_disk_backend_cylinder','retreat_disk_backend_cylinder','seek_disk_backend_cylinder_zero',
    'read_disk_backend_blocks','write_disk_backend_track','check_disk_backend_change')
DISPLAY_ROLES=('print_cursor_text','print_positioned_text','draw_message_line_continuation',
    'probe_display_mode','noop','add_bcd_and_draw_digits','draw_coordinate_digit_pairs','draw_heading_indicator','noop','noop')


def image(target='atari_st_starglider2_main'):
    family=load_family(ROOT,'starglider2')
    return materialize(ROOT,'starglider2',family['targets'][target]['artifact']).read_bytes()


def ram_prefix(ram_size=0x100000,register_seed=0xdeadbeef):
    cpu=MappedExecution(ram_size,register_seed=register_seed)
    cpu.seed(0x1000,image())
    for start,size in [(0xe144,2),(0x27be,4),(0x61668,0x6598),(0x337e,8),(8,12),(0x18,404),(0x10612,1)]:
        cpu.allow_write(start,size)
    if ram_size>0x90000:
        cpu.allow_write(0x90000,1)
    stop=0x3cd42 if ram_size>0x90000 else 0x3cd00
    return cpu,cpu.run(0x1000,stop,28000)


def patch_family(cpu,family):
    """Execute a RAM-only suffix, conditional on earlier I/O completing normally."""
    cpu.writable[:]=bytes(len(cpu.writable))
    if family=='disk':
        start,stop,base,roles=0x3cdc0,0x3ce36,0xfdec,DISK_ROLES
        cpu.allow_write(0x61668+0x9c,16)
    elif family=='colour':
        start,stop,base,roles=0x3ce40,0x3ce96,0xc4f0,DISPLAY_ROLES
    elif family=='monochrome':
        start,stop,base,roles=0x3ce98,0x3ceee,0xc4f0,DISPLAY_ROLES
    else:raise ValueError('unknown patch family')
    before=cpu.read(base,len(roles)*6)
    for i in range(len(roles)):cpu.allow_write(base+6*i+2,4)
    run=cpu.run(start,stop,32)
    after=cpu.read(base,len(roles)*6)
    targets=[int.from_bytes(after[6*i+2:6*i+6],'big') for i in range(len(roles))]
    original_targets=[int.from_bytes(before[6*i+2:6*i+6],'big') for i in range(len(roles))]
    # Validate the complete stub encoding with the native source assembler,
    # rather than a Python opcode decoder or an assumed byte-prefix match.
    for value,addresses in [(before,original_targets),(after,targets)]:
        source='section code,code\n'+''.join(f'jmp ${address:x}.l\n' for address in addresses)
        encoded,_=assemble_platform_source_text_with_c_backend('atari-st-raw',source,target_cpu='68000')
        assert value==encoded
    assert all(0x1000<=v<0x675ec and v%2==0 for v in targets)
    return list(zip(roles,targets)),run


@pytest.mark.parametrize('register_seed',[0,0xdeadbeef])
def test_one_megabyte_startup_selects_st_and_installs_vectors_before_hardware(register_seed):
    cpu,run=ram_prefix(register_seed=register_seed)
    assert run['steps']==26250 and cpu.cpu.a[7]==0x337e
    assert cpu.cpu.a[6]==0x61668
    assert cpu.read(0x90000,1)==b'\xaa' and cpu.read(0x10612,1)==b'\0'
    assert {p:int.from_bytes(cpu.read(p,4),'big') for p in [8,12,16,0x70]}=={8:0xc628,12:0xc666,16:0xc6a4,0x70:0x3ca8e}
    for address in range(0x18,0x1ac,4):
        expected=0x3ca8e if address==0x70 else 0x3cf08
        assert cpu.read(address,4)==expected.to_bytes(4,'big')
    with pytest.raises(ValueError,match='native CPU witness failed.*unsupported concrete move'):
        cpu.run(0x3cd42,0x3cd46,1)


def test_half_megabyte_witness_stops_before_the_unmodeled_bus_error_probe():
    cpu,run=ram_prefix(0x80000)
    assert run['stop_pc']==0x3cd00
    assert cpu.read(8,4)==(0x3cf02).to_bytes(4,'big')
    assert cpu.read(12,4)==(0x3cf02).to_bytes(4,'big')
    # Failure is an observer refusal, not emulated bus-error exception delivery.
    with pytest.raises(ValueError,match='native CPU witness failed.*unsupported concrete move'):
        cpu.run(0x3cd00,0x3cd08,1)


@pytest.mark.parametrize('mode',['colour','monochrome'])
def test_runtime_suffix_installs_st_disk_and_display_stubs(mode):
    cpu,_=ram_prefix()
    disk,run=patch_family(cpu,'disk')
    assert len(disk)==9 and run['steps']==20 and run['writes']==13
    assert cpu.read(0x61704,16)==bytes.fromhex('32597635000008f9000023e8000131e0')
    display,run=patch_family(cpu,mode)
    assert len(display)==10 and run['steps']==11 and run['writes']==10
    assert {target for role,target in display if role=='noop'}=={0x3cf00}
    assert dict(display)['probe_display_mode']==0x3cf0a
    assert cpu.read(0xfdec,54)==assemble_platform_source_text_with_c_backend('atari-st-raw',
        'section code,code\n'+''.join(f'jmp ${v:x}.l\n' for _,v in disk),target_cpu='68000')[0]


def test_model_extent_initializer_scans_all_104_original_headers():
    data=image()
    cpu=MappedExecution(0x80000,register_seed=0xdeadbeef);cpu.seed(0x1000,data)
    cpu.cpu.a[6]=0x70000;cpu.cpu.a[7]=0x76000;cpu.seed(0x76000,(0x7f000).to_bytes(4,'big'))
    for start,size in [(0x70174,2),(0x70178,4),(0x70010,4),(0x70008,4),(0x70014,4),(0x5930,208)]:cpu.allow_write(start,size)
    run=cpu.run(0x49f8,0x7f000,20000)
    assert run['steps']==14530
    expected=bytearray()
    for i in range(104):
        header=int.from_bytes(data[0x19234+4*i:0x19238+4*i],'big')-0x1000
        count=int.from_bytes(data[header+4:header+6],'big')
        coords=int.from_bytes(data[header+14:header+18],'big')-0x1000
        assert count>0 and 0<=coords<coords+count*2<=len(data)
        words=[int.from_bytes(data[coords+2*j:coords+2*j+2],'big',signed=True) for j in range(count)]
        expected.extend(max([-32768]+words).to_bytes(2,'big',signed=True))
    assert cpu.read(0x5930,208)==expected


def test_ground_grid_initializer_builds_25_quad_offset_records():
    from amiga_reversing.disasm.game_catalog import verify_correspondence
    link=verify_correspondence(ROOT,'starglider2','shared_ground_grid_initialization')
    expected=b''.join((row*48+column*8+corner).to_bytes(2,'big')
        for row in range(5) for column in range(5) for corner in (0,8,56,48))
    for side in ('left','right'):
        span=link[side];data=image(span['target'])
        # The PC-relative LEA has the same encoded displacement in both copies.
        table=0x1000+span['offset']+0x84
        cpu=MappedExecution(0x80000);cpu.seed(0x1000,data)
        cpu.cpu.a[7]=0x76000;cpu.seed(0x76000,(0x7f000).to_bytes(4,'big'));cpu.allow_write(table,200)
        cpu.run(0x1000+span['offset'],0x7f000,256)
        assert cpu.read(table,200)==expected


@pytest.mark.parametrize('seed_word',[0,0x1357,0xffff,0x80ff])
@pytest.mark.parametrize('extend',[0,1])
def test_shared_prng_initializer_retains_its_incoming_extend_dependency(seed_word,extend):
    from amiga_reversing.disasm.game_catalog import verify_correspondence
    link=verify_correspondence(ROOT,'starglider2','shared_prng_initialization')
    results=[]
    high,low=seed_word>>8,seed_word&0xff
    first=(high+low+extend)&0xff
    shifted=(first<<1)&0xff
    second=(shifted+low+(first>>7))&0xff
    expected=bytes([high,first,low,shifted,second,second>>1])
    for side in ('left','right'):
        span=link[side];cpu=MappedExecution(0x80000,register_seed=0xdeadbeef)
        cpu.seed(0x1000,image(span['target']));cpu.cpu.a[6]=0x70000;cpu.cpu.a[7]=0x76000
        cpu.cpu.sr=0x2700|(extend<<4)
        cpu.seed(0x701b0,seed_word.to_bytes(2,'big'));cpu.seed(0x70034,b'\xa5'*12)
        cpu.seed(0x76000,(0x7f000).to_bytes(4,'big'))
        for start,size in [(0x70034,6),(0x7003c,4),(0x70060,8)]:cpu.allow_write(start,size)
        cpu.run(0x1000+span['offset'],0x7f000,32)
        assert cpu.read(0x70034,6)==expected
        assert cpu.read(0x7003a,2)==b'\xa5\xa5'
        assert cpu.read(0x7003c,4)==bytes.fromhex('00314159')
        assert cpu.read(0x70060,8)==bytes.fromhex('9590114328731549')
        results.append(cpu.read(0x70034,12))
    assert results[0]==results[1]


def test_committed_code_entries_cover_the_observed_runtime_dispatch_destinations():
    from amiga_reversing.disasm.effective_metadata import effective_target_metadata
    metadata=effective_target_metadata(ROOT/'targets/atari_st_starglider2_main')
    declared={(entry.addr+0x1000,entry.name) for entry in metadata.seeded_code_entrypoints}
    for mode in ['colour','monochrome']:
        cpu,_=ram_prefix()
        disk,_=patch_family(cpu,'disk');display,_=patch_family(cpu,mode)
        for role,address in disk:assert (address,'st_'+role) in declared
        for role,address in display:
            name='st_noop' if role=='noop' else 'st_probe_display_mode' if role=='probe_display_mode' else 'st_'+mode+'_'+role
            assert (address,name) in declared

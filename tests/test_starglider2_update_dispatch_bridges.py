"""Original two-level object dispatch: tail transfers and diagnostic side effects.

Stop before the destination handler. No object lifetime, hardware delivery or
complete update-loop claim follows from these supplied CPU entries.
"""
import struct
import subprocess
from pathlib import Path
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run

CASES=[
    (0x83FA, 'update_nearby_asteroid', None),
    (0x83FE, 'update_nearby_skim_missile', 192),
    (0x840A, 'update_distant_skim_missile', 193),
    (0x8416, 'update_nearby_skim_launcher_drone', 194),
    (0x8422, 'finish_distant_skim_launcher_drone_update', 195),
    (0x8484, 'update_nearby_mini_sentinel', 196),
    (0x8490, 'advance_distant_mini_sentinel_orbit_angle', 197),
    (0x849C, 'update_nearby_volcano', 198),
    (0x84A8, 'update_nearby_falling_type47', 199),
    (0x84B4, 'retire_distant_type47', 200),
    (0x84C0, 'update_nearby_tractor_beam_marker', None),
    (0x84C4, 'remove_distant_tractor_beam_marker', None),
    (0x84C8, 'update_nearby_planetary_bodies', 201),
    (0x84D4, 'update_nearby_apogee_moons', 202),
    (0x84E0, 'update_nearby_millway_moons', 203),
    (0x84EC, 'update_nearby_q_beta', 204),
    (0x84F8, 'update_distant_planetary_bodies', 205),
    (0x8504, 'update_distant_apogee_moons', 206),
    (0x8510, 'update_distant_millway_moons', 207),
    (0x851C, 'update_distant_q_beta', 208),
    (0x8528, 'update_nearby_solice_display', 209),
    (0x8534, 'finish_distant_solice_update', 210),
    (0x8540, 'update_nearby_projector_base', 211),
    (0x854C, 'update_nearby_projector_mount', 212),
    (0x8558, 'update_nearby_projector_cover', 213),
    (0x8564, 'update_nearby_projector_turret', 214),
    (0x8570, 'update_nearby_projector_fuel_crystals', 215),
    (0x857C, 'update_nearby_projector_control_tower', 216),
    (0x8588, 'update_nearby_projector_crew_quarters', 217),
    (0x8594, 'update_nearby_projector_sentinel', 218),
    (0x85B8, 'update_nearby_space_station', 221),
    (0x85C4, 'update_distant_space_station', 222),
    (0x85D0, 'update_nearby_energy_spheroid', 223),
    (0x85E8, 'update_nearby_bouncing_bomb', 225),
    (0x85F4, 'update_distant_bouncing_bomb', 226),
    (0x8600, 'update_nearby_neutron_bomb', 227),
    (0x860C, 'update_distant_neutron_bomb', 228),
    (0x8618, 'update_nearby_pirate_ship', 229),
]

# Accepted original post-RNG mask/read entries; stop before the object store.
READERS=[
    (0xA036,0xA03E,'airborne_spawn_model_type_choices',0,8),
    (0xA924,0xA92C,'airborne_spawn_model_type_choices',0,8),
    (0xA300,0xA30A,'ground_spawn_model_type_choices',3,4),
    (0xAA6C,0xAA76,'ground_spawn_model_type_choices',3,4),
    (0x8734,0x873E,'fragment_model_type_tags',3,4),
]


@pytest.fixture(scope='module')
def labels(tmp_path_factory,original_image):
    target=Path(__file__).resolve().parents[1]/'targets/amiga_raw_starglider2_game'
    names=sorted({name for _,name,_ in CASES}|{name for _,_,name,_,_ in READERS})+['diagnostic_step_byte']
    temp=tmp_path_factory.mktemp('update-dispatch');asm,out=temp/'labels.s',temp/'labels.raw'
    asm.write_text((target/'starglider2_game.s').read_text()+'\n dc.l '+','.join(names)+'\n')
    result=subprocess.run([str(target.parents[1]/'tools/vasmm68k_mot.exe'),'-quiet','-Fbin','-m68000','-no-opt',
        '-I'+str(target/'includes'),'-o',str(out),str(asm)],cwd=target,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    raw=out.read_bytes();size=4*len(names)
    assert raw[:-size]==original_image[0]
    return dict(zip(names,struct.unpack('>'+'I'*len(names),raw[-size:])))


@pytest.mark.parametrize('entry,destination,diagnostic',CASES)
def test_original_dispatch_preserves_frame_and_reaches_named_body(original_image,memory,labels,entry,destination,diagnostic):
    cpu=state(memory,entry);before_d,before_a=list(cpu.d),list(cpu.a);before_sr=cpu.sr
    expected=bytearray(memory)
    if diagnostic is not None:expected[labels['diagnostic_step_byte']]=diagnostic
    run(original_image,memory,cpu,{labels[destination]},limit=4)
    assert bytes(memory)==expected
    assert list(cpu.d)==before_d and list(cpu.a)==before_a
    assert cpu.sr==((before_sr&~15)|8 if diagnostic is not None else before_sr)


@pytest.mark.parametrize('entry,stop,table,dest,count,index',[
    (*reader,index)for reader in READERS for index in range(reader[4])])
def test_masked_spawn_reader_uses_each_original_stored_id(original_image,memory,labels,entry,stop,table,dest,count,index):
    cpu=state(memory,entry);cpu.a[1]=labels[table]
    cpu.d[0]=0xBEEF0000|((0x10000-count)|index);cpu.d[3]=0xCAFE7654
    expected=memory[labels[table]+index];before=bytes(memory)
    run(original_image,memory,cpu,{stop},limit=4)
    assert bytes(memory)==before and cpu.a[1]==labels[table]
    assert cpu.d[dest]==((0xBEEF0000 if dest==0 else 0xCAFE0000)|expected)
    if dest:assert cpu.d[0]==0xBEEF0000|index

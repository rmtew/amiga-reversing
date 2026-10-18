"""Regression checks against original, canonical Copperline captures.

These receipts prove a blocked ordinary shot and live table/state membership;
they deliberately do not promote that evidence to a successful NPC hit.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=json.loads((ROOT/'runtime/observations/pandora-rifle-descriptor-admission.json').read_text())
DATA=(ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()

assert hashlib.sha256(DATA).hexdigest()==REPORT['original_sha256']


def word(offset):return int.from_bytes(DATA[offset:offset+2],'big')


def captures(phase):return {int(r['address'],16):bytes.fromhex(r['bytes']) for r in phase['capture']['memory_reads']}


def test_live_table_has_original_prefix_middle_members_tail_and_null():
    observation=REPORT['descriptor_audit'];phase=observation['phases'][0]
    assert observation['checkpoint']['status']=='restored'
    assert observation['direct_payload_handoff']['status']=='verified'
    assert phase['payload']['payload_sha256']==REPORT['original_sha256']
    reads=captures(phase)
    raw=b''.join(reads[0x1309a+64*i] for i in range(5))
    pointers=[int.from_bytes(raw[i:i+4],'big') for i in range(0,len(raw),4)]
    original=[int.from_bytes(DATA[0x309a+4*i:0x309e+4*i],'big') for i in range(68)]
    assert pointers[:29]==original[:29] and pointers[61:]==original[61:]
    assert Counter(pointers[29:61])==Counter(original[29:61])
    assert len(set(pointers[:-1]))==67 and pointers[-1]==0
    assert reads[0x3ca4][:6]==bytes.fromhex('0001309a0043')
    assert pointers[REPORT['table']['flight_descriptor_index']]==0x5bfba
    assert pointers[REPORT['table']['feed_descriptor_index']]==0x5c2be


def test_skipped_flight_root_has_eligible_attachment_and_feed_has_cached_geometry():
    reads=captures(REPORT['descriptor_audit']['phases'][0])
    root,child=reads[0x5bfc6][:26],reads[0x5bfc6][26:52]
    assert root[25]==0x88 and int.from_bytes(root[20:24],'big')==0x5bfe0
    assert child[25]==0 and int.from_bytes(child[:4],'big')==0x5bcca
    assert child[20:24]==bytes(4)
    feed=reads[0x5c2ca]
    assert feed[24]==1 and feed[25]==0 and int.from_bytes(feed[:4],'big')==0x5c264
    assert reads[0x3d18]==bytes.fromhex('00070000')
    for source,expected in [(0x4bcca,[0,0,31,27]),(0x4c264,[7,0,25,27])]:
        assert [word(source+i) for i in [14,16,12,10]]==expected


def test_simultaneous_left_fire_uses_retained_aim_and_consumes_mutable_ammo_only():
    phases=REPORT['normal_input_shot']['phases']
    assert [p['payload']['payload_offset'] for p in phases]==['0x5ca','0x92e2','0x9410','0x5ca']
    assert all(p['status']=='hit' and p['payload']['status']=='pc_matched' for p in phases)
    first=phases[1]['capture']['registers'];wall=phases[2]['capture']['registers']
    assert tuple(int(first[k],16)&65535 for k in ['d0','d1','d2','d3'])==(1270,888,14,0)
    assert tuple(int(wall[k],16)&65535 for k in ['d5','d6'])==(1270,888)
    for i,phase in enumerate(phases):
        reads=captures(phase)
        assert reads[0x1924c]==bytes.fromhex('05010501' if i==0 else '05010401')
        assert reads[0x5c352]==bytes.fromhex('04cc036a')
        assert reads[0x5c35e]==bytes.fromhex('005f') and reads[0x5bc46]==bytes.fromhex('0037')
    # Independently decode the original macrocell and MSB-first movement bit.
    row,col=888//16,1270//16
    selector=word(0x3502+2*((row//3)*30+col//3))
    tile=word(0x3f16+2*(9*selector+3*(row%3)+col%3))//128
    assert tile==306 and DATA[0xa822+tile//8]&(128>>(tile%8))
    audit=json.loads((ROOT/'runtime/scenarios/pandora-rifle-checkpoint-audit.json').read_text())
    for phase in audit['phases'][1:]:
        reads=phase['capture']['memory_reads']
        assert any(r.get('address')==0x1924e and r['expect_hex']=='0501' for r in reads)
        assert any(r.get('offset')==796 and r['expect_hex']=='00070000' for r in reads)


def test_separately_accepted_left_aim_crosses_one_clear_tile_before_wall():
    phases=REPORT['separated_left_aim']['phases']
    assert all(p['status']=='hit' and p['payload']['status']=='pc_matched' for p in phases)
    assert [p['payload']['payload_offset'] for p in phases]==['0x5ca']*3+['0x92e2','0x9410','0x5ca']
    ready=captures(phases[2])
    assert ready[0x5c352]==bytes.fromhex('04b7036a')
    assert ready[0x3d18]==bytes.fromhex('fff90000') and ready[0x3bc2]==bytes(4)
    first,wall=phases[3]['capture']['registers'],phases[4]['capture']['registers']
    assert tuple(int(first[k],16)&65535 for k in ['d0','d1','d2','d3'])==(1193,888,65522,0)
    assert tuple(int(wall[k],16)&65535 for k in ['d5','d6'])==(1179,888)
    for x,expected,blocked in [(1193,92,False),(1179,64,True)]:
        row,col=888//16,x//16
        selector=word(0x3502+2*((row//3)*30+col//3))
        tile=word(0x3f16+2*(9*selector+3*(row%3)+col%3))//128
        assert tile==expected and bool(DATA[0xa822+tile//8]&(128>>(tile%8)))==blocked
    for i,p in enumerate(phases):
        reads=captures(p)
        assert reads[0x1924c]==bytes.fromhex('05010501' if i<3 else '05010401')
        assert reads[0x5c35e]==bytes.fromhex('005f') and reads[0x5bc46]==bytes.fromhex('0037')
    assert captures(phases[-1])[0x5c352]==ready[0x5c352]

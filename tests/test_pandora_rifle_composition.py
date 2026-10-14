"""Regression checks against the normal-input rifle and patrol receipts."""
from dataclasses import replace
import json
from pathlib import Path

from amiga_reversing.tools.pandora_patrol_timing import PatrolState, tick, assess_crossing

ROOT=Path(__file__).resolve().parents[1]
MODEL=json.loads((ROOT/'runtime/observations/pandora-world-model.json').read_text())
REPORT=json.loads((ROOT/'runtime/observations/pandora-rifle-composition.json').read_text())
DATA=(ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()


def state(raw):
    return PatrolState(raw['pc'],tuple(raw['xy']),raw['delay'],{int(k):v for k,v in raw['counters'].items()},raw['flags'])


def advance(s):
    return tick(DATA,s,0x10000,MODEL['opcode_values'],script_start=REPORT['flight_timing']['script_start'])


def test_all_flight_crossing_snapshots_fit_the_admitted_call_windows():
    rows=REPORT['flight_timing']['states'];previous=state(rows[0]['actor'])
    assert previous.xy==(1104,868) and len(rows)==29
    for row in rows[1:]:
        actual=state(row['actor']);calls=row['eligible_calls_since_previous']
        assert 1<=calls<=6
        for _ in range(calls):previous=advance(previous)
        assert previous.flags&0x42==actual.flags&0x42
        assert replace(previous,flags=actual.flags)==actual
        previous=actual
    assert REPORT['flight_timing']['proof']['status']=='conditional_clearance'


def test_normal_empty_slot_swap_and_rifle_pickup_preserve_health_ammo_and_provenance():
    captures={p['name']:p for p in REPORT['normal_inventory_and_pickup_captures']}
    selected=lambda name:int(captures[name]['capture']['memory_reads'][2]['bytes'],16)
    assert selected('rifle_inventory_opened')==54
    assert selected('empty_slot_selected')==selected('rifle_pickup_ready')==0
    assert selected('rifle_item_written')==selected('rifle_equipped_loop')==18
    final=REPORT['final_player']
    assert final['xy']==[1228,874] and final['inventory_bytes']=='3600000000000000'
    assert final['hit_points']==95 and final['fire_pressed']==0 and final['ammunition']=='0501'
    assert final['receptacle_data']=='00058a481201'
    assert final['volume']=='0040' and final['shared_audio_flags']=='00'
    chain=REPORT['checkpoint_chain']
    for previous,current in zip(chain,chain[1:]):
        assert current['parent_snapshot_sha256']==previous['snapshot_sha256']
        assert current['binding']==previous['binding']
    assert [s['canonical_phases_hit'] for s in REPORT['segments']]==[61,32,30,38,5,2]
    assert all(p['expectations_matched'] for segment in REPORT['segments'] for p in segment['phases'])


def test_coarse_reverse_corridor_model_refuses_all_cycle_gates_instead_of_guessing():
    reverse=REPORT['reverse_flight_gate_assessment'];s=PatrolState(REPORT['flight_timing']['script_start'],(0,0),0)
    assert len(reverse['path'])==45 and reverse['admitted_gates']==[]
    for _ in range(377):
        s=advance(s)
        assert assess_crossing(DATA,s,0x10000,MODEL['opcode_values'],reverse['path'],
                               script_start=REPORT['flight_timing']['script_start'],max_calls_per_move=6)['status']=='unsafe'


def test_rifle_checkpoint_idle_audit_keeps_inputs_and_position_neutral():
    rows={p['name']:p for p in REPORT['normal_inventory_and_pickup_captures']}
    for name in ('rifle_checkpoint_anchor','rifle_checkpoint_idle_loop'):
        reads=rows[name]['capture']['memory_reads']
        assert reads[0]['bytes']=='04cc036a' and reads[2]['bytes']=='12'
        assert reads[4]['bytes']=='00' and reads[-1]['bytes']=='00000000'
        assert all(r.get('expectation',{}).get('matched',True) for r in reads)


def test_eastward_aim_candidate_uses_live_geometry_and_correct_grid_base():
    aim=REPORT['aim_candidate'];body=aim['captured_feed']
    assert body['geometry_bounds_half_open']==[847,168,872,195]
    assert body['object_xy']==body['descriptor_xy']==[840,168] and body['hit_points']==29
    p=body['geometry_pointer']-0x10000
    assert [int.from_bytes(DATA[p+i:p+i+2],'big') for i in (12,10,14,16)]==[25,27,7,0]
    x,y,_=aim['player_candidate'];dx,dy=aim['accepted_request']
    assert aim['first_ray_point']==[x+14+4*dx,y+14+4*dy]==[850,168]
    assert aim['captured_tile_grid_base']==0x4000
    cell=next(c for c in aim['captured_cells'] if c['tile_xy']==[53,10])
    assert cell['tile_id']==450 and cell['matches_original']
    bits=DATA[MODEL['source_bindings']['tile_movement_block_bits']:][:64]
    assert not bits[450//8] & (128>>(450%8))
    assert aim['observation']['phase']['status']=='hit'
    assert aim['guard_counterexample']['status']=='capture_expectation_mismatch'

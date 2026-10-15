"""Counterexample-driven checks for the bounded Pandora planning model."""
from pathlib import Path
import json

import pytest

from amiga_reversing.tools.pandora_world_model import (
    Terrain, encounter_outcome, keepout, move, movement_gate, plan, script_envelope,
)

ROOT = Path(__file__).resolve().parents[1]


def report():
    return json.loads((ROOT/'runtime/observations/pandora-world-model.json').read_text())


def test_recorded_pianist_encounter_and_following_ui_gate():
    observed = report()
    event = observed['validated_encounter']
    assert event['player_xy'] == [808, 794]
    assert event['actor']['xy'] == [816, 808]
    assert encounter_outcome(event['player_xy'], event['actor']) == 'combat'
    transition = observed['validated_transition']
    assert transition['predicted_combat_xy'] == transition['observed_player_xy'] == [10808, 794]
    assert movement_gate(transition['ui_flags']) == 'combat_or_inventory_blocks_movement'


@pytest.mark.parametrize('xy,outcome', [
    ([792, 808], 'out_of_range'),  # X difference24 is excluded by the game.
    ([793, 808], 'combat'),
    ([816, 792], 'out_of_range'),  # Y difference16 is excluded.
    ([816, 793], 'combat'),
])
def test_encounter_strict_boundary_from_native_range_check(xy, outcome):
    actor = dict(report()['validated_encounter']['actor'])
    assert encounter_outcome(xy, actor) == outcome


def test_unresolved_trade_state_is_not_silently_safe():
    actor = dict(report()['validated_encounter']['actor'], selected_item_id=0)
    assert encounter_outcome([808, 794], actor) == 'trade_predicate_unresolved'
    actor['flags'] |= 2
    assert encounter_outcome([808, 794], actor) == 'no_automatic_combat'


def test_original_patrol_counter_is_tested_before_decrement():
    """Actual source: (24+1)+(72+1)+(24+1) steps of2 =>246px, not240."""
    model = report()
    actor = next(a for a in model['actors'] if a['name'] == 'world_object_pianist')
    payload = (ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()
    result = script_envelope(payload, actor['initial_script'], 0x10000, model['opcode_values'])
    assert result['status'] == 'bounded_cycle'
    assert result['x_range'] == [816, 816]
    assert result['y_range'] == [728, 974]
    assert set(result['movement_executions'].values()) == {25, 73}
    assert 0x1f56 in result['admitted_source_offsets']  # Actual captured live script PC.


def test_unknown_script_is_not_promoted_to_a_patrol_bound():
    result = script_envelope(b'\xff\xff'+bytes(20), 0, 0x10000, {'WORLD_CMD_SET_POSITION': 23})
    assert result['status'] == 'unknown'
    assert 'x_range' not in result


def test_script_budget_refuses_incomplete_envelope():
    model = report()
    actor = next(a for a in model['actors'] if a['name'] == 'world_object_pianist')
    payload = (ROOT/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/binary.bin').read_bytes()
    assert script_envelope(payload, actor['initial_script'], 0x10000, model['opcode_values'], max_steps=2)['status'] == 'unknown'


def test_lateral_drift_matches_previous_verified_route_transition():
    state, dx, dy = move((507, 650, 'right'), 'down')
    assert state == (500, 650, 'down')
    assert (dx, dy) == (0, 4)  # The request remains vertical; commit applies drift.
    assert move(state, 'up')[0] == (500, 646, 'up')


def test_planner_will_not_walk_through_an_encounter_to_reach_goal():
    terrain = Terrain([[0]*6 for _ in range(6)], b'\0', [(1, 1, 0, 0)])
    route = plan(terrain, (7, 32, 'right'), lambda x, y: x == 35,
                 lambda x, y: abs(x-35)/7, [(30, 40, 0, 95)], max_states=10000)
    assert route['status'] == 'unknown_no_route_within_model_budget'
    assert route['event_edges_rejected'] > 0


def test_staging_plan_stops_before_the_patrol_and_exposes_short_checks():
    model = report()
    stage = model['pianist_staging_route']
    assert stage['status'] == 'conditional_candidate'
    assert stage['goal'] == [780, 794]
    assert stage['accepted_moves'] == 95
    assert [(r['direction'], r['moves']) for r in stage['runs']] == [('up', 18), ('right', 77)]
    a, b, c, d = model['validated_encounter']['patrol_keepout_inclusive']
    assert not a <= stage['goal'][0] <= b
    assert stage['checkpoints'][-1]['after_moves'] == 95
    assert all(right['after_moves']-left['after_moves'] <= 8 for left, right in zip(stage['checkpoints'], stage['checkpoints'][1:]))
    assert model['rifle_staging_route']['status'] == 'unknown_no_route_within_model_budget'


def test_derived_event_dependencies_keep_BYTE_claim_unobserved():
    prerequisites = report()['scenario_prerequisites']
    assert prerequisites['rifle_pickup']['xy'] == [1244, 867]
    assert prerequisites['rifle_pickup']['item_id'] == 18
    assert prerequisites['direct_weapon_kill']['feed_initial_hp'] == 29
    assert prerequisites['direct_weapon_kill']['initial_ammunition'] == [5, 1]
    assert prerequisites['BYTE_write']['state'] == 'not dynamically observed'


@pytest.mark.parametrize('damage', ['missing_phase', 'ambiguous_pc', 'wrong_payload', 'wrong_copy'])
def test_unverified_checkpoint_never_queries_world_facts(monkeypatch, tmp_path, damage):
    from amiga_reversing.tools import pandora_world_model as model
    checkpoint = json.loads((ROOT/'runtime/observations/pandora-world-model-checkpoint.json').read_text())
    observation = checkpoint['observation']
    phase = next(p for p in observation['scenario']['phases'] if p['name'] == 'model_observe_encounter_entry')
    if damage == 'missing_phase':
        observation['scenario']['phases'].remove(phase)
    elif damage == 'ambiguous_pc':
        phase['payload']['status'] = 'ambiguous'
    elif damage == 'wrong_payload':
        phase['payload']['payload_sha256'] = '0'*64
    else:
        observation['reverse_boundary']['materialization']['copied_sha256'] = '0'*64
    path = tmp_path/'checkpoint.json'
    path.write_text(json.dumps(checkpoint))
    def no_world_query(*args, **kwargs):
        raise AssertionError('Invalid execution evidence must not seed a world model')
    monkeypatch.setattr(model, 'RestorationClient', no_world_query)
    with pytest.raises(ValueError):
        model.build('amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8', path)


def test_actor_binding_uses_source_identity_across_corrected_names():
    from amiga_reversing.tools.pandora_world_model import actor_at_source
    for name in ['world_object_megabio_feed', 'world_object_pianist_actor']:
        actor = {'name': name, 'source_offset': 0x4C1D2}
        assert actor_at_source([actor], 0x4C1D2) is actor
    with pytest.raises(ValueError, match='missing or ambiguous'):
        actor_at_source([], 0x4C1D2)
    with pytest.raises(ValueError, match='missing or ambiguous'):
        actor_at_source([actor, dict(actor)], 0x4C1D2)

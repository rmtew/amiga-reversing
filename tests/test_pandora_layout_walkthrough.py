"""Normal-export consumption refuses stale/missing identities before execution."""
import copy
import hashlib
import json

import pytest

from amiga_reversing.tools.pandora_layout_walkthrough import TARGET, export_context, seed_copies, loader_family_context


def fixture():
    original = bytes.fromhex('4e75')
    plan = dict(layout_id='original', status='placement_valid', export_ready=False, chip_bytes=0x100000,
        bootstrap=dict(kind='retained_prefix_copy', variant='native', load_address=0x20000,input_sha256=hashlib.sha256(original).hexdigest(),
                       file_size=2, copied_source_end=2, image_region_id='image'),
        regions=[dict(region_id='image', region_kind='image', size=2, runtime_address=0x10000,
                      original_address=0x10000)])
    payload = dict(status='ok', layout_status='source_only_unqualified', target=TARGET, metadata_hash='current',
        target_identity_sha256=hashlib.sha256(original).hexdigest(),layout_id='original',layout_plan=plan,
        layout_runtime_qualified=False,non_verification=True)
    bind(payload)
    return payload, original


def bind(payload):
    payload['layout_plan_sha256'] = hashlib.sha256(json.dumps(payload['layout_plan'],
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def test_consumes_native_plan_without_claiming_runtime_qualification():
    payload, original = fixture()
    plan, boot, image = export_context(payload, original, 'current')
    assert plan is payload['layout_plan']
    assert plan['export_ready'] is False and image['runtime_address'] == 0x10000
    assert boot['copied_source_end'] == len(original)


@pytest.mark.parametrize('field,value,reason', [
    ('metadata_hash','old','stale or different'),
    ('target_identity_sha256','0'*64,'input identity'),
    ('layout_id','other','another layout'),
    ('layout_plan_sha256','0'*64,'plan identity'),
    ('layout_status','qualified','unqualified'),
    ('layout_plan',None,'plan is missing'),
    ('layout_runtime_qualified',True,'unqualified'),
    ('non_verification',False,'unqualified'),
])
def test_export_identity_refusals(field, value, reason):
    payload, original = fixture()
    payload[field] = value
    with pytest.raises(ValueError, match=reason):
        export_context(payload, original, 'current')


@pytest.mark.parametrize('field,value,reason', [
    ('chip_bytes',0x80000,'diagnostic profile'),
    ('status','refused','placement is refused'),
    ('bootstrap',None,'initialization contract'),
])
def test_unsupported_native_result_is_not_a_pass(field, value, reason):
    payload, original = fixture()
    payload['layout_plan'][field] = value
    bind(payload)
    with pytest.raises(ValueError, match=reason):
        export_context(payload, original, 'current')


def test_file_and_prefix_extent_are_distinct():
    payload, original = fixture()
    changed = copy.deepcopy(payload)
    changed['layout_plan']['bootstrap']['file_size'] = 3
    bind(changed)
    with pytest.raises(ValueError, match='complete staging size'):
        export_context(changed, original, 'current')


def test_native_seed_consumer_refuses_rewritten_or_unknown_source_bytes():
    payload,original=fixture();plan=payload['layout_plan']
    plan['regions'].append(dict(loader_seed=dict(source_offset=0,size=2,runtime_address=0xe0088,
                                               phase='before_payload_entry')))
    assert seed_copies(plan,original,original)==((0,0xe0088,2),)
    with pytest.raises(ValueError,match='rewritten'):
        seed_copies(plan,original,bytes(2))
    plan['regions'][-1]['loader_seed']['source_offset']=2
    with pytest.raises(ValueError,match='outside original'):
        seed_copies(plan,original,original)


def test_family_controls_execute_identical_guest_seed_program_not_only_reservations():
    original,data=fixture()
    seed=dict(source_offset=0,size=2,runtime_address=0x20000,phase='before_payload_entry')
    original['layout_plan']['regions'].append(dict(loader_seed=seed))
    bind(original)
    moved=copy.deepcopy(original)
    moved['layout_id']=moved['layout_plan']['layout_id']='moved'
    moved['layout_plan']['regions'][-1]['loader_seed']['runtime_address']=0xe0088
    bind(moved)
    selected_a,program_a,reservations_a,ids_a=loader_family_context(original,data,data,[moved,original])
    selected_b,program_b,reservations_b,ids_b=loader_family_context(moved,data,data,[original,moved])
    assert selected_a!=selected_b
    assert program_a==program_b==((0,0x20000,2),(0,0xe0088,2))
    assert reservations_a==reservations_b and ids_a==ids_b
    with pytest.raises(ValueError,match='rewritten'):
        loader_family_context(original,data,bytes(2),[moved])
    moved['metadata_hash']='stale'
    with pytest.raises(ValueError,match='stale'):
        loader_family_context(original,data,data,[moved])


def test_runtime_observer_consumes_native_context_and_refuses_legacy_or_stale_bounds():
    from amiga_reversing.tools.pandora_layout_runtime import runtime_context
    payload,_=fixture()
    config=dict(normal_layout_export=True,layout_plan=payload['layout_plan'],
        layout_plan_sha256=payload['layout_plan_sha256'],assembly_base=0x10000,
        load_address=0x20000,entrypoint=0x20000,copied_prefix_bytes=2,old_materialized_interval=[0x10000,0x10002])
    image,bootstrap=runtime_context(config)
    assert image['runtime_address']==0x10000 and bootstrap['load_address']==0x20000
    for field,value in [('normal_layout_export',False),('layout_plan_sha256','old'),('assembly_base',0x80000),('copied_prefix_bytes',3)]:
        with pytest.raises(ValueError):runtime_context(config|{field:value})

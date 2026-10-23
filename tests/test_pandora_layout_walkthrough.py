"""Normal-export consumption refuses stale/missing identities before execution."""
import copy
import hashlib
import json

import pytest

from amiga_reversing.tools.pandora_layout_walkthrough import TARGET, export_context


def fixture():
    original = bytes.fromhex('4e75')
    plan = dict(layout_id='original', status='placement_valid', export_ready=False, chip_bytes=0x100000,
        bootstrap=dict(kind='retained_prefix_copy', variant='native', input_sha256=hashlib.sha256(original).hexdigest(),
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

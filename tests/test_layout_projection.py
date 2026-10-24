"""Native frozen-plan projection equals clean export or refuses explicitly."""
import copy
import json

import pytest

from tests.test_bootstrap_layouts import build,metadata
from tests.test_memory_layouts import region


def model():
    m=metadata()
    m['memory_regions'] += [region('workspace',0x4000,8),region('display',0x70000,16,kind='display')]
    m['target_equates']=[dict(name='SAME_NUMBER_SCALAR',value=0x4000,value_representation='hex',group='fixture')]
    return m


def overlay(m,**changes):
    return dict(memory_layouts=copy.deepcopy(m['memory_layouts']),selected_memory_layout_id='diagnostic') | changes


def source(artifact):return artifact.inline_source_text_with_profile()[0]


@pytest.mark.parametrize('resource',['workspace','display'])
@pytest.mark.parametrize('address',[0x6000,0x60000,0xe0000])
def test_runtime_only_move_equals_clean_plan_and_does_not_mutate_owner(tmp_path,address,resource):
    m=model();base=build(tmp_path,m)
    try:
        before=source(base)
        changed=copy.deepcopy(m)
        changed['memory_layouts'][0]['placements'] += [dict(region_id=resource,runtime_address=address)]
        result=base.layout_projection_payload(overlay(changed))
        assert result['status']=='ok',result
        fresh=build(tmp_path,changed)
        try:
            assert result['canonical_source_text']==source(fresh)
            assert result['package']==fresh.source_package_payload()
            assert result['memory_layouts']==fresh.memory_layouts_payload()
        finally:fresh.close()
        assert result['projection']['semantic_analysis_runs']==0
        assert result['projection']['rewritten_roots']==1
        assert source(base)==before
        assert base.layout_projection_payload(overlay(m))['projection']['rewritten_roots']==0
    finally:base.close()


@pytest.mark.parametrize('change', ['image','bootstrap','chip'])
def test_executable_assumption_change_requires_new_plan(tmp_path,change):
    m=model();base=build(tmp_path,m)
    try:
        o=overlay(m);config=o['memory_layouts'][0]
        if change=='image':config['placements'][0]['runtime_address']=0x90000
        elif change=='bootstrap':config['bootstrap_variant']='native'
        else:config['chip_bytes']=0x80000
        r=base.layout_projection_payload(o)
        # Chip bounds may already refuse image placement. Neither status exports.
        assert r['status'] in ('rebuild_required','refused') and 'package' not in r
    finally:base.close()


@pytest.mark.parametrize('value',[{},dict(memory_layouts=[1],selected_memory_layout_id='diagnostic'),
    dict(memory_layouts=[dict(schema_version=1.5)],selected_memory_layout_id='diagnostic'),
    dict(memory_regions=[],memory_layouts=[],selected_memory_layout_id='diagnostic')])
def test_overlay_does_not_silently_admit_bad_layouts_or_new_semantic_facts(tmp_path,value):
    base=build(tmp_path,model())
    try:
        r=base.layout_projection_payload(value)
        assert r['status']=='refused' and 'package' not in r
    finally:base.close()


def test_partial_typed_extent_and_overlap_share_clean_admission_refusal(tmp_path):
    m=model();m['target_equates']=[dict(name='TYPED',value=0x4000,address_domain='runtime',
        extent_bytes=16,value_representation='hex',group='fixture')]
    base=build(tmp_path,m)
    try:
        o=overlay(m);o['memory_layouts'][0]['placements'].append(dict(region_id='workspace',runtime_address=0xe0000))
        assert base.layout_projection_payload(o)['reason']=='partial_or_ambiguous_runtime_reference'
        o['memory_layouts'][0]['placements'][-1]['runtime_address']=0x80000
        assert base.layout_projection_payload(o)['reason']=='unrelated_region_overlap'
    finally:base.close()

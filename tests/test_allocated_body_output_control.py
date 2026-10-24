"""Actual return, admission and consumed payload must agree before comparison."""
import copy
import pytest
from amiga_reversing.tools.runtime_allocation import capsule,plan_digest
from amiga_reversing.tools.pandora_rebase_output_compare import admit_allocated_body_control

OWNER='pandora_ui_snapshot_body'

def reports():
    original=dict(status='placement_valid',bootstrap={'entry':0x20000},chip_bytes=0x100000,
                  regions=[dict(region_id=OWNER,runtime_address=0x7f0,size=2304),
                           dict(region_id='display',runtime_address=0xe0000,size=0xd000)])
    plan=dict(status='bounded_allocation_candidate',scope='reviewed_typed_LONG_data_only_not_all_path_alias_proof',
              region_id=OWNER,size=2304,memory_requirement='chip',alignment=2,lifetime='retain_until_DMA_quiescent_exit',
              layout={'items':[original]},fixups=[dict(source_section_index=0,source_offset=0x3402,width=4,
                  encoding='absolute_long_data',address_domain='runtime_only',region_offset=0,staged_value=0x7f0)])
    result=[]
    for base,extra in [(0xf568,0),(0xf5a8,64)]:
        actual=copy.deepcopy(original);actual['regions'][0]['runtime_address']=base
        cap=capsule(plan,scratch_extra=extra)
        lease=dict(base=base,size=2304,plan_sha256=cap['plan_sha256'])
        result.append(dict(config=dict(normal_layout_export=True,original_control=False,assembly_base=0x80000,
            original_binary_sha256='a'*64,layout_plan=actual,layout_plan_sha256=plan_digest(actual),
            runtime_allocation=cap,runtime_payload_sha256='b'*64),
            runtime_allocation=dict(lease=lease,native_admission=dict(status='actual_placement_valid',layout={'items':[actual]})),
            handoff=dict(runtime_allocation=copy.deepcopy(lease),payload_sha256='b'*64),
            allocation_loader_identity={'sha256':'c'*64}))
    return result


def test_two_actual_allocator_returns_admit_without_changing_other_regions():
    admit_allocated_body_control(*reports())


@pytest.mark.parametrize('mutation',['returned_base','unadmitted','consumed_input','other_region','contract'])
def test_false_allocation_binding_refuses(mutation):
    a,b=reports()
    if mutation=='returned_base':b['runtime_allocation']['lease']['base']+=8
    elif mutation=='unadmitted':b['runtime_allocation']['native_admission']['status']='refused'
    elif mutation=='consumed_input':b['handoff']['payload_sha256']='d'*64
    elif mutation=='other_region':b['config']['layout_plan']['regions'][1]['runtime_address']+=0x10000
    else:
        b['config']['runtime_allocation']['plan']['fixups'][0]['source_offset']+=4
        b['config']['runtime_allocation']['plan_sha256']=plan_digest(b['config']['runtime_allocation']['plan'])
    with pytest.raises((ValueError,AssertionError)):admit_allocated_body_control(a,b)

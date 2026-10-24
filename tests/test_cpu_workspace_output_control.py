"""The CPU parent and keyboard are separate, explicitly scoped movements."""
import copy
import pytest
from amiga_reversing.tools.pandora_rebase_output_compare import admit_cpu_workspace_control


def reports():
    a=dict(config=dict(normal_layout_export=True,original_control=False,assembly_base=0x80000,
        original_binary_sha256='original',layout_plan=dict(bootstrap={'entry':0x20000},chip_bytes=0x100000,
        regions=[dict(region_id='pandora_cpu_workspace',runtime_address=0x39fc,size=0xbb6c),
                 dict(region_id='raster',parent_region_id='pandora_cpu_workspace',runtime_address=0x39fc,size=400),
                 dict(region_id='grid',parent_region_id='pandora_cpu_workspace',runtime_address=0x4000,size=0xb568),
                 dict(region_id='keyboard_state',runtime_address=0x397c,size=128),
                 dict(region_id='display',runtime_address=0xe0000,size=0xd000)])))
    b=copy.deepcopy(a)
    for r in b['config']['layout_plan']['regions']:
        if r['region_id'] in ('pandora_cpu_workspace','raster','grid'):r['runtime_address']+=0x2684
        elif r['region_id']=='keyboard_state':r['runtime_address']=0x5a00
    return a,b


def test_keyboard_has_an_independent_delta():
    admit_cpu_workspace_control(*reports())


@pytest.mark.parametrize('defect',['child','unrelated','missing_keyboard','contract'])
def test_unadmitted_changes_refuse(defect):
    a,b=reports();rows=b['config']['layout_plan']['regions']
    if defect=='child':rows[1]['runtime_address']+=2
    elif defect=='unrelated':rows[-1]['runtime_address']+=0x10000
    elif defect=='missing_keyboard':rows[3]['runtime_address']=0x397c
    else:b['config']['layout_plan']['bootstrap']['entry']+=4
    with pytest.raises(ValueError):admit_cpu_workspace_control(a,b)

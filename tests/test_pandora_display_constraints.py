"""Retained live Copper high/low updates require the evidenced base congruence."""
import pytest
from tests.test_memory_layouts import region,layout,project


@pytest.mark.parametrize('address,valid',[(0x70000,True),(0xd8000,False),(0xe0000,True)])
def test_display_group_alignment_preserves_retained_split_pointer_contract(tmp_path,address,valid):
    root=region('display',0x70000,0xd000,kind='display');root['alignment']=0x10000
    result=project(tmp_path,[root,region('bank0',0x70000,32000,parent='display',kind='display'),
        region('bank1',0x78000,20480,parent='display',kind='display')],layout([('display',address)]))
    assert result['status']==('placement_valid' if valid else 'refused')
    if valid:
        by_id={r['region_id']:r for r in result['regions']}
        assert by_id['bank0']['runtime_address']==address
        assert by_id['bank1']['runtime_address']==address+0x8000
    else:assert result['reason']=='invalid_extent_or_alignment'

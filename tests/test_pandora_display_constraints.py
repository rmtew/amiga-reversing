"""Retained live Copper high/low updates require the evidenced base congruence."""
import pytest
from tests.test_memory_layouts import region,layout,project


@pytest.mark.parametrize('address,valid',[(0x70000,True),(0xd8000,False),(0xe0000,True)])
def test_display_group_alignment_preserves_retained_split_pointer_contract(tmp_path,address,valid):
    root=region('display',0x70000,0xd000,kind='display');root['alignment']=0x10000
    regions=[root,region('bank0',0x70000,32000,parent='display',kind='display'),
        region('bank1',0x78000,20480,parent='display',kind='display'),
        region('hit',0x77d00,768,parent='display'),region('palette',0x77fe0,32,parent='hit')]
    result=project(tmp_path,regions,layout([('display',address)]))
    assert result['status']==('placement_valid' if valid else 'refused')
    if valid:
        by_id={r['region_id']:r for r in result['regions']}
        assert by_id['bank0']['runtime_address']==address
        assert by_id['bank1']['runtime_address']==address+0x8000
        for original in regions:
            placed=by_id[original['region_id']]['runtime_address']
            assert placed & 0xffff == original['runtime_address'] & 0xffff
        bank0=by_id['bank0']['runtime_address']
        # Recorded pre-low-write counters in BPL2/4. High WORD changes first;
        # the old low WORD remains until the following Copper write.
        for old_hybrid in (0x70002,0x70006):
            hybrid=(bank0 & 0xffff0000) | (old_hybrid & 0xffff)
            assert hybrid & 0xffff == old_hybrid & 0xffff
            assert hybrid==bank0+(old_hybrid-0x70000)
            assert bank0 <= hybrid and hybrid+2 <= bank0+40
    else:assert result['reason']=='invalid_extent_or_alignment'

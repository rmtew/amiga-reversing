import pytest
from amiga_reversing.tools.observed_layout_mapping import observed_address,abandoned_ranges


def plan():
    return dict(regions=[dict(original_address=0x10000,runtime_address=0x80000,size=0x55370),
       dict(original_address=0x397c,runtime_address=0x6000,size=0xbbec),
       dict(original_address=0x39fc,runtime_address=0x6080,size=0x190,parent_region_id='cpu')])


def test_read_mapping_preserves_shared_alias_delta_and_scalar_values():
    p=plan()
    assert observed_address(p,0x3b9a,4)==0x621e
    assert observed_address(p,0x39fc,400)==0x6080
    assert observed_address(p,0x20000,4)==0x90000
    assert observed_address(p,0xdff000,2)==0xdff000


def test_active_workspace_in_old_image_is_not_falsely_guarded_as_abandoned():
    p=plan()
    assert abandoned_ranges(p,0x10000,0x55370)==[(0x11bec,0x53784)]
    assert abandoned_ranges(p,0x397c,0xbbec)==[(0x397c,0x2684)]


def test_partial_and_conflicting_alias_reads_refuse():
    p=plan()
    with pytest.raises(ValueError):observed_address(p,0x397a,4)
    p['regions'][2]['runtime_address']+=2
    with pytest.raises(ValueError):observed_address(p,0x39fc,4)


def test_independent_keyboard_and_shared_app_grid_need_no_keyboard_parent():
    p=dict(regions=[dict(region_id='keyboard',original_address=0x397c,runtime_address=0x6000,size=128),
       dict(region_id='app_grid',original_address=0x39fc,runtime_address=0x6080,size=0xbb6c),
       dict(region_id='raster',parent_region_id='app_grid',original_address=0x39fc,runtime_address=0x6080,size=400),
       dict(region_id='grid',parent_region_id='app_grid',original_address=0x4000,runtime_address=0x6684,size=0xb568)])
    assert observed_address(p,0x39bc,1)==0x6040
    assert observed_address(p,0x39fc,4)==0x6080
    assert observed_address(p,0x4000,4)==0x6684
    # The actual app +$604 overlay remains the same physical grid prefix.
    assert observed_address(p,0x39fc,1)+0x604==observed_address(p,0x4000,4)
    p['regions'][0]['runtime_address']=0x7000
    assert observed_address(p,0x39bc,1)==0x7040
    assert observed_address(p,0x4000,4)==0x6684


def test_stale_A4_probe_is_one_owned_byte_not_an_extended_grid():
    parent=dict(region_id='app_grid',original_address=0x39fc,runtime_address=0x6080,size=0xbbb3)
    grid=dict(region_id='grid',parent_region_id='app_grid',original_address=0x4000,
              runtime_address=0x6684,size=0xb568)
    p=dict(regions=[parent,grid])
    assert grid['original_address']+grid['size']==0xf568
    assert observed_address(p,0xf568+0x46,1)==0x11c32
    with pytest.raises(ValueError):observed_address(p,0xf568+0x46,2)
    # Ownership padding is deliberately not treated as another semantic access.
    assert abandoned_ranges(p,0x10000,0x55370)[0][0]==0x11c33

"""Exact PCM interval admission and corruption negatives; synthetic float data."""
import struct
import pytest
from amiga_reversing.tools.pandora_rebase_output_compare import pcm_interval, wav_info, require_loader_family, admit_cursor_control


def wav(path, values, *, channels=2, tag=3):
    data=struct.pack('<'+'f'*len(values),*values)
    fmt=struct.pack('<HHIIHH',tag,channels,44100,44100*channels*4,channels*4,32)
    body=b'WAVEfmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(data))+data
    path.write_bytes(b'RIFF'+struct.pack('<I',len(body))+body)
    return path


def test_pcm_compares_every_sample_in_declared_interval(tmp_path):
    values=[i/128 for i in range(64)]
    a=wav(tmp_path/'a.wav',values);b=wav(tmp_path/'b.wav',values)
    r=pcm_interval(a,b,0,480)
    assert r['status']=='pass' and r['compared_stereo_frames']==5
    assert r['original_interval_sha256']==r['candidate_interval_sha256']
    values[4]=0.75;wav(b,values)
    r=pcm_interval(a,b,0,480)
    assert r['status']=='mismatch' and r['first_different_sample']==2


def test_pre_game_exclusion_is_explicit_and_does_not_hide_game_changes(tmp_path):
    values=[0.0]*64;a=wav(tmp_path/'a.wav',values);values[0]=1.0;b=wav(tmp_path/'b.wav',values)
    r=pcm_interval(a,b,1000,1500)
    assert r['status']=='pass' and r['start_sample']==13
    values[28]=1.0;wav(b,values)
    assert pcm_interval(a,b,1000,1500)['status']=='mismatch'


@pytest.mark.parametrize('channels,tag',[(1,3),(2,1)])
def test_wrong_capture_format_is_refused(tmp_path,channels,tag):
    with pytest.raises(ValueError):wav_info(wav(tmp_path/'bad.wav',[0.0]*32,channels=channels,tag=tag))


def test_truncation_or_missing_interval_never_passes(tmp_path):
    a=wav(tmp_path/'a.wav',[0.0]*64);b=wav(tmp_path/'b.wav',[0.0]*64)
    with pytest.raises(ValueError):pcm_interval(a,b,0,1_000_000)
    b.write_bytes(b.read_bytes()[:-4])
    with pytest.raises(ValueError):wav_info(b)


def test_common_loader_profile_requires_same_guest_work_not_just_same_reservations():
    import copy
    a=dict(config=dict(loader_family_mode='common_guest_seed_program',
        loader_seed_copies=[dict(source_offset=4,runtime_address=0xe0088,size=4)],
        loader_family=[dict(layout_id='original',layout_plan_sha256='a'*64)],
        loader_shared_reservations=[[0xe0088,8]]))
    b=copy.deepcopy(a)
    require_loader_family(a,b)
    b['config']['loader_seed_copies'][0]['runtime_address']+=4
    with pytest.raises(ValueError,match='Different guest seed programs'):require_loader_family(a,b)
    b=copy.deepcopy(a);b['config'].pop('loader_family_mode')
    with pytest.raises(ValueError,match='Different loader seed program modes'):require_loader_family(a,b)


def cursor_controls():
    import copy
    a=dict(config=dict(normal_layout_export=True,original_control=False,assembly_base=0x80000,
        original_binary_sha256='a'*64,layout_plan=dict(bootstrap={'contract_id':'retained'},chip_bytes=0x100000,
        regions=[dict(region_id='image',runtime_address=0x80000),
                 dict(region_id='display',runtime_address=0x70000),
                 dict(region_id='pandora_cursor_sprites',runtime_address=0x65370,size=140),
                 dict(region_id='seed',parent_region_id='pandora_cursor_sprites',runtime_address=0x653f8,
                      loader_seed=dict(source_offset=0x453f8,runtime_address=0x653f8,size=4))])))
    b=copy.deepcopy(a)
    for region in b['config']['layout_plan']['regions'][2:]:
        region['runtime_address']+=0xe0000-0x65370
        if 'loader_seed' in region:region['loader_seed']['runtime_address']+=0xe0000-0x65370
    return a,b


def test_independent_cursor_control_is_a_distinct_bounded_contract():
    a,b=cursor_controls()
    admit_cursor_control(a,b)


@pytest.mark.parametrize('mutation',['image','display','seed','unmoved','bootstrap'])
def test_cursor_control_does_not_admit_unrelated_changes(mutation):
    import copy
    a,b=cursor_controls()
    if mutation=='image':b['config']['assembly_base']=0x90000
    elif mutation=='display':b['config']['layout_plan']['regions'][1]['runtime_address']+=8
    elif mutation=='seed':b['config']['layout_plan']['regions'][3]['loader_seed']['source_offset']+=2
    elif mutation=='bootstrap':b['config']['layout_plan']['bootstrap']['contract_id']='replacement'
    else:b=copy.deepcopy(a)
    with pytest.raises(ValueError):admit_cursor_control(a,b)


def display_controls():
    import copy
    a,_=cursor_controls()
    regions=a['config']['layout_plan']['regions']
    regions[1]=dict(region_id='pandora_display_storage',runtime_address=0x70000,size=0xd000)
    regions.extend([dict(region_id='pandora_framebuffer_bank0',parent_region_id='pandora_display_storage',runtime_address=0x70000,size=32000),
        dict(region_id='pandora_framebuffer_bank1_world',parent_region_id='pandora_display_storage',runtime_address=0x78000,size=20480),
        dict(region_id='hit',parent_region_id='pandora_display_storage',runtime_address=0x77d00,size=768,
            loader_seed=dict(source_offset=0x57d00,runtime_address=0x77d00,size=2))])
    b=copy.deepcopy(a)
    for region in b['config']['layout_plan']['regions']:
        if region['region_id']=='pandora_display_storage' or region.get('parent_region_id')=='pandora_display_storage':
            region['runtime_address']+=0x68000
            if 'loader_seed' in region:region['loader_seed']['runtime_address']+=0x68000
    return a,b


def test_display_family_control_and_native_dma_coordinates():
    from amiga_reversing.tools.pandora_rebase_output_compare import admit_display_control,display_ranges,normalize_dma_address
    a,b=display_controls();admit_display_control(a,b)
    assert display_ranges(b)==[('pandora_framebuffer_bank0',0xd8000,0xdfd00),
        ('pandora_framebuffer_bank1_world',0xe0000,0xe5000)]
    assert normalize_dma_address(a,0x75028)==normalize_dma_address(b,0xdd028)
    assert normalize_dma_address(b,0x75028)==('fixed',0x75028)


@pytest.mark.parametrize('mutation',['cursor','seed_source','bank_delta','image','bootstrap'])
def test_display_control_refuses_unrelated_or_incoherent_changes(mutation):
    from amiga_reversing.tools.pandora_rebase_output_compare import admit_display_control
    a,b=display_controls();regions=b['config']['layout_plan']['regions']
    if mutation=='cursor':regions[2]['runtime_address']+=2
    elif mutation=='seed_source':regions[-1]['loader_seed']['source_offset']+=2
    elif mutation=='bank_delta':regions[-2]['runtime_address']+=2
    elif mutation=='image':b['config']['assembly_base']+=0x10000
    else:b['config']['layout_plan']['bootstrap']['contract_id']='replacement'
    with pytest.raises(ValueError):admit_display_control(a,b)

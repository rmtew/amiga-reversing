"""Exact PCM interval admission and corruption negatives; synthetic float data."""
import struct
import pytest
from amiga_reversing.tools.pandora_rebase_output_compare import pcm_interval, wav_info


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

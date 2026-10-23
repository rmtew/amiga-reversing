"""Fixed-layout patch admission; defaults never enable corrections implicitly."""
from copy import deepcopy
import pytest
from amiga_reversing.tools.optional_patch import apply_patches, sha256


def manifest():
    return {'schema_version':1, 'layout':'raw-single-section',
            'original_sha256':sha256(b'abcdefgh'), 'patches':[
                {'id':'one','start':'s0:00000002:instruction','end':'s0:00000004:instruction',
                 'expected_hex':b'cd'.hex(),'replacement_hex':b'XY'.hex(),
                 'rationale':'test correction','preconditions':['bounded fixture'],'conflicts':[]}]}


def test_default_is_original_and_selection_is_explicit():
    m=manifest()
    assert apply_patches(b'abcdefgh',m,[]) == (b'abcdefgh',[])
    result,selected=apply_patches(b'abcdefgh',m,['one'])
    assert result == b'abXYefgh' and len(result)==8 and len(selected)==1


@pytest.mark.parametrize('case', ['hash','expected','resize','range','anchor','unknown','duplicate','overlap','conflict'])
def test_refuses_stale_ambiguous_or_layout_changing_patches(case):
    m=manifest(); p=m['patches'][0]; enabled=['one']
    if case=='hash': m['original_sha256']='bad'
    if case=='expected': p['expected_hex']='0000'
    if case=='resize': p['replacement_hex']='00'
    if case=='range': p['end']='s0:00000010:instruction'
    if case=='anchor': p['start']='s1:00000002:instruction'
    if case=='unknown': enabled=['missing']
    if case=='duplicate': enabled=['one','one']
    if case in ('overlap','conflict'):
        other=deepcopy(p);other['id']='two';m['patches'].append(other);enabled.append('two')
        if case=='conflict': p['conflicts']=['two']
    with pytest.raises(ValueError): apply_patches(b'abcdefgh',m,enabled)


def test_cli_default_preserves_original_and_refuses_existing_or_source_destinations(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from amiga_reversing.disasm import project_paths
    from amiga_reversing.disasm.binary_source import BinarySourceKind
    from amiga_reversing.tools.optional_patch import main
    source=tmp_path/'targets/fixture/binary.bin';source.parent.mkdir(parents=True);source.write_bytes(b'abcdefgh')
    m=manifest();m['target_id']='fixture'; spec=tmp_path/'patch.json';spec.write_text(json.dumps(m))
    monkeypatch.setattr(project_paths,'PROJECT_ROOT',tmp_path)
    monkeypatch.setattr(project_paths,'resolve_project_paths',lambda _:SimpleNamespace(binary_source=SimpleNamespace(kind=BinarySourceKind.RAW_BINARY,read_bytes=source.read_bytes)))
    output=tmp_path/'bin/rebuilt/default'
    argv=['--manifest',str(spec),'--output-directory',str(output)]
    assert main(argv)==0
    assert (output/'payload.bin').read_bytes()==source.read_bytes()==b'abcdefgh'
    with pytest.raises(FileExistsError):main(argv)
    with pytest.raises(ValueError):main(['--manifest',str(spec),'--output-directory',str(source.parent)])
    assert source.read_bytes()==b'abcdefgh'


def test_cli_refuses_unresolved_canonical_boundary_before_writing(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from amiga_reversing.disasm import project_paths,c_backend
    from amiga_reversing.disasm.binary_source import BinarySourceKind
    from amiga_reversing.tools.optional_patch import main
    m=manifest();m['target_id']='fixture';spec=tmp_path/'patch.json';spec.write_text(json.dumps(m))
    monkeypatch.setattr(project_paths,'PROJECT_ROOT',tmp_path)
    monkeypatch.setattr(project_paths,'resolve_project_paths',lambda _:SimpleNamespace(binary_source=SimpleNamespace(kind=BinarySourceKind.RAW_BINARY,read_bytes=lambda:b'abcdefgh')))
    closed=[]
    monkeypatch.setattr(c_backend,'build_project_listing_artifact_profile',lambda _:(None,None,SimpleNamespace(row_for_source_offset=lambda **kwargs:None,close=lambda:closed.append(True))))
    output=tmp_path/'bin/rebuilt/refused'
    with pytest.raises(ValueError,match='canonical instruction'):
        main(['--manifest',str(spec),'--enable','one','--output-directory',str(output)])
    assert closed==[True] and not output.exists()

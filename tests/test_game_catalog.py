"""Catalog identity/context and private materialization are one source contract."""
import copy
import hashlib
import json
import os
from pathlib import Path
import pytest
from amiga_reversing.disasm import game_catalog as catalog
from amiga_reversing.disasm.binary_source import ArtifactBinarySource,resolve_target_binary_source,write_source_descriptor
from amiga_reversing.disasm.projects import create_project,get_project
from amiga_reversing.disasm.target_metadata import TargetMetadata,write_target_metadata

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def family(tmp_path):
    data=b'\x4e\x75';artifact=hashlib.sha256(data).hexdigest()
    value=dict(schema_version=1,id='fixture',name='Fixture',releases={'st':dict(platform='atari-st',edition='synthetic',media=[artifact])},
               artifacts={artifact:dict(size=2,role='program')},sources={artifact:dict(kind='private_media',format='bytes')},derivations={},
               targets={'st_program':dict(release='st',artifact=artifact,context=dict(kind='raw',address_model='runtime_absolute',load_address=0x1000,entrypoint=0x1000,code_start_offset=0,phase='handoff'))},correspondences=[])
    (tmp_path/'games').mkdir();(tmp_path/'games/fixture.json').write_text(json.dumps(value))
    create_project('st_program',project_root=tmp_path)
    target=tmp_path/'targets/st_program';write_source_descriptor(target,dict(kind='artifact',family='fixture',target='st_program'))
    write_target_metadata(target,TargetMetadata(target_type='raw',entry_register_seeds=()))
    return tmp_path,value,data,artifact,target


def save(root,value):
    (root/'games/fixture.json').write_text(json.dumps(value))


def test_unavailable_media_can_be_browsed_without_recovery(family):
    root,value,data,artifact,target=family
    source=resolve_target_binary_source(target,root)
    assert isinstance(source,ArtifactBinarySource) and source.backend_name=='atari-st-raw'
    project=get_project('st_program',root)
    assert not project.ready and project.game_family=='fixture' and project.release_id=='st'
    assert project.artifact_id==artifact and project.artifact_phase=='handoff'
    assert not (root/'.amiga_reversing/artifacts').exists()
    with pytest.raises(FileNotFoundError):source.read_bytes()


def test_private_binding_materializes_one_content_identity_and_rejects_corruption(family):
    root,value,data,artifact,target=family
    original=root/'private.bin';original.write_bytes(data)
    catalog.bind_source(root,'fixture',artifact,original)
    source=resolve_target_binary_source(target,root)
    assert source.available and source.read_bytes()==data
    path=source.materialized_path
    assert path.parent==root/'.amiga_reversing/artifacts'
    original.unlink()
    assert source.read_bytes()==data
    path.write_bytes(b'xx')
    with pytest.raises(ValueError,match='identity mismatch'):source.read_bytes()


def test_wrong_source_does_not_install_private_binding(family):
    root,value,data,artifact,target=family
    path=root/'wrong.bin';path.write_bytes(b'wrong')
    with pytest.raises(ValueError,match='identity'):catalog.bind_source(root,'fixture',artifact,path)
    assert not (root/'.amiga_reversing/artifact_sources.json').exists()


def test_binding_revision_changes_with_phase_or_platform(family):
    root,value,data,artifact,target=family
    original=catalog.binding_revision(value,'st_program')
    changed=copy.deepcopy(value);changed['targets']['st_program']['context']['phase']='pre_handoff'
    assert catalog.binding_revision(changed,'st_program')!=original
    changed=copy.deepcopy(value);changed['releases']['st']['platform']='amiga'
    assert catalog.binding_revision(changed,'st_program')!=original
    changed=copy.deepcopy(value);changed['releases']['st']['edition']='clearer prose'
    assert catalog.binding_revision(changed,'st_program')==original


@pytest.mark.parametrize('mutation',[lambda p:p.update(schema_version=True),
 lambda p:p['targets']['st_program'].update(artifact='0'*64),
 lambda p:p['targets']['st_program']['context'].update(entrypoint=0x1002),
 lambda p:p['targets']['st_program']['context'].update(phase='guess'),
 lambda p:p['releases']['st'].update(platform='unknown'),
 lambda p:p['artifacts'][next(iter(p['artifacts']))].update(size=True)])
def test_invalid_context_and_identity_are_not_admitted(family,mutation):
    root,value,data,artifact,target=family
    mutation(value)
    with pytest.raises(ValueError):catalog.validate(value,root)


def test_duplicate_target_across_families_is_not_silently_chosen(family):
    root,value,data,artifact,target=family
    other=copy.deepcopy(value);other['id']='other'
    (root/'games/other.json').write_text(json.dumps(other))
    with pytest.raises(ValueError,match='multiple game families'):catalog.target_link(root,'st_program')


def test_unique_counterpart_refuses_ambiguity_and_changed_data():
    left=b'prefix meaningful code suffix'
    result=catalog.unique_counterpart(left,7,15,b'---meaningful code---')
    assert result['offset']==3
    assert catalog.unique_counterpart(left,7,15,b'changed') is None
    with pytest.raises(ValueError,match='ambiguous'):catalog.unique_counterpart(left,7,15,b'meaningful code meaningful code ')
    with pytest.raises(ValueError):catalog.unique_counterpart(left,-1,2,left)


def test_correspondence_requires_equal_qualified_range_identities(family):
    root,value,data,artifact,target=family
    span=dict(target='st_program',offset=0,size=2,sha256=artifact)
    link=dict(id='same',kind='identical_bytes',role='code',left=span,right=copy.deepcopy(span),evidence='fixture')
    value['correspondences']=[link];save(root,value)
    original=root/'private.bin';original.write_bytes(data);catalog.bind_source(root,'fixture',artifact,original)
    assert catalog.verify_correspondence(root,'fixture','same')['id']=='same'
    changed=copy.deepcopy(value);changed['correspondences'][0]['right']['sha256']='0'*64
    with pytest.raises(ValueError,match='identity differs'):catalog.validate(changed,root)
    changed=copy.deepcopy(value);changed['correspondences'][0]['left']['offset']=1
    with pytest.raises(ValueError,match='range'):catalog.validate(changed,root)
    value['correspondences'].append(copy.deepcopy(link))
    with pytest.raises(ValueError,match='duplicate correspondence'):catalog.validate(value,root)


def test_artifact_context_selects_atari_reproduction_and_identity(family):
    root,value,data,artifact,target=family
    original=root/'private.bin';original.write_bytes(data);catalog.bind_source(root,'fixture',artifact,original)
    from amiga_reversing.disasm.manual_actions import build_target_identity
    from amiga_reversing.disasm.reproduction import backend_for_binary_source
    source=resolve_target_binary_source(target,root)
    assert backend_for_binary_source(source)=='atari-st-raw'
    stamp=build_target_identity(source)
    assert stamp['source_kind']=='artifact' and stamp['platform']=='atari-st'
    assert stamp['artifact_id']==artifact and stamp['binding_revision']==source.binding_revision


def test_raw_artifact_is_an_admitted_export_and_oracle_source_kind():
    from amiga_reversing.disasm.binary_source import BinarySourceKind
    from amiga_reversing.disasm.oracle_compatibility import _vasm_format_for_source_kind
    from amiga_reversing.disasm.source_export import SOURCE_BINARY_RENDERERS
    assert BinarySourceKind.ARTIFACT.is_raw
    assert not BinarySourceKind.HUNK_FILE.is_raw
    assert _vasm_format_for_source_kind(BinarySourceKind.ARTIFACT)=='-Fbin'
    assert BinarySourceKind.ARTIFACT in SOURCE_BINARY_RENDERERS


def derivation_fixture(family):
    root,value,_,_,target=family
    from tests.test_stx_recovery import fixture
    image,plan=fixture()
    word=b'\x11\x22';plan['actions'].append(dict(op='capture',file='word.bin',address=0x2000,size=2,sha256=catalog.digest(word)))
    image_id=catalog.digest(image);output=catalog.digest(bytes.fromhex('11223344'));word_id=catalog.digest(word)
    value['artifacts']={image_id:dict(size=len(image),role='media'),output:dict(size=4,role='decoded'),word_id:dict(size=2,role='slice')}
    value['sources']={image_id:dict(kind='private_media',format='stx')}
    value['releases']['st']['media']=[image_id]
    value['targets']['st_program']['artifact']=output
    recipe=root/'recipe.json';recipe.write_text(json.dumps(plan))
    value['derivations']={'decode':dict(kind='stx_cpu_recovery',input=image_id,recipe='recipe.json',recipe_sha256=catalog.digest(recipe.read_bytes()),outputs={'result.bin':output,'word.bin':word_id})}
    save(root,value)
    source=root/'input.stx';source.write_bytes(image);catalog.bind_source(root,'fixture',image_id,source)
    return root,value,image_id,output,word_id,recipe


def test_recipe_outputs_are_cached_once_and_recipe_mutation_invalidates_binding(family,monkeypatch):
    root,value,image,output,word,recipe=derivation_fixture(family)
    monkeypatch.setenv('AMIGA_C_BACKEND_DLL_ROOT',str(ROOT))
    from amiga_reversing.disasm import stx_recovery
    original=stx_recovery.recover;calls=[]
    def counted(*args,**kwargs):calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(stx_recovery,'recover',counted)
    assert catalog.materialize(root,'fixture',output).read_bytes()==bytes.fromhex('11223344')
    assert catalog.materialize(root,'fixture',word).read_bytes()==b'\x11\x22'
    assert calls==[1]
    recipe.write_text(recipe.read_text()+' ')
    with pytest.raises(ValueError,match='stale recovery recipe'):catalog.load_family(root,'fixture')


def test_derived_input_override_and_recipe_escape_are_refused(family):
    root,value,image,output,word,recipe=derivation_fixture(family)
    with pytest.raises(ValueError,match='only root'):catalog.bind_source(root,'fixture',output,root/'input.stx')
    value['derivations']['decode']['recipe']='../outside.json'
    with pytest.raises(ValueError,match='escapes project'):catalog.validate(value,root)


def test_artifact_cycles_and_unbound_outputs_are_refused(family):
    root,value,image,output,word,recipe=derivation_fixture(family)
    broken=copy.deepcopy(value);broken['artifacts']['0'*64]=dict(size=1,role='orphan')
    with pytest.raises(ValueError,match='no source'):catalog.validate(broken,root)
    plan=json.loads(recipe.read_text());plan['actions']=[dict(op='capture',file='loop.bin',address=0,size=len((root/'input.stx').read_bytes()),sha256=image)]
    recipe.write_text(json.dumps(plan))
    value['artifacts']={image:value['artifacts'][image]};value['sources']={};value['targets']['st_program']['artifact']=image
    value['derivations']['decode'].update(recipe_sha256=catalog.digest(recipe.read_bytes()),outputs={'loop.bin':image})
    with pytest.raises(ValueError,match='cycle'):catalog.validate(value,root)


def test_corpus_entry_retains_qualified_artifact_identity_without_materializing(family):
    root,value,data,artifact,target=family
    from src.scripts.target_usage_manifest import _project_target_manifest_entry
    entry,source=_project_target_manifest_entry(target,root=root)
    assert entry['platform']=='atari-st-raw'
    assert entry['game_family']=='fixture' and entry['release_id']=='st'
    assert entry['artifact_id']==artifact and entry['sha256']==artifact and entry['size']==2
    assert entry['source_available'] is False
    assert not (root/'.amiga_reversing/artifacts').exists()


@pytest.mark.parametrize('changed', [False, True])
def test_raw_artifact_reproduction_compares_bytes_without_object_container(family, monkeypatch, changed):
    from amiga_reversing.disasm import reproduction
    root, value, original, artifact, target = family
    source = resolve_target_binary_source(target, root)
    rebuilt = original[:-1] + b'\0' if changed else original
    monkeypatch.setattr(reproduction, 'reproduction_compare_rebuilt_bytes_with_c_backend_profile',
        lambda *a, **k: pytest.fail('Raw artifact must not enter PRG/hunk object comparison'))
    comparison, profile = reproduction._comparison_for_rebuilt_bytes(source, rebuilt,
        backend='atari-st-raw', policy=dict(mode='exact', comparison='full_file', requested_exactness='full_file', requested_exactness_id=1),
        metadata_path=None, project_root=root, original=original, canonical_rebuilt=rebuilt,
        diff_ranges=[], canonical_diff_ranges=[], file_layout=[])
    assert comparison['full_file_exact'] is (not changed)
    assert profile is None
    assert reproduction._include_dir_for_backend('atari-st-raw', root) == root / 'ext/atarist_includes/devpac_3_10/include'

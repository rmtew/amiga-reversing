"""Source completeness, deterministic extension and standalone build refusals."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import pytest
from tests.test_source_package import package
from amiga_reversing.disasm.source_package import extend_source_package,validate_source_package
ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('allocate_image,high_masks,count',[(None,None,8),(False,None,6),(True,False,7),(True,True,8)])
def test_reference_contract_requests_the_same_guest_owner_family(allocate_image,high_masks,count):
    from amiga_reversing.disasm.hosted_application_export import native_contract,TARGET
    from amiga_reversing.tools.pandora_OS_application import OWNERS,IMAGE_OWNER,HIGH_MASK_OWNER
    class Artifact:
        def __init__(self):self.requested=[]
        def runtime_allocation_plan(self,name,layout):
            self.requested.append(name)
            return dict(status='bounded_allocation_candidate',staged_address=0x80000)
        def runtime_allocation_batch_plan(self,layout,actual):
            assert [p['region_id'] for p in actual['placements']]==self.requested
            return dict(status='actual_placements_valid',uncovered_runtime_extents=[])
        def loaded_backend_identity(self):return dict(sha256='fixture')
    a=Artifact()
    flags={} if allocate_image is None else dict(allocate_image=allocate_image)
    if high_masks is not None:flags['allocate_high_masks']=high_masks
    contract=native_contract(a,TARGET,'hosted',**flags)
    assert tuple(contract['candidates'])==(*OWNERS,IMAGE_OWNER,HIGH_MASK_OWNER)[:count]


def test_high_mask_contract_does_not_bypass_image_profile_precondition():
    from amiga_reversing.disasm.hosted_application_export import native_contract,TARGET
    with pytest.raises(ValueError,match='requires the admitted image'):
        native_contract(None,TARGET,'hosted',allocate_image=False,allocate_high_masks=True)


def record(name,data,kind='application_source'):
    return dict(path=name,size=len(data),data_hex=data.hex(),kind=kind,provenance='fixture')


def test_extension_preserves_game_and_binds_authored_and_generated_sources():
    p=package();extras=[record('runtime.s',b' rts\n'),record('bindings.i',b'BASE EQU 4\n','runtime_bindings')]
    a=extend_source_package(p,extras,application=dict(entry_source='runtime.s'))
    b=extend_source_package(p,list(reversed(extras)),application=dict(entry_source='runtime.s'))
    assert a==b and a['manifest']['source']=='demo.s' and len(a['files'])==4
    assert validate_source_package(a)['assets/a.bin']==b'\0\1\xff'
    with pytest.raises(ValueError,match='collides'):
        extend_source_package(p,[record('demo.s',b'wrong')],application={})
    a['files'][0]['data_base64']=base64.b64encode(b'changed').decode()
    with pytest.raises(ValueError,match='integrity'):validate_source_package(a)


def test_hosted_verification_refuses_rehashed_unreviewed_package(monkeypatch, tmp_path):
    from amiga_reversing.disasm import hosted_application_export as hosted, source_export
    p = package()
    payload = dict(package=p, layout_id='hosted')
    monkeypatch.setattr(source_export, 'source_export_payload', lambda *a, **k:
        dict(package=dict(sha256='different-current-canonical-package')))
    with pytest.raises(ValueError, match='Stale hosted source package'):
        hosted.verify('fixture', payload, tmp_path)


def test_hosted_verification_missing_assembler_is_not_pass(monkeypatch, tmp_path):
    from amiga_reversing.disasm import hosted_application_export as hosted, source_export, oracle_compatibility
    p = package()
    payload = dict(package=p, layout_id='hosted')
    monkeypatch.setattr(source_export, 'source_export_payload', lambda *a, **k: payload)
    monkeypatch.setattr(oracle_compatibility, '_resolve_capability_with_workflow', lambda *a, **k: ({}, {}))
    result = hosted.verify('fixture', payload, tmp_path)
    assert result['status'] == 'missing_prerequisite'
    assert result['exact'] is result['build_verified'] is result['runtime_verified'] is False


@pytest.mark.parametrize('mode',['ok','allocated_image','wrong_game','changed_source','changed_assembler'])
def test_standalone_script_builds_without_repo_imports_and_refuses_stale_inputs(tmp_path,mode):
    root=tmp_path/'extracted';root.mkdir();script=root/'build.py'
    script.write_bytes((ROOT/'tools/amiga_pandora_package_build.py').read_bytes())
    (root/'game.s').write_bytes(b'fixture game source');(root/'runtime.s').write_bytes(b'fixture runtime source')
    data=b'native expected bytes'
    fast=1<<json.loads((ROOT/'knowledge/amiga_hunk_format.json').read_text())['memory_flags']['HUNKB_FAST']['bit']
    hunk=struct.pack('>8I',1011,0,1,0,0,fast|1,1001,1)+bytes.fromhex('4e754e71')+struct.pack('>I',1010)
    assembler=tmp_path/'vasm-fixture'
    assembler.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\nargs=sys.argv\n'+
        f"Path(args[args.index('-o')+1]).write_bytes({(b'wrong' if mode=='wrong_game' else data)!r} if '-Fbin' in args else {hunk!r})\n"+
        ("Path(__file__).write_text(Path(__file__).read_text()+'# changed\\n')\n" if mode=='changed_assembler' else ''))
    assembler.chmod(0o755)
    records=[dict(path=p.name,size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.iterdir()]
    manifest=dict(files=records,target_identity_sha256='original',application=dict(profile='pandora-dos-owned-prefix-v1',
        game_source='game.s',entry_source='runtime.s',expected_payload_sha256=hashlib.sha256(data).hexdigest()))
    if mode=='allocated_image':manifest['application']['profile']='pandora-dos-allocated-image-v1'
    (root/'manifest.json').write_text(json.dumps(manifest))
    if mode=='changed_source':(root/'game.s').write_bytes(b'changed')
    result=subprocess.run([sys.executable,str(script),'--vasm',str(assembler)],cwd=tmp_path,capture_output=True,text=True)
    if mode in ('ok','allocated_image'):
        assert result.returncode==0,result.stderr
        receipt=json.loads((root/'bin/build-receipt.json').read_text())
        assert receipt['files']['Pandora']['sha256']==hashlib.sha256(hunk).hexdigest()
        assert receipt['original_binary_exact'] is False
    else:
        assert result.returncode!=0 and not (root/'bin/build-receipt.json').exists()

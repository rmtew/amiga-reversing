"""Corrected runtime payloads keep exact provenance and reject old code mappings."""
import json
from types import SimpleNamespace
import pytest
from amiga_reversing.disasm import optional_artifact as optional, derived_artifact
from amiga_reversing.disasm.binary_source import BinarySourceKind
from amiga_reversing.tools.optional_patch import sha256
from amiga_reversing.tools import copperline_session as session, direct_payload_adapter as adapter


def fixture(tmp_path,monkeypatch):
    original=b'abcdefgh';payload=b'abXYefgh'
    monkeypatch.setattr(optional,'resolve_project_paths',lambda _:SimpleNamespace(binary_source=SimpleNamespace(kind=BinarySourceKind.RAW_BINARY,read_bytes=lambda:original)))
    m={'schema_version':1,'kind':optional.KIND,'layout':'raw-single-section','artifact_file':'payload.bin','target_id':'fixture','manifest_sha256':'a'*64,'original_sha256':sha256(original),'output_sha256':sha256(payload),'size':8,'enabled':['guard'],'default_original':False,'patches':[{'id':'guard','start':'s0:00000002:instruction','end':'s0:00000004:instruction','expected_hex':b'cd'.hex(),'replacement_hex':b'XY'.hex(),'rationale':'fixture','preconditions':['fixture'],'conflicts':[]}]}
    (tmp_path/'payload.bin').write_bytes(payload)
    path=tmp_path/'receipt.json';path.write_text(json.dumps(m))
    return path,m


def test_exact_optional_runtime_contract(tmp_path,monkeypatch):
    p,m=fixture(tmp_path,monkeypatch)
    assert derived_artifact.validate_manifest(p,'fixture')==(m,tmp_path/'payload.bin')
    data=b'abXYefgZ';(tmp_path/'payload.bin').write_bytes(data);m['output_sha256']=sha256(data);p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='exact patch ledger'):derived_artifact.validate_manifest(p,'fixture')


@pytest.mark.parametrize('field,value',[('target_id','other'),('original_sha256','0'*64),('size',9),('artifact_file','../payload.bin'),('enabled',[]),('enabled',['unknown']),('default_original',True),('kind','unknown')])
def test_wrong_build_context_refused(tmp_path,monkeypatch,field,value):
    p,m=fixture(tmp_path,monkeypatch);m[field]=value;p.write_text(json.dumps(m))
    with pytest.raises(ValueError):derived_artifact.validate_manifest(p,'fixture')


@pytest.mark.parametrize('offset,admitted',[(0,True),(2,False),(3,False),(4,True)])
def test_optional_scenario_excludes_rewritten_instruction_range(tmp_path,monkeypatch,offset,admitted):
    p,m=fixture(tmp_path,monkeypatch)
    artifact=SimpleNamespace(_runtime_observation_views=({'base_addr':0x10000,'source_start':0,'source_end':8},),memory_regions_payload=lambda:{'items':[]},row_for_source_offset=lambda **k:{'stable_key':f"s0:{k['offset']:08X}:instruction",'start_offset':k['offset']},close=lambda:None)
    monkeypatch.setattr(session,'build_project_listing_artifact_profile',lambda _:(None,None,artifact))
    scenario={'schema_version':1,'identifier':'fixture','target_id':'fixture','phases':[{'name':'root','observable':'direct_payload_handoff'},{'name':'probe','breakpoint_stable_key':f's0:{offset:08X}:instruction','wait_seconds':1}]}
    source=tmp_path/'scenario.json';source.write_text(json.dumps(scenario));out=tmp_path/'compiled.json'
    if admitted:assert session.compile_scenario('fixture',source,out,derived_manifest=p)['phases'][0]['source_offset']==offset
    else:
        with pytest.raises(ValueError,match='inside an optional patch'):session.compile_scenario('fixture',source,out,derived_manifest=p)
        assert not out.exists()


def test_optional_contract_changes_only_payload_identity(tmp_path,monkeypatch):
    from amiga_reversing.disasm import c_backend
    p,m=fixture(tmp_path,monkeypatch)
    artifact=SimpleNamespace(row_for_source_offset=lambda **k:{'stable_key':f"s0:{k['offset']:08X}:instruction"},close=lambda:None)
    monkeypatch.setattr(c_backend,'build_project_listing_artifact_profile',lambda _:(None,None,artifact))
    contract=adapter.DirectPayloadContract('fixture','fixture',m['original_sha256'],0x20000,0x20000,{},0x7fff8,0x48414e44)
    bound,path,_=adapter.bind_derived_contract(contract,p)
    assert bound.payload_sha256==m['output_sha256'] and path==tmp_path/'payload.bin'
    assert bound.reservations==contract.reservations and bound.materialization==contract.materialization


def test_paused_pc_inside_patch_never_claims_original_instruction(tmp_path,monkeypatch):
    p,m=fixture(tmp_path,monkeypatch)
    artifact=SimpleNamespace(row_for_runtime_address=lambda **_: {'start_offset':2},close=lambda:None)
    monkeypatch.setattr(session,'build_project_listing_artifact_profile',lambda _:(None,None,artifact))
    report={'observation':{'pc':'0x10002','active_execution':{'payload':{'status':'pc_matched','payload_offset':'0x2','runtime_base':'0x10000'}}}}
    result=session.resolve_paused_pc('fixture',report,derived_manifest=p)
    assert result['status']=='modified_instruction_range' and 'canonical_row' not in result


def test_runtime_symbols_omit_functions_intersecting_patch(tmp_path,monkeypatch):
    from amiga_reversing.tools import runtime_symbols as symbols
    monkeypatch.setattr(symbols,'_eligible_functions',lambda *_:({'base_addr':0x10000,'source_start':0,'source_end':16},(symbols.FunctionSymbol('before',0,2),symbols.FunctionSymbol('rewritten',2,4),symbols.FunctionSymbol('spanning',0,6),symbols.FunctionSymbol('after',4,8))))
    result=symbols.generate_runtime_symbol_artifact('fixture',tmp_path,artifact=object(),excluded_ranges=((2,4),))
    assert [f['name'] for f in result['functions']]==['before','after']
    assert json.loads((tmp_path/'canonical-runtime-symbols.json').read_text())==result

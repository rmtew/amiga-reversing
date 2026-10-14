import json
from copy import deepcopy
from pathlib import Path

import pytest

from amiga_reversing.tools import copperline_checkpoint as cp
from amiga_reversing.tools.copperline_control import CopperlineError


class SnapshotClient:
    def __init__(self):
        self.regs={'pc':0x105ca,'sp':0x10400,'d0':7};self.saved=None;self.calls=[]
    def registers(self):return dict(self.regs)
    def request(self,method,params=None):
        self.calls.append(method)
        if method=='state.save':
            self.saved=dict(self.regs);Path(params['path']).write_bytes(b'owned-game-state')
        if method=='state.load':self.regs=dict(self.saved)


def fixture(tmp_path):
    c=SnapshotClient();view={'base_addr':0x10000,'source_start':0,'source_end':0x55370}
    phase={'stable_key':'s0:000005CA:instruction','source_offset':0x5ca,'breakpoint_address':0x105ca,'runtime_view':view}
    scenario={'phases':[phase],'symbols':{'runtime_view':view}}
    payload={'status':'pc_matched','payload_offset':'0x5ca','runtime_base':'0x00010000','payload_sha256':'a'*64}
    root={'handoff':{'status':'verified','payload_sha256':'a'*64},'reverse_boundary':{'materialization':{'status':'verified'}}}
    context={'payload_sha256':'a'*64,'derived_manifest_sha256':None,'rom_sha256':'b'*64}
    result={'phases':[dict(status='hit',name='anchor',payload=payload)]}
    identify=lambda *a,**kw:dict(payload)
    path=tmp_path/'checkpoint.json'
    return c,scenario,payload,root,context,result,identify,path


def saved(tmp_path):
    c,s,p,root,ctx,r,identify,path=fixture(tmp_path)
    cp.save(c,path,ctx,s,r,root['handoff'],root['reverse_boundary'],identify=identify,payload_path=Path('unused'))
    return c,s,p,root,ctx,r,identify,path


def test_saved_state_roundtrip_binds_context_and_exact_canonical_anchor(tmp_path):
    c,s,p,root,ctx,r,identify,path=saved(tmp_path)
    record=cp.read_checkpoint(path,ctx)
    c.regs['d0']=99
    outcome=cp.restore(c,path,record,s,Path('unused'),identify)
    assert c.regs['d0']==7 and outcome['status']=='restored'
    assert outcome['root_verification']=='inherited_from_saved_execution'
    assert c.calls==['state.save','state.load','reverse_anchor']


@pytest.mark.parametrize('damage',['other_layout','other_rom','snapshot','held_input','missing_root'])
def test_context_or_provenance_mismatch_refused_before_state_load(tmp_path,damage):
    c,s,p,root,ctx,r,identify,path=saved(tmp_path)
    expected=dict(ctx);record=json.loads(path.read_text())
    if damage=='other_layout':expected['derived_manifest_sha256']='c'*64
    elif damage=='other_rom':expected['rom_sha256']='d'*64
    elif damage=='snapshot':path.with_suffix('.clstate').write_bytes(b'changed')
    elif damage=='held_input':record['inputs_released']=False
    else:record['root']={}
    path.write_text(json.dumps(record))
    with pytest.raises(CopperlineError):cp.read_checkpoint(path,expected)
    assert 'state.load' not in c.calls


def test_wrong_resume_anchor_is_refused_before_loading_or_input(tmp_path):
    c,s,p,root,ctx,r,identify,path=saved(tmp_path)
    record=cp.read_checkpoint(path,ctx);s['phases'][0]['source_offset']=0x9844
    with pytest.raises(CopperlineError,match='saved canonical'):
        cp.restore(c,path,record,s,Path('unused'),identify)
    assert c.calls==['state.save']


@pytest.mark.parametrize('damage',['registers','payload'])
def test_post_load_state_must_reestablish_exact_identity_before_resuming(tmp_path,damage):
    c,s,p,root,ctx,r,identify,path=saved(tmp_path);record=cp.read_checkpoint(path,ctx)
    if damage=='registers':c.saved['sp']+=2
    else:identify=lambda *a,**kw:dict(p,status='ambiguous')
    with pytest.raises(CopperlineError):cp.restore(c,path,record,s,Path('unused'),identify)
    assert c.calls==['state.save','state.load']


def test_failed_scenario_cannot_create_checkpoint(tmp_path):
    c,s,p,root,ctx,r,identify,path=fixture(tmp_path);r['phases'][0]['status']='not_hit'
    with pytest.raises(CopperlineError,match='completed'):
        cp.save(c,path,ctx,s,r,root['handoff'],root['reverse_boundary'],identify=identify,payload_path=Path('unused'))
    assert not c.calls and not path.exists()


def test_successor_retains_root_and_records_snapshot_parent(tmp_path):
    c,s,p,root,ctx,r,identify,path=saved(tmp_path);parent=cp.read_checkpoint(path,ctx)
    next_path=tmp_path/'successor.json'
    cp.save(c,next_path,ctx,s,r,None,None,parent=parent,identify=identify,payload_path=Path('unused'))
    successor=cp.read_checkpoint(next_path,ctx)
    assert successor['root']==root
    assert successor['parent_snapshot_sha256']==parent['snapshot_sha256']


def test_binding_hashes_actual_files_and_rejects_wrong_target(tmp_path):
    from types import SimpleNamespace
    paths={}
    for name in ('rom','emulator','floppy','payload'):
        paths[name]=tmp_path/name;paths[name].write_bytes(name.encode())
    session=SimpleNamespace(host_directory=None,floppy0=paths['floppy'],rom_path=paths['rom'],binary_path=paths['emulator'],target_payload_path=paths['payload'],derived_artifact_manifest=None)
    contract=SimpleNamespace(target_id='target',identifier='direct',payload_sha256=cp.digest(paths['payload']))
    scenario={'target_id':'target','symbols':{'runtime_view':{'base_addr':0x10000}}}
    original=cp.binding(session,contract,scenario)
    paths['rom'].write_bytes(b'other ROM')
    assert cp.binding(session,contract,scenario)['rom_sha256']!=original['rom_sha256']
    with pytest.raises(CopperlineError,match='target/payload'):
        cp.binding(session,contract,dict(scenario,target_id='other'))


def test_checkpoint_receipt_cannot_overwrite_its_binary_snapshot_name(tmp_path):
    with pytest.raises(CopperlineError,match='.json'):
        cp.snapshot_path(tmp_path/'snapshot.clstate')


def test_original_root_cannot_be_saved_as_another_payload_layout(tmp_path):
    c,s,p,root,ctx,r,identify,path=saved(tmp_path);parent=cp.read_checkpoint(path,ctx)
    before=list(c.calls);destination=tmp_path/'wrong-layout.json'
    with pytest.raises(CopperlineError,match='matching root'):
        cp.save(c,destination,dict(ctx,payload_sha256='e'*64),s,r,None,None,parent=parent,identify=identify,payload_path=Path('unused'))
    assert c.calls==before and not destination.exists()

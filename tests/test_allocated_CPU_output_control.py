"""CPU output admission binds real returned bases; comparison stays exact."""
import copy
import pytest
from tests.test_CPU_allocation_boot import contract_fixture
from amiga_reversing.tools.runtime_allocation import capsule,plan_digest
from amiga_reversing.tools.pandora_rebase_output_compare import admit_allocated_CPU_control


def reports(tmp_path):
    _,_,plan=contract_fixture(tmp_path)
    old=plan['region_id'];plan['region_id']='pandora_cpu_workspace'
    for r in plan['layout']['items'][0]['regions']:
        if r['region_id']==old:r['region_id']=plan['region_id']
        if r.get('parent_region_id')==old:r['parent_region_id']=plan['region_id']
    plan['layout']['items'][0]['regions'].append(dict(region_id='keyboard_state',runtime_address=0x6000,size=0x80))
    result=[]
    for base,prior in ((0x6080,0),(0x7080,4096)):
        actual=copy.deepcopy(plan['layout']['items'][0]);owner=next(r for r in actual['regions'] if r['region_id']==plan['region_id'])
        delta=base-owner['runtime_address'];family={owner['region_id']}
        for _ in actual['regions']:
            family.update(r['region_id'] for r in actual['regions'] if r.get('parent_region_id') in family)
        for r in actual['regions']:
            if r['region_id'] in family:r['runtime_address']+=delta
        cap=capsule(plan,prior_allocation_bytes=prior)
        lease=dict(base=base,size=plan['size'],plan_sha256=cap['plan_sha256'],prior_base=0x6080 if prior else 0,prior_size=prior)
        result.append(dict(config=dict(normal_layout_export=True,original_control=False,assembly_base=0x80000,
            original_binary_sha256='a'*64,layout_plan=actual,layout_plan_sha256=plan_digest(actual),
            runtime_allocation=cap,runtime_payload_sha256='b'*64),
            runtime_allocation=dict(lease=lease,native_admission=dict(status='actual_placement_valid',layout={'items':[actual]})),
            handoff=dict(runtime_allocation=copy.deepcopy(lease),payload_sha256='b'*64),allocation_loader_identity={'sha256':'c'*64}))
    return result


def test_CPU_owner_moves_without_requiring_independent_keyboard_to_move(tmp_path):
    admit_allocated_CPU_control(*reports(tmp_path))


@pytest.mark.parametrize('mutation',['base','unadmitted','consumed','prior','contract','keyboard'])
def test_CPU_false_binding_refuses(tmp_path,mutation):
    a,b=reports(tmp_path)
    if mutation=='base':b['runtime_allocation']['lease']['base']+=8
    elif mutation=='unadmitted':b['runtime_allocation']['native_admission']['status']='refused'
    elif mutation=='consumed':b['handoff']['payload_sha256']='d'*64
    elif mutation=='prior':b['runtime_allocation']['lease']['prior_size']=0
    elif mutation=='keyboard':b['config']['layout_plan']['regions'][-1]['runtime_address']+=8
    else:
        b['config']['runtime_allocation']['plan']['fixups'][0]['source_offset']+=4
        b['config']['runtime_allocation']['plan_sha256']=plan_digest(b['config']['runtime_allocation']['plan'])
    with pytest.raises(ValueError):admit_allocated_CPU_control(a,b)


def wait_reports(tmp_path):
    import re
    from amiga_reversing.tools.direct_payload_adapter import build_boot_adf
    result=[]
    for prior in (0,4096):
        d=tmp_path/str(prior);d.mkdir()
        c,payload,_=contract_fixture(d,prior=prior)
        build=build_boot_adf(c,payload,d/'experiment.adf')
        listing=(d/'experiment.bootcode.allocation.lst').read_text()
        start=int(re.search(r'^([0-9A-Fa-f]{8}) await_session_release$',listing,re.M)[1],16)
        identity=dict(base=0x1500,size=build['allocation_boot_code_size'],sha256=build['allocation_boot_code_sha256'])
        report=dict(allocation_loader_identity=identity,boot_phase_fixture=dict(stop=dict(cck=35525509),
            registers=dict(pc=identity['base']+start+10,sr=0,d0=0)))
        result.append((d,report))
    return result


def test_different_boot_lengths_bind_same_assembled_wait_instruction(tmp_path):
    from amiga_reversing.tools.pandora_rebase_output_compare import compare_boot_fixture
    (a,ra),(b,rb)=wait_reports(tmp_path)
    assert ra['boot_phase_fixture']['registers']['pc']!=rb['boot_phase_fixture']['registers']['pc']
    result=compare_boot_fixture(a,b,ra,rb,'canonical_allocated_CPU')
    assert result['control']['block_sha256']==result['candidate']['block_sha256']
    assert result['control']['pc_offset']==result['candidate']['pc_offset']==10
    with pytest.raises(ValueError):compare_boot_fixture(a,b,ra,rb,'canonical_allocated_body')


@pytest.mark.parametrize('mutation',['clock','register','pc','adf','listing','missing_listing_bytes','missing_label'])
def test_wait_comparison_refuses_unbound_or_different_fixture(tmp_path,mutation):
    from amiga_reversing.tools.pandora_rebase_output_compare import compare_boot_fixture
    (a,ra),(b,rb)=wait_reports(tmp_path)
    if mutation=='clock':rb['boot_phase_fixture']['stop']['cck']+=1
    elif mutation=='register':rb['boot_phase_fixture']['registers']['d0']=1
    elif mutation=='pc':rb['boot_phase_fixture']['registers']['pc']+=2
    elif mutation=='adf':
        p=b/'experiment.adf';data=bytearray(p.read_bytes());data[12]^=1;p.write_bytes(data)
    else:
        p=b/'experiment.bootcode.allocation.lst';data=p.read_text()
        if mutation=='listing':data=data.replace('00:00000000 48E7','00:00000000 48E6',1)
        elif mutation=='missing_label':data=data.replace(' await_session_release\n',' absent_wait\n')
        else:data='\n'.join(s for s in data.splitlines() if not s.startswith('00:00000000 '))
        p.write_text(data)
    with pytest.raises(ValueError):compare_boot_fixture(a,b,ra,rb,'canonical_allocated_CPU')

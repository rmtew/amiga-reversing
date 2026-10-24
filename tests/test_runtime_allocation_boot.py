"""Assemble the optional loader and reject stale/untyped native capsules."""
import hashlib
from dataclasses import replace

import pytest

from tests.test_runtime_allocation_plan import fixture
from amiga_reversing.tools.runtime_allocation import capsule,validate_payload
from amiga_reversing.tools.direct_payload_adapter import DirectPayloadContract,build_boot_adf


def native_contract(tmp_path, **options):
    a=fixture(tmp_path)
    try:plan=a.runtime_allocation_plan('body','diagnostic')
    finally:a.close()
    data=bytes.fromhex('4e71b3ca4e754e75000007f0')+bytes(500)
    p=tmp_path/'payload.bin';p.write_bytes(data)
    c=DirectPayloadContract('fixture','fixture',hashlib.sha256(data).hexdigest(),
        0x20000,0x20000,{},0x7fff8,0x48414e44,runtime_allocation=capsule(plan,**options))
    return c,p


@pytest.mark.parametrize('fault',[None,'before_owner','after_owner'])
def test_native_allocation_loader_assembles_inside_boot_limit(tmp_path,fault):
    contract,payload=native_contract(tmp_path,fault=fault)
    result=build_boot_adf(contract,payload,tmp_path/'run.adf')
    assert result['status']=='ok'
    assert (tmp_path/'run.adf').stat().st_size==901120


def test_stale_typed_field_refused_before_build(tmp_path):
    contract,payload=native_contract(tmp_path)
    data=bytearray(payload.read_bytes());data[8:12]=(0x7f2).to_bytes(4,'big');payload.write_bytes(data)
    contract=replace(contract,payload_sha256=hashlib.sha256(data).hexdigest())
    with pytest.raises(ValueError,match='stale'):
        build_boot_adf(contract,payload,tmp_path/'bad.adf')
    assert not (tmp_path/'bad.adf').exists()


def test_runtime_fixup_may_not_change_seed_source(tmp_path):
    contract,payload=native_contract(tmp_path)
    with pytest.raises(ValueError,match='seed'):
        validate_payload(contract.runtime_allocation,payload.read_bytes(),contract.load_address,
                         contract.handoff_marker_address,[(8,0xf0000,4)])


def test_extended_seed_program_keeps_all_loader_branches_in_range(tmp_path):
    contract,payload=native_contract(tmp_path)
    contract=replace(contract,seed_copies=((32,0xd0000,2),(34,0xd0008,2),(36,0xd0010,4)))
    assert build_boot_adf(contract,payload,tmp_path/'seeds.adf')['status']=='ok'

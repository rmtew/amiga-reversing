"""Bounded original-loader aliases: native placement and guest seed execution."""
import ctypes as C
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm.memory_regions import validate_region
from amiga_reversing.tools import direct_payload_adapter as adapter
from tests.test_bootstrap_layouts import build, metadata
from tests.test_memory_layouts import region


def seed_region(**changes):
    return region('seed',0x20004,4) | {'loader_seed':dict(source_offset=4,region_offset=0,size=4)} | changes


def seed_metadata(**changes):
    m=metadata()
    m['memory_regions'].append(seed_region(**changes))
    m['memory_layouts'][0]['placements'].append(dict(region_id='seed',runtime_address=0xe0000))
    return m


def test_native_loader_seed_retains_explicit_original_file_domain(tmp_path):
    artifact=build(tmp_path,seed_metadata())
    try:
        seed=artifact.memory_layouts_payload()['items'][0]['regions'][-1]['loader_seed']
        assert seed==dict(source_offset=4,region_offset=0,size=4,runtime_address=0xe0000,
                          staging_address=0x20004,phase='before_payload_entry')
        assert artifact.memory_regions_payload()['items'][-1]['loader_seed']==dict(source_offset=4,region_offset=0,size=4)
    finally:artifact.close()


@pytest.mark.parametrize('value',[None,[],dict(source_offset=4.5,region_offset=0,size=4),
    dict(source_offset=True,region_offset=0,size=4),dict(source_offset=4,region_offset=0,size=0),
    dict(source_offset=4,region_offset=0,size=5),dict(source_offset=4,region_offset=0,size=4,guess=True)])
def test_invalid_seed_authored_native_parity(tmp_path,value):
    with pytest.raises(ValueError,match='loader_seed'):validate_region(seed_region(loader_seed=value))
    with pytest.raises(RuntimeError,match='memory region'):build(tmp_path,seed_metadata(loader_seed=value))


def test_seed_cannot_invent_original_loader_alias(tmp_path):
    with pytest.raises(RuntimeError,match='loader_seed_original_staging_mismatch'):
        build(tmp_path,seed_metadata(loader_seed=dict(source_offset=3,region_offset=0,size=4)))


def test_seed_needs_identity_bound_bootstrap(tmp_path):
    m=seed_metadata();m['memory_layouts'][0].pop('bootstrap_contract_id');m['memory_layouts'][0].pop('bootstrap_variant')
    with pytest.raises(RuntimeError,match='loader_seed_requires_bootstrap_contract'):build(tmp_path,m)


def direct(copies):
    return adapter.DirectPayloadContract('seed','test','0'*64,0x20000,0x20000,{'a1':0x20000},0x7fff8,0x48414e44,
                                         seed_copies=copies)


def test_matching_aliases_coalesce_but_conflicting_seed_values_refuse():
    assert adapter.normalize_seed_copies(((128,0xe0000,4),(130,0xe0002,4)))==((128,0xe0000,6),)
    with pytest.raises(adapter.DirectPayloadContractError,match='Conflicting'):
        adapter.normalize_seed_copies(((128,0xe0000,4),(160,0xe0002,4)))


@pytest.mark.parametrize('copies',[((511,0xe0000,4),),((128,0x20084,4),),((128,0xe0000,0),),((128,0xe0000,True),)])
def test_source_bounds_and_live_input_are_not_bypassed(copies):
    with pytest.raises(adapter.DirectPayloadContractError):adapter.validate_materialization(direct(copies),512)


def test_seed_reservation_rounding_does_not_claim_padding_purpose():
    copies=((128,0xe0088,4),)
    assert adapter.seed_reservation_spans(copies)==((0xe0088,8),)
    assert (0xe0088,8) in adapter.reservation_plan(direct(copies),512)


def test_paired_controls_own_identical_seed_backing_before_io():
    from dataclasses import replace
    old=((128,0x20080,4),);new=((128,0xe0088,4),)
    common=adapter.seed_reservation_spans(old+new)
    a=replace(direct(old),reservations=common);b=replace(direct(new),reservations=common)
    assert adapter.reservation_plan(a,512)==adapter.reservation_plan(b,512)


@pytest.mark.parametrize('address',[0x20080,0xe0088])
def test_guest_seed_copy_executes_exact_bytes_before_entry(tmp_path,address):
    # Synthetic local call proves the emitted loop; actual startup/Paula is
    # separately qualified through Copperline, never inferred from this CPU test.
    from src.tests.test_m68k_simulator_arithmetic import State,Trace,engine
    contract=direct(((128,address,4),))
    source=tmp_path/'seed.s';binary=tmp_path/'seed.bin'
    source.write_text('    ORG $1000\n'+adapter.seed_copy_source(contract,512)+'    rts\n')
    root=Path(__file__).resolve().parents[1]
    subprocess.run([str(root/'tools/vasmm68k_mot.exe'),'-Fbin','-m68000','-no-opt','-o',str(binary),str(source)],
                   check=True,capture_output=True)
    memory=bytearray(b'\xA5'*0x100000);code=binary.read_bytes();memory[0x1000:0x1000+len(code)]=code
    memory[0x20080:0x20084]=bytes.fromhex('a0004000');memory[0x9000:0x9004]=(0x800).to_bytes(4,'big')
    before=bytes(memory)
    state=State();state.pc=0x1000;state.sr=0x2000;state.a[7]=0x9000
    trace=Trace();buffer=(C.c_uint8*len(memory)).from_buffer(memory)
    rc=engine()(0,buffer,len(memory),C.byref(state),128,0x800,0x802,None,C.byref(trace))
    assert rc==0 and trace.stop_reason==1 and not trace.overflow
    assert memory[address:address+4]==bytes.fromhex('a0004000')
    assert memory[:address]==before[:address] and memory[address+4:]==before[address+4:]
    assert state.a[0]==0x20084 and state.a[1]==address+4

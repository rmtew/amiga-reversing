"""Guest cleanup is observed at its verified label, not a guessed frame delay."""
import hashlib
from pathlib import Path
import pytest

from amiga_reversing.tools.runtime_allocation import abort_guest
from tests.test_runtime_allocation_boot import native_contract
from amiga_reversing.tools.direct_payload_adapter import build_boot_adf,reservation_plan


@pytest.mark.parametrize('cpu,retained,partial',[(False,None,False),(True,None,False),(False,4,False),(False,8,False),(True,24,False),(True,24,True)])
def test_unwind_waits_for_assembled_label_after_ROM_preemption(tmp_path,monkeypatch,cpu,retained,partial):
    if cpu:
        from tests.test_CPU_allocation_boot import contract_fixture
        contract,payload,_=contract_fixture(tmp_path,prior=4096)
    else:contract,payload=native_contract(tmp_path)
    build=build_boot_adf(contract,payload,tmp_path/'probe.adf')
    base=0x1600;marker=contract.handoff_marker_address
    spans=reservation_plan(contract,payload.stat().st_size)
    acquired=spans.index((marker-0xf8,0xf0))+1 if partial else len(spans)
    code=Path(build['floppy0']).read_bytes()[12:12+build['allocation_boot_code_size']]
    sequence=[]
    class Client:
        done=False
        def read_memory(self,address,size):
            if address==marker-4:return acquired.to_bytes(4,'big')
            if address==marker-8:return base.to_bytes(4,'big')
            if address==marker-0xf8:
                record=bytearray(size);record[:4]=b'ALLO'
                if retained is not None:record[retained:retained+4]=(0x6080).to_bytes(4,'big')
                return bytes(record)
            assert address==base and size==len(code)
            return code
        def request(self,method,params=None):
            sequence.append((method,params))
            assert method in ('mem.write','reverse_anchor')
        def registers(self):
            assert self.done,'An in-progress ROM frame is not completion'
            return dict(d3=int.from_bytes(b'FREE','big'),pc=base+build['allocation_boot_symbols']['allocation_closed'])
    client=Client()
    monkeypatch.setattr('amiga_reversing.tools.copperline_runtime.wait_for_marker',lambda *args,**kwargs:dict(matched=True))
    def completion(c,address,seconds):
        assert address==base+build['allocation_boot_symbols']['allocation_closed']
        assert sequence[-2][1]['data']==b'FREE'.hex()
        c.done=True
        return dict(status='hit',address=address)
    monkeypatch.setattr('amiga_reversing.tools.copperline_runtime.wait_for_pc',completion)
    if retained is not None and not partial:
        with pytest.raises(ValueError,match='retained an owned lease'):
            abort_guest(client,contract,build,already_aborted=True)
        assert not sequence
        return
    result=abort_guest(client,contract,build,already_aborted=True)
    assert result['status']=='guest_unwind_complete_diagnostic_hold_not_OS_return'

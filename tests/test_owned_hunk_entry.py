"""A cached file prefix must not be mistaken for the executed CODE HUNK."""
import pytest
from amiga_reversing.tools.pandora_OS_application import observe_owned_hunk_entry


class Client:
    def __init__(self,*,bad_tail=False):
        self.code=bytes(range(64));self.cache=0xc01000;self.actual=0xc02000
        ram=bytearray(0x80000)
        for base in (self.cache,self.actual):ram[base-0xc00000:base-0xc00000+64]=self.code
        if bad_tail:ram[self.actual-0xc00000+48]^=1
        self.ram=bytes(ram);self.pc=0;self.bp={};self.removed=[];self.calls=0
    def run_until(self,target,timeout):
        self.calls+=1
        if self.calls==1:return dict(reason='target',frame=target['frame'])
        self.pc=self.actual+8;return dict(reason='breakpoint',frame=target['frame'])
    def registers(self):return dict(pc=self.pc)
    def read_memory(self,address,size):
        offset=address-0xc00000;return self.ram[offset:offset+size]
    def add_breakpoint(self,address):
        result=len(self.bp)+1;self.bp[result]=address;return result
    def remove_breakpoint(self,number):self.removed.append(number)


@pytest.mark.parametrize('bad_tail',[False,True])
def test_executed_candidate_wins_and_immutable_tables_are_checked(bad_tail):
    c=Client(bad_tail=bad_tail)
    labels=dict(pre_entry_ready=8,immutable_code_end=32,immutable_tables_start=48)
    if bad_tail:
        with pytest.raises(ValueError,match='tables differ'):observe_owned_hunk_entry(c,c.code,labels)
    else:
        base,ready,stop=observe_owned_hunk_entry(c,c.code,labels)
        assert base==c.actual and c.bp[ready]==c.actual+8 and stop['reason']=='breakpoint'
        assert c.bp[c.removed[0]]==c.cache+8 and ready not in c.removed

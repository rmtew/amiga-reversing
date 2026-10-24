"""Bounded proposed address-form semantics; no natural gameplay claim."""
from pathlib import Path
import subprocess

import machine68k
import pytest

from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend
from amiga_reversing.tools.direct_payload_adapter import VASM
from amiga_reversing.tools.pandora_layout_walkthrough import TARGET
from amiga_reversing.disasm.project_paths import resolve_project_paths


@pytest.mark.parametrize('site,value',[(0x78c4,0x1e928),(0x79f2,0x24c28),
    (0x9f38,0x24c28),(0x4b0ce,0x1e928)])
def test_original_and_proposed_frame_store_have_same_effects_and_oracle_cycles(tmp_path,site,value):
    original=resolve_project_paths(TARGET).target_dir.joinpath('binary.bin').read_bytes()[site:site+8]
    codes=[]
    for index,dest in enumerate(['$64c0.w','$2ac4(a6)']):
        text=f' SECTION code,code\n org $1000\n move.l #${value:x},{dest}\n'
        code,_=assemble_platform_source_text_with_c_backend('amiga-raw',text)
        src=tmp_path/f'form{index}.s';binary=tmp_path/f'form{index}.bin';src.write_text(text)
        result=subprocess.run([str(VASM),'-quiet','-Fbin','-m68000','-no-opt','-o',str(binary),str(src)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert code==binary.read_bytes() and len(code)==8
        codes.append(code)
    assert codes[0]==original
    for app in [0x39fc,0x6080,0x7080,0x10000]:
        for ccr in range(32):
            observations=[]
            for index,code in enumerate(codes):
                target=0x64c0 if index==0 else app+0x2ac4
                m=machine68k.Machine(machine68k.CPUType.M68000,128)
                m.mem.w_block(0x1000,code+b'\x4e\x71'*2)
                m.mem.w_block(target-4,b'\xa5'*12)
                for n in range(8):
                    m.cpu.w_reg(getattr(machine68k.Register,f'D{n}'),0x12340000+n)
                    m.cpu.w_reg(getattr(machine68k.Register,f'A{n}'),0x9000+n*4)
                m.cpu.w_reg(machine68k.Register.A6,app);m.cpu.w_sr(0x2700|ccr);m.cpu.w_pc(0x1000)
                bus=[];m.mem.set_trace_func(lambda *args:bus.append(args));m.mem.set_trace_mode(True)
                result=m.cpu.execute(1)
                # The callback is a coarse operand-access trace, not CCK slots.
                m.mem.set_trace_mode(False)
                assert m.mem.r_block(target-4,12)==b'\xa5'*4+value.to_bytes(4,'big')+b'\xa5'*4
                assert m.cpu.r_pc()==0x1008
                assert m.cpu.r_sr()==(0x2700|(ccr&0x10))
                assert [m.cpu.r_reg(getattr(machine68k.Register,f'D{n}')) for n in range(8)]==[0x12340000+n for n in range(8)]
                assert [m.cpu.r_reg(getattr(machine68k.Register,f'A{n}')) for n in range(8)]==[0x9000+n*4 if n!=6 else app for n in range(8)]
                assert [(x[0],x[1]) for x in bus]==[('R',1),('R',2),('R',1),('W',2)]
                assert bus[-1][2:]==(target,value)
                observations.append(result.cycles)
            assert observations==[24,24]

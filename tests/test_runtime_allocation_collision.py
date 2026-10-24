"""Execute the real guest collision/unwind includes against bounded Exec stubs.

This is a loader-only two-collision refusal, not gameplay or an Exec allocator
implementation. The oracle observes the exact FreeMem arguments at each call.
"""
import subprocess
from pathlib import Path

import machine68k

from amiga_reversing.tools.direct_payload_adapter import VASM

ROOT=Path(__file__).resolve().parents[1]


def test_second_collision_preserves_first_scratch_lease_size(tmp_path):
    (tmp_path/'direct_payload_allocation_exclusions.i').write_text('''
    move.l #$5000,d6
    cmpi.l #$2000,d2
    bne.b second_collision
    move.l #$3000,d6
second_collision:
    bra.w allocation_collision
''')
    (tmp_path/'direct_payload_allocation_static_unwind.i').write_text('')
    source=tmp_path/'collision.s'
    source.write_text('''
    org $1000
ALLOCATION_RECORD equ $9000
HANDOFF_MARKER equ $9100
ALLOCATION_SIZE equ $100
ALLOCATION_SCRATCH_EXTRA equ 0
ALLOCATION_STATIC_READY equ 1
ALLOCATION_RECORD_OWNED equ 2
_LVOAllocMem equ -198
_LVOFreeMem equ -210
    include "amiga_runtime_allocation.i"
    bra.w failed
failed:
    include "amiga_runtime_allocation_unwind.i"
''')
    # exec/memory.i supplies flags; use the same include roots as the builder.
    from amiga_reversing.tools.direct_payload_adapter import NDK_INCLUDE
    binary=tmp_path/'collision.bin'
    result=subprocess.run([str(VASM),'-Fbin','-m68000','-no-opt','-I'+str(ROOT/'tools'),
                           '-I'+str(NDK_INCLUDE),'-I'+str(tmp_path),'-o',str(binary),str(source)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    machine=machine68k.Machine(machine68k.CPUType.M68000,128)
    machine.mem.w_block(0x1000,binary.read_bytes())
    for address in (0x7000-198,0x7000-210):machine.mem.w_block(address,b'\x4e\x75')
    machine.cpu.w_reg(machine68k.Register.A6,0x7000)
    machine.cpu.w_reg(machine68k.Register.A7,0x1f000)
    machine.cpu.w_reg(machine68k.Register.D4,1)
    machine.cpu.w_sr(0x2700);machine.cpu.w_pc(0x1000)
    returns=iter((0x2000,0x2000,0x3800));allocated=[];freed=[];steps=0
    class Refused(Exception):pass
    def hook(pc):
        nonlocal steps
        steps+=1
        assert steps<300,'Unbounded loader execution'
        if machine.mem.r_block(0x9100,4)==b'ABOR':raise Refused
        if pc==0x7000-198:
            allocated.append(machine.cpu.r_reg(machine68k.Register.D0))
            machine.cpu.w_reg(machine68k.Register.D0,next(returns))
        elif pc==0x7000-210:
            freed.append((machine.cpu.r_reg(machine68k.Register.A1),machine.cpu.r_reg(machine68k.Register.D0)))
    machine.cpu.set_instr_hook_callback(hook)
    try:machine.cpu.execute(100000)
    except Refused:pass
    else:raise AssertionError('Second collision did not refuse')
    assert allocated==[0x100,0x1000,0x100]
    assert freed==[(0x2000,0x100),(0x3800,0x100),(0x2000,0x1000)]
    assert machine.mem.r_block(0x9004,8)==bytes(8),'Owner and scratch must both be released'

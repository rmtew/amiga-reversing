"""MOVEM uses shared EA formulas; only auto-update needs a bound An."""
import ctypes

import pytest

from tests.test_memory_frame_arithmetic import assemble_arithmetic, ConcreteState, ConcreteResult
from src.tests.test_m68k_simulator_abstract import _disasm_library, _diag_has_errors, _diag_message, M68kSimCpuState, _const


@pytest.mark.parametrize('width',[2,4])
@pytest.mark.parametrize('ea',['$200.w','$200.l','12(a3)','0(a3,d5.w)','table(pc)','table(pc,d5.w)'])
def test_concrete_movem_loads_all_registers_without_spurious_address_register_requirement(tmp_path,width,ea):
    suffix='w'if width==2 else'l'
    code=assemble_arithmetic(tmp_path,f'movem.{suffix} {ea},d0/d2/a1\n rts\ntable: dc.l 0,0,0')
    table=len(code)-12
    memory=(ctypes.c_uint8*0x4000)()
    cpu=ConcreteState();cpu.pc=0x1000;cpu.sr=0x271F
    cpu.d[:]=[0x11220000+i for i in range(8)];cpu.a[:]=[0x33440000+i for i in range(8)]
    cpu.a[3]=0x1F4 if ea.startswith('12')else 0x200
    cpu.d[5]=0
    address=0x1000+table if ea.startswith('table')else 0x200
    values=[0x8001,0x7FFF,0xFFFF]if width==2 else[0x80012345,0x7FFFFFFF,0xFFFFFFFF]
    for i,v in enumerate(values):memory[address+width*i:address+width*(i+1)]=v.to_bytes(width,'big')
    before_d=list(cpu.d);before_a=list(cpu.a);before=bytes(memory)
    buf=(ctypes.c_uint8*len(code)).from_buffer_copy(code)
    step=_disasm_library().m68k_simulate_one_concrete_for_cpu
    step.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_uint8,
                   ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ConcreteState)]
    step.restype=ConcreteResult
    result=step(buf,len(code),0,memory,len(memory),ctypes.byref(cpu))
    assert not _diag_has_errors(result.diagnostics),_diag_message(result.diagnostics)
    expected=[v|0xFFFF0000 if width==2 and v&32768 else v for v in values]
    before_d[0],before_d[2],before_a[1]=expected
    assert list(cpu.d)==before_d and list(cpu.a)==before_a
    assert bytes(memory)==before and cpu.sr==0x271F and cpu.pc==0x1000+table-2


@pytest.mark.parametrize('width',[2,4])
@pytest.mark.parametrize('ea',['$200.w','$200.l','12(a3)','0(a3,d5.w)'])
def test_concrete_movem_stores_full_list_to_nonupdating_eas(tmp_path,width,ea):
    code=assemble_arithmetic(tmp_path,f'movem.{"w"if width==2 else"l"} d0/d2/a1,{ea}')
    memory=(ctypes.c_uint8*0x1000).from_buffer_copy(b'\xA5'*0x1000)
    cpu=ConcreteState();cpu.pc=0x1000;cpu.sr=0x271F
    cpu.d[:]=[0x11223300+i for i in range(8)];cpu.a[:]=[0x33445500+i for i in range(8)]
    cpu.a[3]=0x1F4 if ea.startswith('12')else 0x200;cpu.d[5]=0
    before_d=list(cpu.d);before_a=list(cpu.a);expected=bytearray(memory)
    expected[0x200:0x200+3*width]=b''.join((v&((1<<(8*width))-1)).to_bytes(width,'big')for v in [cpu.d[0],cpu.d[2],cpu.a[1]])
    buf=(ctypes.c_uint8*len(code)).from_buffer_copy(code)
    step=_disasm_library().m68k_simulate_one_concrete_for_cpu
    step.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_uint8,
                   ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ConcreteState)]
    step.restype=ConcreteResult
    result=step(buf,len(code),0,memory,len(memory),ctypes.byref(cpu))
    assert not _diag_has_errors(result.diagnostics),_diag_message(result.diagnostics)
    assert bytes(memory)==expected and list(cpu.d)==before_d and list(cpu.a)==before_a
    assert cpu.sr==0x271F and cpu.pc==0x1000+len(code)


@pytest.mark.parametrize('indexed',[False,True])
def test_abstract_pc_relative_movem_reads_section_data_without_a_base_register(tmp_path,indexed):
    code=assemble_arithmetic(tmp_path,'movem.w table(pc'+(',d5.w'if indexed else'')+'),d0/d2/a1\n rts\ntable: dc.w $8001,$7FFF,$FFFF')
    buf=(ctypes.c_uint8*len(code)).from_buffer_copy(code)
    cpu=M68kSimCpuState();cpu.d[5]=_const(0);cpu.sr=0x271F
    outcome=_disasm_library().m68k_simulate_one_abstract_for_cpu(buf,len(code),0,ctypes.byref(cpu))
    assert not _diag_has_errors(outcome.diagnostics),_diag_message(outcome.diagnostics)
    values=[outcome.step.next_state.d[0],outcome.step.next_state.d[2],outcome.step.next_state.a[1]]
    assert [(v.kind,v.value)for v in values]==[(1,0xFFFF8001),(1,0x7FFF),(1,0xFFFFFFFF)]
    assert outcome.step.next_state.sr==cpu.sr


@pytest.mark.parametrize('ea',['table(pc,d5.w)','(a3)','(a3)+'])
def test_unknown_ea_cannot_reuse_old_destination_register_values(tmp_path,ea):
    code=assemble_arithmetic(tmp_path,f'movem.l {ea},d0/d2/a1\n rts\ntable: dc.l 1,2,3')
    buf=(ctypes.c_uint8*len(code)).from_buffer_copy(code)
    cpu=M68kSimCpuState();cpu.d[0]=_const(44);cpu.d[2]=_const(55);cpu.a[1]=_const(66)
    outcome=_disasm_library().m68k_simulate_one_abstract_for_cpu(buf,len(code),0,ctypes.byref(cpu))
    assert not _diag_has_errors(outcome.diagnostics),_diag_message(outcome.diagnostics)
    assert [outcome.step.next_state.d[0].kind,outcome.step.next_state.d[2].kind,outcome.step.next_state.a[1].kind]==[0,0,0]


@pytest.mark.parametrize('instruction',['movem.l d0/d2,-(a3)','movem.l (a3)+,d0/d2'])
def test_unmapped_auto_update_base_cannot_remain_at_old_constant(tmp_path,instruction):
    code=assemble_arithmetic(tmp_path,instruction)
    buf=(ctypes.c_uint8*len(code)).from_buffer_copy(code)
    cpu=M68kSimCpuState();cpu.a[3]=_const(0x20000)
    outcome=_disasm_library().m68k_simulate_one_abstract_for_cpu(buf,len(code),0,ctypes.byref(cpu))
    assert not _diag_has_errors(outcome.diagnostics),_diag_message(outcome.diagnostics)
    assert outcome.step.next_state.a[3].kind==0


@pytest.mark.parametrize('instruction', ['btst.b #3,table(pc)','btst.b d0,table(pc)'])
def test_pc_base_layout_handles_both_prefixed_and_unprefixed_scalar_readers(tmp_path,instruction):
    code=assemble_arithmetic(tmp_path,instruction+'\n rts\ntable: dc.w $0800')
    buf=(ctypes.c_uint8*len(code)).from_buffer_copy(code)
    memory=(ctypes.c_uint8*0x2000)()
    table=0x1000+len(code)-2
    memory[table]=8
    cpu=ConcreteState();cpu.pc=0x1000;cpu.d[0]=3;cpu.sr=0x271F
    step=_disasm_library().m68k_simulate_one_concrete_for_cpu
    step.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_uint8,
                   ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.POINTER(ConcreteState)]
    step.restype=ConcreteResult
    result=step(buf,len(code),0,memory,len(memory),ctypes.byref(cpu))
    assert not _diag_has_errors(result.diagnostics),_diag_message(result.diagnostics)
    assert cpu.sr==0x271B and cpu.d[0]==3

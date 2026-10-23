"""Symbol rewriting must retain generated special-register operand identities."""
import subprocess

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


@pytest.mark.parametrize('mnemonic,register,value', [
    ('move', 'sr', 0x2700), ('move', 'ccr', 1),
    ('ori', 'sr', 0x2000), ('ori', 'ccr', 1),
    ('andi', 'sr', 0xDFFF), ('andi', 'ccr', 0xFE),
    ('eori', 'sr', 0x2000), ('eori', 'ccr', 1),
])
@pytest.mark.parametrize('forward', [False, True])
def test_symbolic_status_immediate_matches_numeric_and_independent_vasm(tmp_path, mnemonic, register, value, forward):
    declaration = f'status_value EQU ${value:X}\n'
    body = f' SECTION code,code\n ORG 0\n {mnemonic} #status_value,{register.upper()}\n rts\n'
    source = body+declaration if forward else declaration+body
    actual, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', source, project_root=PROJECT_ROOT)
    expected, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',
        body.replace('status_value', f'${value:X}'), project_root=PROJECT_ROOT)
    assert actual == expected
    path, output = tmp_path/'status.s', tmp_path/'oracle.bin'
    path.write_text(source)
    result = subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'), '-quiet', '-Fbin', '-o', str(output), str(path)],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
    assert actual == output.read_bytes()

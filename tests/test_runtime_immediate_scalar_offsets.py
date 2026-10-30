"""An address-valued destination does not make its arithmetic addend a pointer."""
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from tests.test_app_cursor_propagation import cursor_artifact


def _round_trip(tmp_path, text, original):
    assert c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)[0] == original
    asm, out = tmp_path/'source.s', tmp_path/'out.bin'
    asm.write_text(text)
    vasm = Path(__file__).resolve().parents[1]/'tools/vasmm68k_mot.exe'
    subprocess.run([str(vasm), '-quiet', '-Fbin', '-m68000', '-no-opt',
                    '-o', str(out), str(asm)], check=True, capture_output=True, text=True)
    assert out.read_bytes() == original


def body(operation, dest):
    instruction = f'{operation} #$1010,{dest}'
    encoded = c_backend.assemble_platform_source_text_with_c_backend(
        'amiga-raw', ' SECTION code,code\n ORG $1000\n '+instruction+'\n')[0]
    padding = 16-len(encoded)-2
    assert padding >= 0
    return f'{instruction}\n bra.b function\n dcb.b {padding},0\nfunction:\n rts'


@pytest.mark.parametrize('operation,dest', [
    ('adda.w', 'a4'), ('adda.l', 'a4'), ('suba.w', 'a4'), ('suba.l', 'a4'),
    ('addi.l', 'd4'), ('subi.l', '(a4)'), ('addi.l', '(a4)'),
    ('ori.l', '(a4)'), ('andi.l', '(a4)'),
])
def test_untyped_arithmetic_coincidence_does_not_name_a_code_address(tmp_path, operation, dest):
    text = body(operation, dest)
    artifact, original = cursor_artifact(tmp_path, text, regions=False, metadata_extra=dict(
        seeded_code_labels=[dict(hunk=0, addr=16, name='real_code_entry')]))
    try:
        rendered = artifact.inline_source_text_with_profile()[0]
        line, = [line for line in rendered.splitlines() if line.startswith('\t'+operation+' ')]
        assert '#real_code_entry' not in line
        assert 'real_code_entry:' in rendered
        _round_trip(tmp_path, rendered, original)
    finally:
        artifact.close()


@pytest.mark.parametrize('operation,dest', [('movea.l', 'a4'), ('movea.w', 'a4'), ('move.l', '(a4)'),
                                         ('cmpa.w', 'a4'), ('cmpa.l', 'a4')])
def test_supported_address_assignment_retains_its_existing_symbol(tmp_path, operation, dest):
    artifact, original = cursor_artifact(tmp_path, body(operation, dest), regions=False, metadata_extra=dict(
        seeded_code_labels=[dict(hunk=0, addr=16, name='real_code_entry')]))
    try:
        rendered = artifact.inline_source_text_with_profile()[0]
        assert '#real_code_entry,' in rendered
        _round_trip(tmp_path, rendered, original)
    finally:
        artifact.close()

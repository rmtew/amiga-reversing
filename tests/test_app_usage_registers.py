"""The app closure consumes native register facts, never rendered operands."""
from pathlib import Path
import pytest
from amiga_reversing.disasm.app_access_audit import AuditIncomplete, decode_retained_instruction, explicit_register_writes
from amiga_reversing.disasm.c_backend import assemble_platform_source_text_with_c_backend

ROOT = Path(__file__).resolve().parents[1]


def evidence(asm):
    code, _ = assemble_platform_source_text_with_c_backend('amiga-raw', ' SECTION code,code\n ORG 0\n '+asm+'\n')
    return decode_retained_instruction(code, project_root=ROOT)


@pytest.mark.parametrize('asm, expected', [
    ('lea.l $39fc.l,a6', ['A6']),
    ('move.w d0,$190(a6)', []),
    ('move.l (a7)+,a6', ['A6','A7']),
    ('move.l (a6)+,d0', ['A6','D0']),
    ('movem.l (a7)+,d0-d1/a0-a7', ['A0','A1','A2','A3','A4','A5','A6','A7','D0','D1']),
    ('movem.l d0-d1/a0-a7,-(a7)', ['A7']),
])
def test_native_register_effects_include_ranges_and_address_updates(asm, expected):
    assert explicit_register_writes(evidence(asm)) == expected


def test_exact_one_instruction_refuses_trailing_or_truncated_bytes():
    for code in [b'', b'\x4e', bytes.fromhex('4e754e75')]:
        with pytest.raises(AuditIncomplete):
            decode_retained_instruction(code, project_root=ROOT)


def test_missing_semantics_refuses_register_closure():
    with pytest.raises(AuditIncomplete, match='semantics missing'):
        explicit_register_writes(dict(metadata_available=False))

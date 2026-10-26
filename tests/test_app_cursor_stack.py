"""App cursor stack transfers preserve full values, never partial saves."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact, derived_refs

@pytest.mark.parametrize('registers', ['a4-a5', 'd0/a4-a5'])
def test_long_movem_restores_app_cursor(tmp_path, registers):
    body = f'''lea.l $BC6(a6),a4
 lea.l $78(a4),a5
 movem.l {registers},-(a7)
 movea.l #0,a4
 movea.l #0,a5
 movem.l (a7)+,{registers}
 move.w (a5),d0'''
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        reads = [r for r in derived_refs(artifact) if r['access'] == 'read']
        assert [r['displacement'] for r in reads] == [0xC3E]
        assert reads[0]['base_evidence'] == 'a6_fallback'
    finally:
        artifact.close()

@pytest.mark.parametrize('middle,size', [
    ('', 'w'),
    ('move.l #0,4(a7)', 'l'),
    ('adda.l d0,a7', 'l'),
    ('move.b #0,5(a7)', 'l'),
    ('move.w #0,6(a7)', 'l'),
])
def test_incomplete_or_clobbered_save_does_not_restore_cursor(tmp_path, middle, size):
    body = f'''lea.l $BC6(a6),a4
 lea.l $78(a4),a5
 movem.{size} a4-a5,-(a7)
 movea.l #0,a4
 movea.l #0,a5
 {middle}
 movem.{size} (a7)+,a4-a5
 move.w (a5),d0'''
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] == 'read']
    finally:
        artifact.close()


def test_stack_pointer_in_save_mask_is_not_a_cursor_frame(tmp_path):
    body = """lea.l $BC6(a6),a4
 lea.l $78(a4),a5
 movem.l a4-a5/a7,-(a7)
 movea.l #0,a4
 movea.l #0,a5
 movem.l (a7)+,a4-a5/a7
 move.w (a5),d0"""
    artifact, _ = cursor_artifact(tmp_path, body)
    try:
        assert not [r for r in derived_refs(artifact) if r['access'] == 'read']
    finally:
        artifact.close()

"""A conflict describes known incompatible inputs, not a stronger must fact."""
from itertools import permutations

import pytest

from tests.test_app_cursor_propagation import cursor_artifact
from tests.test_custom_prefix_join import metadata


@pytest.mark.parametrize('inputs', list(permutations(['left', 'right', 'unknown'])))
def test_real_unknown_absorbs_type_conflict_in_every_predecessor_order(tmp_path, inputs):
    loads = dict(left='movea.l a1,a0', right='movea.l a2,a0', unknown='movea.l d6,a0')
    artifact, _ = cursor_artifact(tmp_path, f'''tst.w d7
 beq.w first
 tst.w d5
 beq.w second
 {loads[inputs[2]]}
 bra.w joined
first:
 {loads[inputs[0]]}
 bra.w joined
second:
 {loads[inputs[1]]}
joined:
 move.l 12(a0),d0''', regions=False, metadata_extra=metadata(right='Other'))
    try:
        analysis = artifact.analysis_payload()[0]
        assert not analysis['incomplete_analysis']
        section = analysis['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert not [r for r in section['recovered_platform_unresolved_typed_accesses']
                    if r['classification'] == 'type_conflict']
    finally:
        artifact.close()


def test_incompatible_known_inputs_still_report_their_conflict(tmp_path):
    artifact, _ = cursor_artifact(tmp_path, '''tst.w d7
 beq.w other
 movea.l a1,a0
 bra.w joined
other:
 movea.l a2,a0
joined:
 move.l 12(a0),d0''', regions=False, metadata_extra=metadata(right='Other'))
    try:
        section = artifact.analysis_payload()[0]['sections'][0]
        assert not section['recovered_platform_typed_accesses']
        assert any(r['classification'] == 'type_conflict'
                   for r in section['recovered_platform_unresolved_typed_accesses'])
    finally:
        artifact.close()

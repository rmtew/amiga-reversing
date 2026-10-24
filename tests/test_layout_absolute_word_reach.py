"""Fresh and reused source refuse typed RAM addresses lost by W truncation."""
import copy

import pytest

from tests.test_bootstrap_layouts import build
from tests.test_runtime_CPU_allocation_plan import fixture


@pytest.mark.parametrize('address,refused',[(0x6000,False),(0x7ff0,False),
    (0x7ff4,True),(0x8000,True)])
def test_fresh_and_frozen_layout_word_reach_match(tmp_path,address,refused):
    a=fixture(tmp_path)
    try:
        import json
        m=json.loads((tmp_path/'metadata.json').read_text())
        m['memory_layouts'][0]['placements'][-1]['runtime_address']=address
        overlay=dict(memory_layouts=copy.deepcopy(m['memory_layouts']),selected_memory_layout_id='diagnostic')
        result=a.layout_projection_payload(overlay)
        original=(tmp_path/'cpu.bin').read_bytes();original+=bytes(512-len(original))
        if refused:
            assert result['status']=='refused',result
            assert result['reason']=='absolute_word_layout_overflow'
            assert 'package' not in result
            with pytest.raises(RuntimeError,match='absolute_word_layout_overflow'):
                build(tmp_path,m,original)
        else:
            assert result['status']=='ok',result
            fresh=build(tmp_path,m,original)
            try:assert fresh.inline_source_text_with_profile()[0]==result['canonical_source_text']
            finally:fresh.close()
        assert a.runtime_allocation_plan('cpu','diagnostic')['status']=='bounded_allocation_candidate'
    finally:a.close()

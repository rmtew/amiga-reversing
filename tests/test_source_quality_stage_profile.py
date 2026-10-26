"""Optional native stage tracing must not change recovered facts."""
import json

import pytest

from amiga_reversing.disasm import c_backend
from tests.test_c_backend import _requires_c_backend_dlls

pytestmark = pytest.mark.c_backend


def test_source_quality_stage_trace_preserves_analysis(tmp_path, monkeypatch, capfd):
    _requires_c_backend_dlls()
    binary = tmp_path / 'profile.raw'
    binary.write_bytes(bytes.fromhex('4e75') + b'STAGE PROFILE\0')

    def analyze():
        payload = json.loads(c_backend._platform_file_text(
            'platform_file_facts_v2_analysis_raw_path_json_alloc',
            'amiga-raw', str(binary), 0, 0, 0, '', '',
            project_root=c_backend.PROJECT_ROOT))
        payload.pop('profile', None)
        return payload

    monkeypatch.delenv('AMIGA_REVERSING_PROFILE_SOURCE_QUALITY', raising=False)
    original = analyze()
    assert 'source_quality_stage ' not in capfd.readouterr().err
    monkeypatch.setenv('AMIGA_REVERSING_PROFILE_SOURCE_QUALITY', '1')
    observed = analyze()
    trace = capfd.readouterr().err
    assert observed == original
    assert 'source_quality_stage append_generic_string_items ' in trace
    assert 'source_quality_total ' in trace

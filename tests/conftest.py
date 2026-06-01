from __future__ import annotations

from pathlib import Path

import pytest

_C_BACKEND_FILES = {
    "test_c_backend.py",
}

_CODEGEN_DRIFT_TEST_NAMES = {
    "test_diagnostic_inventory_loads_current_generated_form_tables",
    "test_canonical_inventory_summarizes_current_generated_data",
    "test_diagnostic_check_command_succeeds_with_current_classified_data",
    "test_canonical_check_command_prints_canonical_summaries",
    "test_bootstrap_unsupported_inventory_classifies_current_families",
    "test_generated_mac_os_runtime_metadata_is_current",
}

_ROUTE_INTEGRATION_FILES = {
    "test_api_workflow_harness.py",
}

_MACOS_REAL_FIXTURE_FILES = {
    "test_macos_asm_container.py",
    "test_macos_container_payload.py",
    "test_macos_web_view.py",
}

_REAL_INTEGRATION_NAME_PREFIXES = (
    "test_real_dll_",
    "test_agent_real_",
)

_REAL_INTEGRATION_NAME_FRAGMENTS = (
    "real_asm",
    "committed_macos",
    "committed_mpw",
    "macos_listing_source_sits",
    "macos_listing_artifact_uses_macos_source",
    "code1_main_is_decodable_by_existing_m68k_listing_backend",
    "c_macos_hfs_code_summary_matches_committed_mpw_asm_metadata",
)

_REAL_INTEGRATION_FILES = {
    "test_full_reproduction_integration.py",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    integration = pytest.mark.integration
    c_backend = pytest.mark.c_backend
    codegen_drift = pytest.mark.codegen_drift
    route_integration = pytest.mark.route_integration
    macos_real_fixture = pytest.mark.macos_real_fixture
    real_integration = pytest.mark.real_integration
    web_e2e = pytest.mark.web_e2e
    for item in items:
        test_name = item.name
        file_name = Path(str(item.fspath)).name
        is_real_integration = (
            file_name in _REAL_INTEGRATION_FILES
            or test_name.startswith(_REAL_INTEGRATION_NAME_PREFIXES)
            or any(fragment in test_name for fragment in _REAL_INTEGRATION_NAME_FRAGMENTS)
        )
        layer_markers = []
        standalone_markers = []
        if file_name in _C_BACKEND_FILES:
            layer_markers.append(c_backend)
        if test_name in _CODEGEN_DRIFT_TEST_NAMES:
            layer_markers.append(codegen_drift)
        if file_name in _ROUTE_INTEGRATION_FILES:
            layer_markers.append(route_integration)
        if file_name in _MACOS_REAL_FIXTURE_FILES:
            layer_markers.append(macos_real_fixture)
        if file_name == "test_web_e2e_cdp.py":
            standalone_markers.append(web_e2e)
        if file_name == "test_disasm_server.py" and test_name.startswith(
            ("test_route_", "test_installed_disasm_server_")
        ):
            layer_markers.append(route_integration)
        if is_real_integration:
            layer_markers.append(real_integration)
        for marker in layer_markers:
            item.add_marker(marker)
        for marker in standalone_markers:
            item.add_marker(marker)
        if layer_markers and not is_real_integration:
            item.add_marker(integration)

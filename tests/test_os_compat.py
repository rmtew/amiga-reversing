from disasm.os_compat import normalize_compatibility_version


def test_normalize_compatibility_version_raises_to_next_supported_kb_level() -> None:
    assert normalize_compatibility_version("2.1", ("1.3", "2.0", "3.1", "3.5")) == "3.1"

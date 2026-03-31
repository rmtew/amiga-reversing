from __future__ import annotations

from types import SimpleNamespace

import pytest

from disasm.os_value_domains import resolve_value_domain_expression
from m68k_kb import runtime_os


def _test_constant(raw: str, value: int | None) -> runtime_os.OsConstant:
    return runtime_os.OsConstant(
        raw=raw,
        value=value,
        owner=runtime_os.OsIncludeOwner(
            kind="native_include",
            canonical_include_path="test/test.i",
            assembler_include_path="test/test.i",
            source_file="test/test.i",
        ),
    )


def test_resolve_value_domain_expression_matches_enum_exactly() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "dos.seek.mode": runtime_os.OsValueDomain(
                kind="enum",
                members=("OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"),
                zero_name=None,
                exact_match_policy="error",
                composition=None,
                remainder_policy=None,
            ),
        },
        CONSTANTS={
            "OFFSET_BEGINNING": _test_constant(raw="-1", value=-1),
            "OFFSET_CURRENT": _test_constant(raw="0", value=0),
            "OFFSET_END": _test_constant(raw="1", value=1),
        },
    )

    resolved = resolve_value_domain_expression(os_kb, "dos.seek.mode", -1)

    assert resolved is not None
    assert resolved.names == ("OFFSET_BEGINNING",)
    assert resolved.text == "OFFSET_BEGINNING"


def test_resolve_value_domain_expression_composes_flags() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "exec.allocmem.attributes": runtime_os.OsValueDomain(
                kind="flags",
                members=("MEMF_PUBLIC", "MEMF_CHIP", "MEMF_FAST"),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            ),
        },
        CONSTANTS={
            "MEMF_PUBLIC": _test_constant(raw="(1<<0)", value=0x1),
            "MEMF_CHIP": _test_constant(raw="(1<<1)", value=0x2),
            "MEMF_FAST": _test_constant(raw="(1<<2)", value=0x4),
        },
    )

    resolved = resolve_value_domain_expression(os_kb, "exec.allocmem.attributes", 0x3)

    assert resolved is not None
    assert resolved.names == ("MEMF_PUBLIC", "MEMF_CHIP")
    assert resolved.text == "MEMF_PUBLIC|MEMF_CHIP"


def test_resolve_value_domain_expression_rejects_unmatched_flag_bits() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "exec.signal_mask": runtime_os.OsValueDomain(
                kind="flags",
                members=("SIGBREAKF_CTRL_C",),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            ),
        },
        CONSTANTS={
            "SIGBREAKF_CTRL_C": _test_constant(raw="(1<<12)", value=0x1000),
        },
    )

    with pytest.raises(ValueError, match="No complete flag decomposition"):
        resolve_value_domain_expression(os_kb, "exec.signal_mask", 0x1001)


def test_resolve_value_domain_expression_treats_zero_flags_as_empty_set() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "exec.signal_mask": runtime_os.OsValueDomain(
                kind="flags",
                members=("SIGBREAKF_CTRL_C",),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            ),
        },
        CONSTANTS={
            "SIGBREAKF_CTRL_C": _test_constant(raw="(1<<12)", value=0x1000),
        },
    )

    assert resolve_value_domain_expression(os_kb, "exec.signal_mask", 0) is None


def test_resolve_value_domain_expression_uses_zero_name_when_declared() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "exec.signal_mask": runtime_os.OsValueDomain(
                kind="flags",
                members=("SIGBREAKF_CTRL_C",),
                zero_name="ZERO_SIGNAL_MASK",
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="error",
            ),
        },
        CONSTANTS={
            "SIGBREAKF_CTRL_C": _test_constant(raw="(1<<12)", value=0x1000),
            "ZERO_SIGNAL_MASK": _test_constant(raw="0", value=0),
        },
    )

    resolved = resolve_value_domain_expression(os_kb, "exec.signal_mask", 0)

    assert resolved is not None
    assert resolved.names == ("ZERO_SIGNAL_MASK",)
    assert resolved.text == "ZERO_SIGNAL_MASK"


def test_resolve_value_domain_expression_can_prefer_canonical_exact_alias() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "dos.seek.mode": runtime_os.OsValueDomain(
                kind="enum",
                members=("OFFSET_BEGINNING", "OFFSET_ALIAS"),
                zero_name=None,
                exact_match_policy="canonical_by_member_order",
                composition=None,
                remainder_policy=None,
            ),
        },
        CONSTANTS={
            "OFFSET_BEGINNING": _test_constant(raw="-1", value=-1),
            "OFFSET_ALIAS": _test_constant(raw="-1", value=-1),
        },
    )

    resolved = resolve_value_domain_expression(os_kb, "dos.seek.mode", -1)

    assert resolved is not None
    assert resolved.names == ("OFFSET_BEGINNING",)
    assert resolved.text == "OFFSET_BEGINNING"


def test_resolve_value_domain_expression_can_append_raw_remainder() -> None:
    os_kb = SimpleNamespace(
        VALUE_DOMAINS={
            "exec.signal_mask": runtime_os.OsValueDomain(
                kind="flags",
                members=("SIGBREAKF_CTRL_C",),
                zero_name=None,
                exact_match_policy="error",
                composition="bit_or",
                remainder_policy="append_hex",
            ),
        },
        CONSTANTS={
            "SIGBREAKF_CTRL_C": _test_constant(raw="(1<<12)", value=0x1000),
        },
    )

    resolved = resolve_value_domain_expression(os_kb, "exec.signal_mask", 0x1001)

    assert resolved is not None
    assert resolved.names == ("SIGBREAKF_CTRL_C",)
    assert resolved.raw_remainder == 0x1
    assert resolved.text == "SIGBREAKF_CTRL_C|$1"

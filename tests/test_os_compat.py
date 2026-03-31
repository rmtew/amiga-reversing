from types import SimpleNamespace

from disasm.os_compat import (
    build_emit_compatibility_report,
    normalize_compatibility_version,
)
from disasm.types import (
    BlockRowContext,
    ListingRow,
    SemanticOperand,
    StructFieldOperandMetadata,
)


def test_normalize_compatibility_version_raises_to_next_supported_kb_level() -> None:
    assert normalize_compatibility_version("2.1", ("1.3", "2.0", "3.1", "3.5")) == "3.1"


def test_build_emit_compatibility_report_lists_exact_dependencies() -> None:
    os_kb = SimpleNamespace(
        META=SimpleNamespace(
            compatibility_versions=("1.3", "2.0", "3.1"),
            include_min_versions={"exec/libraries.i": "1.3"},
        ),
        STRUCTS={
            "LIB": SimpleNamespace(
                available_since="1.3",
                fields=(
                    SimpleNamespace(name="LIB_FLAGS", available_since="2.0"),
                ),
            ),
        },
        LIBRARIES={
            "icon.library": SimpleNamespace(
                functions={
                    "GetDiskObjectNew": SimpleNamespace(available_since="2.0"),
                },
            ),
        },
    )
    session = SimpleNamespace(
        hunk_sessions=(
            SimpleNamespace(
                hunk_index=0,
                os_kb=os_kb,
                lib_calls=(
                    SimpleNamespace(
                        addr=0x1234,
                        library="icon.library",
                        function="GetDiskObjectNew",
                    ),
                ),
            ),
        ),
    )
    rows = [
        ListingRow(
            row_id="inc",
            kind="directive",
            text='    INCLUDE "exec/libraries.i"\n',
            opcode_or_directive="INCLUDE",
        ),
        ListingRow(
            row_id="inst",
            kind="instruction",
            text="    move.w LIB_FLAGS(a6),d0\n",
            addr=0x10,
            operand_parts=(
                SemanticOperand(
                    kind="operand",
                    text="LIB_FLAGS(a6)",
                    metadata=StructFieldOperandMetadata(
                        symbol="LIB_FLAGS(a6)",
                        owner_struct="LIB",
                        field_symbol="LIB_FLAGS",
                    ),
                ),
            ),
            source_context=BlockRowContext(kind="block", hunk_index=0, verified_state="verified"),
        ),
    ]

    report = build_emit_compatibility_report(session, rows=rows)

    assert report.floor == "2.0"
    deps = {(dep.kind, dep.symbol): dep for dep in report.dependencies}
    assert deps[("include", "exec/libraries.i")].required_since == "1.3"
    assert deps[("struct", "LIB")].required_since == "1.3"
    assert deps[("struct_field", "LIB.LIB_FLAGS")].required_since == "2.0"
    assert deps[("struct_field", "LIB.LIB_FLAGS")].usages == ("hunk 0 @ $0010",)
    assert deps[("library_call", "icon.library/GetDiskObjectNew")].required_since == "2.0"
    assert deps[("library_call", "icon.library/GetDiskObjectNew")].usages == ("hunk 0 @ $1234",)


def test_build_emit_compatibility_report_excludes_target_local_structs_and_self_library_calls() -> None:
    os_kb = SimpleNamespace(
        META=SimpleNamespace(
            compatibility_versions=("1.3", "2.0", "3.1"),
            include_min_versions={"exec/libraries.i": "1.3"},
        ),
        STRUCTS={
            "InferredIconLibraryBase": SimpleNamespace(
                source="target_metadata",
                available_since="2.0",
                fields=(SimpleNamespace(name="icon_library_base", available_since="2.0"),),
            ),
        },
        LIBRARIES={
            "icon.library": SimpleNamespace(
                functions={"iconPrivate1": SimpleNamespace(available_since="2.0")},
            ),
        },
    )
    session = SimpleNamespace(
        target_metadata=SimpleNamespace(
            library=SimpleNamespace(library_name="icon.library"),
            resident=None,
        ),
        hunk_sessions=(
            SimpleNamespace(
                hunk_index=0,
                os_kb=os_kb,
                lib_calls=(SimpleNamespace(addr=0x10, library="icon.library", function="iconPrivate1"),),
            ),
        ),
    )
    rows = [
        ListingRow(
            row_id="inc",
            kind="directive",
            text='    INCLUDE "exec/libraries.i"\n',
            opcode_or_directive="INCLUDE",
        ),
        ListingRow(
            row_id="inst",
            kind="instruction",
            text="    move.l icon_library_base(a2),d0\n",
            addr=0x20,
            operand_parts=(
                SemanticOperand(
                    kind="operand",
                    text="icon_library_base(a2)",
                    metadata=StructFieldOperandMetadata(
                        symbol="icon_library_base(a2)",
                        owner_struct="InferredIconLibraryBase",
                        field_symbol="icon_library_base",
                    ),
                ),
            ),
            source_context=BlockRowContext(kind="block", hunk_index=0, verified_state="verified"),
        ),
    ]

    report = build_emit_compatibility_report(session, rows=rows)

    assert report.floor == "1.3"
    assert len(report.dependencies) == 1
    assert report.dependencies[0].kind == "include"
    assert report.dependencies[0].symbol == "exec/libraries.i"

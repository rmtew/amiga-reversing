from pathlib import Path
from typing import cast

from kb.ndk_parser import (
    _map_clib_args_to_inputs,
    build_fd_function_min_versions,
    build_os_compatibility_kb,
    build_os_include_kb,
    canonicalize_json,
    collect_raw_constants_from_include_dir,
    evaluate_all_constants,
    parse_asm_include,
    parse_callback_typedefs,
    parse_clib_prototypes,
    parse_fd_file,
    parse_include_value_bindings,
    parse_synopsis,
    reconcile_clib_callback_types,
    scan_fd_function_names,
    scan_type_macros,
)
from kb.os_reference import (
    load_os_reference_payload,
    merge_os_reference_payloads,
)
from kb.paths import AMIGA_OS_REFERENCE_CORRECTIONS_JSON
from tests.runtime_kb_helpers import (
    load_canonical_os_kb_includes_parsed,
    load_canonical_os_kb_other_parsed,
)


def test_parse_clib_prototypes_preserves_function_pointer_args(
    tmp_path: Path,
) -> None:
    clib_dir = tmp_path / "clib"
    clib_dir.mkdir()
    (clib_dir / "exec_protos.h").write_text(
        "\n".join([
            "#ifndef CLIB_EXEC_PROTOS_H",
            "#define CLIB_EXEC_PROTOS_H",
            "ULONG Supervisor( unsigned long (*userFunction)() );",
            "APTR SetFunction( struct Library *library, long funcOffset,",
            "    unsigned long (*newFunction)() );",
            "#endif",
            "",
        ]),
        encoding="utf-8",
    )

    parsed = parse_clib_prototypes(str(tmp_path))

    assert parsed["exec"]["Supervisor"] == [
        {"name": "userFunction", "type": "unsigned long (*)()"},
    ]
    assert parsed["exec"]["SetFunction"] == [
        {"name": "library", "type": "struct Library *"},
        {"name": "funcOffset", "type": "long"},
        {"name": "newFunction", "type": "unsigned long (*)()"},
    ]


def test_parse_callback_typedefs_resolves_alias_chains(tmp_path: Path) -> None:
    utility_dir = tmp_path / "utility"
    utility_dir.mkdir()
    (utility_dir / "hooks.h").write_text(
        "\n".join([
            "typedef unsigned long (*HOOKFUNC)();",
            "typedef HOOKFUNC HOOKFUNCPTR;",
            "",
        ]),
        encoding="utf-8",
    )

    parsed = parse_callback_typedefs(str(tmp_path))

    assert parsed == {
        "HOOKFUNC": "unsigned long (*)()",
        "HOOKFUNCPTR": "unsigned long (*)()",
    }


def test_parse_callback_typedefs_ignores_multiline_preprocessor_blocks(
    tmp_path: Path,
) -> None:
    utility_dir = tmp_path / "utility"
    utility_dir.mkdir()
    (utility_dir / "hooks.h").write_text(
        "\n".join([
            "#define SOME_MACRO \\",
            "    (1 + \\",
            "    2)",
            "typedef unsigned long (*HOOKFUNC)();",
            "",
        ]),
        encoding="utf-8",
    )

    parsed = parse_callback_typedefs(str(tmp_path))

    assert parsed["HOOKFUNC"] == "unsigned long (*)()"


def test_parse_clib_prototypes_resolves_callback_typedef_args(
    tmp_path: Path,
) -> None:
    utility_dir = tmp_path / "utility"
    utility_dir.mkdir()
    (utility_dir / "hooks.h").write_text(
        "\n".join([
            "typedef unsigned long (*HOOKFUNC)();",
            "typedef HOOKFUNC HOOKFUNCPTR;",
            "",
        ]),
        encoding="utf-8",
    )
    clib_dir = tmp_path / "clib"
    clib_dir.mkdir()
    (clib_dir / "utility_protos.h").write_text(
        "\n".join([
            "#ifndef CLIB_UTILITY_PROTOS_H",
            "#define CLIB_UTILITY_PROTOS_H",
            "ULONG InstallCallback( HOOKFUNCPTR callback );",
            "#endif",
            "",
        ]),
        encoding="utf-8",
    )

    parsed = parse_clib_prototypes(str(tmp_path))

    assert parsed["utility"]["InstallCallback"] == [
        {"name": "callback", "type": "unsigned long (*)()"},
    ]


def test_reconcile_clib_callback_types_updates_semantics_from_headers(
    tmp_path: Path,
) -> None:
    clib_dir = tmp_path / "clib"
    clib_dir.mkdir()
    (clib_dir / "exec_protos.h").write_text(
        "\n".join([
            "ULONG Supervisor( unsigned long (*userFunction)() );",
            "APTR SetFunction( struct Library *library, long funcOffset, unsigned long (*newFunction)() );",
            "",
        ]),
        encoding="utf-8",
    )

    output = {
        "libraries": {
            "exec.library": {
                "functions": {
                    "Supervisor": {
                        "inputs": [
                            {"name": "userFunction", "regs": ["A5"], "type": "void *",
                             "semantic_kind": "code_ptr", "semantic_note": "manual"},
                        ],
                    },
                    "SetFunction": {
                        "inputs": [
                            {"name": "library", "regs": ["A1"], "type": "struct Library *"},
                            {"name": "funcOffset", "regs": ["A0"], "type": "LONG"},
                            {"name": "newFunction", "regs": ["D0"], "type": "APTR",
                             "semantic_kind": "code_ptr", "semantic_note": "manual"},
                        ],
                    },
                },
            },
        },
    }

    updates = reconcile_clib_callback_types(output, str(tmp_path))

    assert updates >= 4
    supervisor = output["libraries"]["exec.library"]["functions"]["Supervisor"]["inputs"][0]
    assert supervisor["type"] == "unsigned long (*)()"
    assert supervisor["semantic_kind"] == "code_ptr"
    assert "semantic_note" not in supervisor

    new_function = output["libraries"]["exec.library"]["functions"]["SetFunction"]["inputs"][2]
    assert new_function["type"] == "unsigned long (*)()"
    assert new_function["semantic_kind"] == "code_ptr"
    assert "semantic_note" not in new_function


def test_map_clib_args_to_inputs_prefers_exact_name_matches() -> None:
    mapped = _map_clib_args_to_inputs(
        [
            {"name": "library"},
            {"name": "funcOffset"},
            {"name": "funcEntry"},
        ],
        [
            {"name": "library", "type": "struct Library *"},
            {"name": "funcOffset", "type": "long"},
            {"name": "newFunction", "type": "unsigned long (*)()"},
        ],
    )

    assert mapped == {
        0: {"name": "library", "type": "struct Library *"},
        1: {"name": "funcOffset", "type": "long"},
        2: {"name": "newFunction", "type": "unsigned long (*)()"},
    }


def test_map_clib_args_to_inputs_uses_callback_only_positional_fallback() -> None:
    mapped = _map_clib_args_to_inputs(
        [
            {"name": "userFunc"},
        ],
        [
            {"name": "userFunction", "type": "unsigned long (*)()"},
        ],
    )

    assert mapped == {
        0: {"name": "userFunction", "type": "unsigned long (*)()"},
    }


def test_map_clib_args_to_inputs_does_not_use_non_callback_positional_fallback() -> None:
    mapped = _map_clib_args_to_inputs(
        [
            {"name": "handle"},
        ],
        [
            {"name": "fileHandle", "type": "LONG"},
        ],
    )

    assert mapped == {}


def test_map_clib_args_to_inputs_does_not_use_ambiguous_multi_callback_positional_fallback() -> None:
    mapped = _map_clib_args_to_inputs(
        [
            {"name": "firstFunc"},
            {"name": "secondFunc"},
        ],
        [
            {"name": "callbackA", "type": "unsigned long (*)()"},
            {"name": "callbackB", "type": "unsigned long (*)()"},
        ],
    )

    assert mapped == {}


def test_reconcile_clib_callback_types_matches_callback_args_by_position_when_names_diverge(
    tmp_path: Path,
) -> None:
    clib_dir = tmp_path / "clib"
    clib_dir.mkdir()
    (clib_dir / "exec_protos.h").write_text(
        "\n".join([
            "ULONG Supervisor( unsigned long (*userFunction)() );",
            "APTR SetFunction( struct Library *library, long funcOffset, unsigned long (*newFunction)() );",
            "",
        ]),
        encoding="utf-8",
    )

    output = {
        "libraries": {
            "exec.library": {
                "functions": {
                    "Supervisor": {
                        "inputs": [
                            {"name": "userFunc", "regs": ["A5"], "type": "void *"},
                        ],
                    },
                    "SetFunction": {
                        "inputs": [
                            {"name": "library", "regs": ["A1"], "type": "struct Library *"},
                            {"name": "funcOffset", "regs": ["A0"], "type": "LONG"},
                            {"name": "funcEntry", "regs": ["D0"], "type": "APTR"},
                        ],
                    },
                },
            },
        },
    }

    updates = reconcile_clib_callback_types(output, str(tmp_path))

    assert updates >= 4
    supervisor = output["libraries"]["exec.library"]["functions"]["Supervisor"]["inputs"][0]
    assert supervisor["type"] == "unsigned long (*)()"
    assert supervisor["semantic_kind"] == "code_ptr"

    func_entry = output["libraries"]["exec.library"]["functions"]["SetFunction"]["inputs"][2]
    assert func_entry["type"] == "unsigned long (*)()"
    assert func_entry["semantic_kind"] == "code_ptr"


def test_reconcile_clib_callback_types_does_not_use_positional_fallback_for_non_callbacks(
    tmp_path: Path,
) -> None:
    clib_dir = tmp_path / "clib"
    clib_dir.mkdir()
    (clib_dir / "exec_protos.h").write_text(
        "LONG Example( LONG fileHandle );\n",
        encoding="utf-8",
    )

    output = {
        "libraries": {
            "exec.library": {
                "functions": {
                    "Example": {
                        "inputs": [
                            {"name": "handle", "regs": ["D0"], "type": "LONG"},
                        ],
                    },
                },
            },
        },
    }

    updates = reconcile_clib_callback_types(output, str(tmp_path))

    assert updates == 0
    example = output["libraries"]["exec.library"]["functions"]["Example"]["inputs"][0]
    assert example["name"] == "handle"
    assert example["type"] == "LONG"
    assert "semantic_kind" not in example


def test_reconcile_clib_callback_types_updates_semantics_via_typedefs(
    tmp_path: Path,
) -> None:
    utility_dir = tmp_path / "utility"
    utility_dir.mkdir()
    (utility_dir / "hooks.h").write_text(
        "\n".join([
            "typedef unsigned long (*HOOKFUNC)();",
            "typedef HOOKFUNC HOOKFUNCPTR;",
            "",
        ]),
        encoding="utf-8",
    )
    clib_dir = tmp_path / "clib"
    clib_dir.mkdir()
    (clib_dir / "utility_protos.h").write_text(
        "\n".join([
            "ULONG InstallCallback( HOOKFUNCPTR callback );",
            "",
        ]),
        encoding="utf-8",
    )

    output = {
        "libraries": {
            "utility.library": {
                "functions": {
                    "InstallCallback": {
                        "inputs": [
                            {"name": "callback", "regs": ["A0"], "type": "APTR"},
                        ],
                    },
                },
            },
        },
    }

    updates = reconcile_clib_callback_types(output, str(tmp_path))

    assert updates >= 2
    callback = output["libraries"]["utility.library"]["functions"]["InstallCallback"]["inputs"][0]
    assert callback["type"] == "unsigned long (*)()"
    assert callback["semantic_kind"] == "code_ptr"


def test_parse_include_value_bindings_extracts_exec_io_domains(tmp_path: Path) -> None:
    exec_dir = tmp_path / "Include_I" / "Exec"
    exec_dir.mkdir(parents=True)
    include_path = exec_dir / "IO.I"
    include_path.write_text(
        "\n".join([
            " STRUCTURE  IO,MN_SIZE",
            "    UWORD   IO_COMMAND",
            "    UBYTE   IO_FLAGS",
            "    BITDEF  IO,QUICK,0",
            "    DEVINIT 0",
            "    DEVCMD  CMD_INVALID",
            "    DEVCMD  CMD_RESET",
            "    DEVCMD  CMD_READ",
            "    DEVCMD  CMD_WRITE",
            "    DEVCMD  CMD_NONSTD",
            "",
        ]),
        encoding="utf-8",
    )
    constants = evaluate_all_constants({
        "MN_SIZE": "20",
        "CMD_INVALID": "0",
        "CMD_RESET": "1",
        "CMD_READ": "2",
        "CMD_WRITE": "3",
        "CMD_NONSTD": "4",
        "IOB_QUICK": "0",
        "IOF_QUICK": "(1<<0)",
    })

    value_domains, field_bindings = parse_include_value_bindings(
        str(include_path),
        constants,
    )

    assert value_domains["exec.io.command"] == {
        "kind": "enum",
        "members": [
            "CMD_INVALID",
            "CMD_RESET",
            "CMD_READ",
            "CMD_WRITE",
            "CMD_NONSTD",
        ],
        "exact_match_policy": "error",
    }
    assert value_domains["exec.io.flags"] == {
        "kind": "flags",
        "members": ["IOF_QUICK"],
        "exact_match_policy": "error",
        "composition": "bit_or",
        "remainder_policy": "error",
    }
    assert field_bindings == [
        {"struct": "IO", "field": "IO_COMMAND", "domain": "exec.io.command", "available_since": "1.0"},
        {"struct": "IO", "field": "IO_FLAGS", "domain": "exec.io.flags", "available_since": "1.0"},
    ]


def test_parse_include_value_bindings_extracts_trackdisk_context_domains(tmp_path: Path) -> None:
    devices_dir = tmp_path / "Include_I" / "Devices"
    devices_dir.mkdir(parents=True)
    include_path = devices_dir / "TRACKDISK.I"
    include_path.write_text(
        "\n".join([
            "TD_NAME: MACRO",
            "    DC.B 'trackdisk.device',0",
            "    ENDM",
            "    DEVINIT",
            "    DEVCMD TD_MOTOR",
            "    DEVCMD TD_RAWREAD",
            "* raw read and write can be synced with a $4489 sync pattern.  This flag",
            "* in io request's IO_FLAGS field tells the driver that you want this.",
            "    BITDEF IOTD,WORDSYNC,5",
            "ETD_READ EQU (CMD_READ!TDF_EXTCOM)",
            "ETD_RAWREAD EQU (TD_RAWREAD!TDF_EXTCOM)",
            "",
        ]),
        encoding="utf-8",
    )
    constants = evaluate_all_constants({
        "CMD_READ": "2",
        "TDF_EXTCOM": "(1<<15)",
        "TD_MOTOR": "10",
        "TD_RAWREAD": "17",
        "ETD_READ": "(CMD_READ!TDF_EXTCOM)",
        "ETD_RAWREAD": "(TD_RAWREAD!TDF_EXTCOM)",
        "IOTDB_WORDSYNC": "5",
        "IOTDF_WORDSYNC": "(1<<5)",
    })

    value_domains, field_bindings = parse_include_value_bindings(
        str(include_path),
        constants,
    )

    assert value_domains["trackdisk.device.io_command"] == {
        "kind": "enum",
        "members": [
            "TD_MOTOR",
            "TD_RAWREAD",
            "ETD_READ",
            "ETD_RAWREAD",
        ],
        "exact_match_policy": "error",
    }
    assert value_domains["trackdisk.device.io_flags"] == {
        "kind": "flags",
        "members": ["IOTDF_WORDSYNC"],
        "exact_match_policy": "error",
        "composition": "bit_or",
        "remainder_policy": "error",
    }
    assert field_bindings == [
        {
            "struct": "IO",
            "field": "IO_COMMAND",
            "domain": "trackdisk.device.io_command",
            "context_name": "trackdisk.device",
            "available_since": "1.0",
        },
        {
            "struct": "IO",
            "field": "IO_FLAGS",
            "domain": "trackdisk.device.io_flags",
            "context_name": "trackdisk.device",
            "available_since": "1.0",
        },
    ]


def test_parse_include_value_bindings_extracts_generic_device_context_domains(tmp_path: Path) -> None:
    devices_dir = tmp_path / "Include_I" / "Devices"
    devices_dir.mkdir(parents=True)
    include_path = devices_dir / "TIMER.I"
    include_path.write_text(
        "\n".join([
            "TIMERNAME: MACRO",
            "    DC.B 'timer.device',0",
            "    ENDM",
            "    DEVINIT",
            "    DEVCMD TR_ADDREQUEST",
            "* in io request's IO_FLAGS field tells the driver that you want this.",
            "    BITDEF IOTR,QUICK,0",
            "",
        ]),
        encoding="utf-8",
    )
    constants = evaluate_all_constants({
        "TR_ADDREQUEST": "9",
        "IOTRB_QUICK": "0",
        "IOTRF_QUICK": "(1<<0)",
    })

    value_domains, field_bindings = parse_include_value_bindings(
        str(include_path),
        constants,
    )

    assert value_domains["timer.device.io_command"] == {
        "kind": "enum",
        "members": ["TR_ADDREQUEST"],
        "exact_match_policy": "error",
    }
    assert value_domains["timer.device.io_flags"] == {
        "kind": "flags",
        "members": ["IOTRF_QUICK"],
        "exact_match_policy": "error",
        "composition": "bit_or",
        "remainder_policy": "error",
    }
    assert field_bindings == [
        {
            "struct": "IO",
            "field": "IO_COMMAND",
            "domain": "timer.device.io_command",
            "context_name": "timer.device",
            "available_since": "1.0",
        },
        {
            "struct": "IO",
            "field": "IO_FLAGS",
            "domain": "timer.device.io_flags",
            "context_name": "timer.device",
            "available_since": "1.0",
        },
    ]


def test_corrections_json_exposes_explicit_api_value_bindings() -> None:
    corrections = load_os_reference_payload(AMIGA_OS_REFERENCE_CORRECTIONS_JSON)
    calling_convention = corrections["_meta"]["calling_convention"]
    exec_base_addr = corrections["_meta"]["exec_base_addr"]
    absolute_symbols = corrections["_meta"]["absolute_symbols"]
    value_domains = corrections["_meta"]["value_domains"]
    bindings = corrections["_meta"]["api_input_value_bindings"]
    semantic_assertions = corrections["_meta"]["api_input_semantic_assertions"]

    assert calling_convention == {
        "scratch_regs": ["D0", "D1", "A0", "A1"],
        "preserved_regs": ["D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6"],
        "base_reg": "A6",
        "return_reg": "D0",
        "note": "Parser-asserted: Amiga library calling convention from ROM Kernel Reference Manual, Libraries 3rd Ed, Ch7. D0-D1/A0-A1 are scratch (caller-saved). D2-D7/A2-A5 are preserved (callee-saved). A6 holds library base on entry, must be preserved. A7(SP) is stack pointer.",
        "seed_origin": "primary_doc",
        "review_status": "seeded",
        "citation": "ROM Kernel Reference Manual, Libraries 3rd Ed, Chapter 7",
    }
    assert exec_base_addr == {
        "address": 4,
        "library": "exec.library",
        "note": "Parser-asserted: ExecBase pointer stored at absolute address $4. ROM Kernel Reference Manual, Exec chapter. All Amiga programs load ExecBase via MOVEA.L ($0004).W,A6. The pointer is to the exec.library base structure.",
        "seed_origin": "primary_doc",
        "review_status": "seeded",
        "citation": "ROM Kernel Reference Manual, Exec chapter",
    }
    assert absolute_symbols == [
        {
            "address": 4,
            "name": "AbsExecBase",
            "note": "Parser-asserted: ExecBase pointer stored at absolute address $4. ROM Kernel Reference Manual, Exec chapter. All Amiga programs load ExecBase via MOVEA.L ($0004).W,A6. The pointer is to the exec.library base structure.",
            "seed_origin": "primary_doc",
            "review_status": "seeded",
            "citation": "ROM Kernel Reference Manual, Exec chapter",
        },
    ]
    assert value_domains == {
        "exec.allocmem.attributes": {
            "kind": "flags",
            "members": [
                "MEMF_ANY",
                "MEMF_PUBLIC",
                "MEMF_CHIP",
                "MEMF_FAST",
                "MEMF_LOCAL",
                "MEMF_24BITDMA",
                "MEMF_KICK",
                "MEMF_NO_EXPUNGE",
                "MEMF_CLEAR",
                "MEMF_LARGEST",
                "MEMF_REVERSE",
                "MEMF_TOTAL",
            ],
            "exact_match_policy": "error",
            "composition": "bit_or",
            "remainder_policy": "error",
        },
        "exec.signal_mask": {
            "kind": "flags",
            "members": [
                "SIGBREAKF_CTRL_C",
                "SIGBREAKF_CTRL_D",
                "SIGBREAKF_CTRL_E",
                "SIGBREAKF_CTRL_F",
            ],
            "exact_match_policy": "error",
            "composition": "bit_or",
            "remainder_policy": "error",
        },
        "dos.seek.mode": {
            "kind": "enum",
            "members": ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
            "exact_match_policy": "error",
        },
        "dos.lock.access_mode": {
            "kind": "enum",
            "members": ["ACCESS_READ", "ACCESS_WRITE"],
            "exact_match_policy": "error",
        },
        "dos.open.access_mode": {
            "kind": "enum",
            "members": ["MODE_NEWFILE", "MODE_OLDFILE", "MODE_READWRITE"],
            "exact_match_policy": "error",
        },
        "dos.packet.action": {
            "kind": "enum",
            "members": [
                "ACTION_NIL",
                "ACTION_GET_BLOCK",
                "ACTION_SET_MAP",
                "ACTION_DIE",
                "ACTION_EVENT",
                "ACTION_CURRENT_VOLUME",
                "ACTION_LOCATE_OBJECT",
                "ACTION_RENAME_DISK",
                "ACTION_FREE_LOCK",
                "ACTION_DELETE_OBJECT",
                "ACTION_RENAME_OBJECT",
                "ACTION_MORE_CACHE",
                "ACTION_COPY_DIR",
                "ACTION_WAIT_CHAR",
                "ACTION_SET_PROTECT",
                "ACTION_CREATE_DIR",
                "ACTION_EXAMINE_OBJECT",
                "ACTION_EXAMINE_NEXT",
                "ACTION_DISK_INFO",
                "ACTION_INFO",
                "ACTION_FLUSH",
                "ACTION_SET_COMMENT",
                "ACTION_PARENT",
                "ACTION_TIMER",
                "ACTION_INHIBIT",
                "ACTION_DISK_TYPE",
                "ACTION_DISK_CHANGE",
                "ACTION_SET_DATE",
                "ACTION_FINDUPDATE",
                "ACTION_FINDINPUT",
                "ACTION_FINDOUTPUT",
                "ACTION_END",
                "ACTION_SEEK",
                "ACTION_SET_FILE_SIZE",
                "ACTION_READ_RETURN",
                "ACTION_WRITE_RETURN",
                "ACTION_IS_FILESYSTEM",
                "ACTION_FH_FROM_LOCK",
                "ACTION_CHANGE_MODE",
                "ACTION_COPY_DIR_FH",
                "ACTION_PARENT_FH",
                "ACTION_EXAMINE_ALL",
                "ACTION_EXAMINE_FH",
                "ACTION_EXAMINE_ALL_END",
                "ACTION_SET_OWNER",
                "ACTION_CHANGE_SIGNAL",
                "ACTION_SCREEN_MODE",
                "ACTION_ADD_NOTIFY",
                "ACTION_REMOVE_NOTIFY",
            ],
            "exact_match_policy": "error",
        },
    }
    assert bindings == [
        {
            "library": "dos.library",
            "function": "Lock",
            "input": "accessMode",
            "domain": "dos.lock.access_mode",
            "available_since": "1.0",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "dos/dosextens.i Open() access mode constants",
        },
        {
            "library": "dos.library",
            "function": "Open",
            "input": "accessMode",
            "domain": "dos.open.access_mode",
            "available_since": "1.0",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "dos/dosextens.i Open() access mode constants",
        },
        {
            "library": "dos.library",
            "function": "Seek",
            "input": "mode",
            "domain": "dos.seek.mode",
            "available_since": "1.0",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "dos/dos.i Seek() mode constants",
        },
        {
            "library": "exec.library",
            "function": "AllocMem",
            "input": "attributes",
            "domain": "exec.allocmem.attributes",
            "available_since": "1.0",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "exec/memory.i MEMF_* constants",
        },
        {
            "library": "exec.library",
            "function": "AvailMem",
            "input": "attributes",
            "domain": "exec.allocmem.attributes",
            "available_since": "1.0",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "exec/memory.i MEMF_* constants",
        },
        {
            "library": "exec.library",
            "function": "SetSignal",
            "input": "signalMask",
            "domain": "exec.signal_mask",
            "available_since": "1.0",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "exec/signals.i SIGBREAKF_* constants",
        },
    ]
    assert corrections["_meta"]["struct_field_value_bindings"] == [
        {
            "struct": "DosPacket",
            "field": "dp_Type",
            "context_name": None,
            "domain": "dos.packet.action",
            "available_since": "1.3",
            "seed_origin": "include",
            "review_status": "seeded",
            "citation": "dos/dosextens.i DosPacket dp_Type ACTION_* constants",
        }
    ]
    assert semantic_assertions == [
        {
            "library": "exec.library",
            "function": "AddTask",
            "input": "finalPC",
            "semantic_kind": "code_ptr",
            "semantic_note": "Parser-authored: exec.library/AddTask uses finalPC as the task exit handler entry point. NDK synopsis types it as APTR, so direct parse cannot preserve callback semantics.",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "exec.library autodoc AddTask",
        },
        {
            "library": "exec.library",
            "function": "AddTask",
            "input": "initPC",
            "semantic_kind": "code_ptr",
            "semantic_note": "Parser-authored: exec.library/AddTask uses initPC as the new task entry point. NDK synopsis types it as APTR, so direct parse cannot distinguish code from generic pointer data.",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "exec.library autodoc AddTask",
        },
        {
            "library": "exec.library",
            "function": "ObtainQuickVector",
            "input": "interruptCode",
            "semantic_kind": "code_ptr",
            "semantic_note": "Parser-authored: exec.library/ObtainQuickVector autodoc says the function installs the code pointer into a quick interrupt vector. NDK synopsis types it as APTR, so direct parse loses callback semantics.",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "exec.library autodoc ObtainQuickVector",
        },
        {
            "library": "lowlevel.library",
            "function": "AddKBInt",
            "input": "intRoutine",
            "semantic_kind": "code_ptr",
            "semantic_note": "Parser-authored: lowlevel.library/AddKBInt autodoc says intRoutine is called from the keyboard interrupt context. NDK synopsis types it as APTR, so direct parse cannot preserve callback semantics.",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "lowlevel.library autodoc AddKBInt",
        },
        {
            "library": "lowlevel.library",
            "function": "AddTimerInt",
            "input": "intRoutine",
            "semantic_kind": "code_ptr",
            "semantic_note": "Parser-authored: lowlevel.library/AddTimerInt autodoc says intRoutine is called from timer interrupt context. NDK synopsis types it as APTR, so direct parse cannot preserve callback semantics.",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "lowlevel.library autodoc AddTimerInt",
        },
        {
            "library": "lowlevel.library",
            "function": "AddVBlankInt",
            "input": "intRoutine",
            "semantic_kind": "code_ptr",
            "semantic_note": "Parser-authored: lowlevel.library/AddVBlankInt autodoc says intRoutine is called from vertical blank interrupt context. NDK synopsis types it as APTR, so direct parse cannot preserve callback semantics.",
            "seed_origin": "autodoc",
            "review_status": "seeded",
            "citation": "lowlevel.library autodoc AddVBlankInt",
        },
    ]


def test_parse_synopsis_prefers_prototype_argument_names_over_fd_names() -> None:
    parsed = parse_synopsis(
        "\n".join([
            "LONG = Seek(file, position, mode)",
            "          D0    D1    D2        D3",
            "BPTR file;",
            "LONG position;",
            "LONG mode;",
        ]),
        ["file", "position", "offset"],
        [["d1"], ["d2"], ["d3"]],
    )

    assert [inp["name"] for inp in parsed["inputs"]] == ["file", "position", "mode"]


def test_parse_synopsis_ignores_trailing_signature_annotations() -> None:
    parsed = parse_synopsis(
        "\n".join([
            "Object * = NewObjectA(classPtr, classID, tags) (V39)",
            "             D0            A0      A1     A2",
            "Class * classPtr;",
            "ClassID classID;",
            "struct TagItem * tags;",
        ]),
        ["classPtr", "classID", "tagList"],
        [["a0"], ["a1"], ["a2"]],
    )

    assert [inp["name"] for inp in parsed["inputs"]] == ["classPtr", "classID", "tags"]


def test_build_os_include_kb_records_native_include_ownership(tmp_path: Path) -> None:
    include_dir = tmp_path / "INCLUDE_I"
    fd_dir = tmp_path / "FD"
    exec_dir = include_dir / "EXEC"
    exec_dir.mkdir(parents=True)
    fd_dir.mkdir()
    (exec_dir / "EXEC_LIB.I").write_text("EXEC_NATIVE\n", encoding="ascii")
    (fd_dir / "EXEC_LIB.FD").write_text(
        "\n".join([
            "##base _SysBase",
            "##bias 30",
            "##public",
            "OpenLibrary(name,version)(a1,d0)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    payload = build_os_include_kb(
        str(include_dir),
        str(fd_dir),
        {"exec.library": {"base": "SysBase", "functions": {"OpenLibrary": {"lvo": -30}}}},
    )

    owner = payload["library_lvo_owners"]["exec.library"]
    assert owner["kind"] == "native_include"
    assert owner["canonical_include_path"] == "exec/exec_lib.i"
    assert owner["assembler_include_path"] == "exec/exec_lib.i"


def test_includes_parsed_does_not_persist_lvo_index() -> None:
    payload = load_canonical_os_kb_includes_parsed()

    assert all("lvo_index" not in library for library in payload["libraries"].values())
    assert "_meta" in payload
    assert "library_lvo_owners" not in payload["_meta"]
    assert "constant_owners" not in payload["_meta"]


def test_other_parsed_is_sparse_function_overlay() -> None:
    payload = load_canonical_os_kb_other_parsed()

    assert set(payload) == {"_meta", "functions"}
    assert payload["functions"]
    sample_library = next(iter(sorted(payload["functions"])))
    assert sample_library.endswith(".library")
    assert payload["functions"][sample_library]


def test_merged_os_payload_derives_lvo_index_from_functions() -> None:
    includes = load_canonical_os_kb_includes_parsed()
    other = load_canonical_os_kb_other_parsed()
    corrections = load_os_reference_payload(AMIGA_OS_REFERENCE_CORRECTIONS_JSON)

    merged = merge_os_reference_payloads(
        includes=includes,
        other=other,
        corrections=corrections,
    )

    exec_library = merged["libraries"]["exec.library"]
    assert exec_library["lvo_index"]["-552"] == "OpenLibrary"
    assert exec_library["functions"]["OpenLibrary"]["lvo"] == -552
    assert exec_library["owner"]["canonical_include_path"] == "exec/exec_lib.i"
    assert merged["constants"]["MEMF_ANY"]["owner"]["canonical_include_path"] == "exec/memory.i"


def test_build_os_include_kb_records_fd_only_ownership_when_native_missing(tmp_path: Path) -> None:
    include_dir = tmp_path / "INCLUDE_I"
    fd_dir = tmp_path / "FD"
    include_dir.mkdir()
    fd_dir.mkdir()
    fd_path = fd_dir / "GRAPHICS_LIB.FD"
    fd_path.write_text(
        "\n".join([
            "##base _GfxBase",
            "##bias 30",
            "##public",
            "BltBitMap(srcBitMap,xSrc,ySrc,destBitMap,xDest,yDest,xSize,ySize,minterm,mask,tempA)(a0,d0/d1/a1,d2/d3/d4/d5/d6/d7/a2)",
            "Text(rp,string,count)(a1,a0,d0)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    payload = build_os_include_kb(
        str(include_dir),
        str(fd_dir),
        {
            "graphics.library": {
                "base": "GfxBase",
                "functions": {
                    "BltBitMap": {"lvo": -30},
                    "Text": {"lvo": -36},
                },
            }
        },
    )

    owner = payload["library_lvo_owners"]["graphics.library"]
    assert owner["kind"] == "fd_only"
    assert owner["canonical_include_path"] is None
    assert owner["assembler_include_path"] == "graphics/graphics_lib.i"
    assert owner["source_file"].endswith("/GRAPHICS_LIB.FD")


def test_build_os_compatibility_kb_records_earliest_include_and_struct_versions(tmp_path: Path) -> None:
    ndk_13 = tmp_path / "NDK_1.3" / "INCLUDES1.3" / "INCLUDE.I" / "EXEC"
    ndk_31 = tmp_path / "NDK_3.1" / "INCLUDES&LIBS" / "INCLUDE_I" / "EXEC"
    fd_13 = tmp_path / "NDK_1.3" / "FD"
    fd_31 = tmp_path / "NDK_3.1" / "FD"
    doc_31 = tmp_path / "NDK_3.1" / "DOCS" / "DOC"
    ndk_13.mkdir(parents=True)
    ndk_31.mkdir(parents=True)
    fd_13.mkdir(parents=True)
    fd_31.mkdir(parents=True)
    doc_31.mkdir(parents=True)
    resident_13 = "\n".join([
        " STRUCTURE RT,0",
        "    UWORD RT_MATCHWORD",
        "    APTR  RT_INIT",
        "    LABEL RT_SIZE",
        "",
    ])
    resident_31 = "\n".join([
        " STRUCTURE RT,0",
        "    UWORD RT_MATCHWORD",
        "    APTR  RT_BOOTINIT",
        "    APTR  RT_NEWFIELD",
        "    LABEL RT_SIZE",
        "",
    ])
    libraries_13 = "\n".join([
        "LIB_VECTSIZE EQU 6",
        "LIB_BASE EQU $FFFFFFFA",
        "LIB_USERDEF EQU LIB_BASE-(4*LIB_VECTSIZE)",
        "LIBINIT MACRO",
        " ENDM",
        "LIBDEF MACRO",
        " ENDM",
        " LIBINIT LIB_BASE",
        " LIBDEF LIB_OPEN",
        " LIBDEF LIB_CLOSE",
        " LIBDEF LIB_EXPUNGE",
        " LIBDEF LIB_EXTFUNC",
        " STRUCTURE LIB,0",
        "    UWORD LIB_VERSION",
        "    LABEL LIB_SIZE",
        "",
    ])
    io_text = "\n".join([
        " LIBINIT",
        " LIBDEF DEV_BEGINIO",
        " LIBDEF DEV_ABORTIO",
        "",
    ])
    exec_doc = "\n".join([
        "exec.library/InitResident",
        "RTF_AUTOINIT set in rt_Flags, and an rt_Init pointer which points",
        "to four longwords.",
        "specific function offsets, terminated with -1L.",
        "Pointer to data table in exec/InitStruct format for",
        "initialization of Library or Device structure.",
        "Pointer to library initialization function, or NULL.",
        "(short format offsets are also acceptable)",
        "",
    ])
    (ndk_13 / "resident.i").write_text(resident_13, encoding="ascii")
    (ndk_31 / "resident.i").write_text(resident_31, encoding="ascii")
    (ndk_13 / "libraries.i").write_text(libraries_13, encoding="ascii")
    (ndk_31 / "libraries.i").write_text(libraries_13, encoding="ascii")
    (ndk_13 / "io.i").write_text(io_text, encoding="ascii")
    (ndk_31 / "io.i").write_text(io_text, encoding="ascii")
    (ndk_13 / "exec_lib.i").write_text("EXEC_LIB\n", encoding="ascii")
    (ndk_31 / "exec_lib.i").write_text("EXEC_LIB\n", encoding="ascii")
    (doc_31 / "EXEC.DOC").write_text(exec_doc, encoding="ascii")
    type_macros = "\n".join([
        "UWORD MACRO",
        "SOFFSET SET SOFFSET+2",
        " ENDM",
        "APTR MACRO",
        "SOFFSET SET SOFFSET+4",
        " ENDM",
        "",
    ])
    (ndk_13 / "types.i").write_text(type_macros, encoding="ascii")
    (ndk_31 / "types.i").write_text(type_macros, encoding="ascii")
    exec_fd_13 = "\n".join([
        "##base _SysBase",
        "##bias 30",
        "##public",
        "OpenLibrary(name,version)(a1,d0)",
        "##end",
        "",
    ])
    exec_fd_31 = "\n".join([
        "##base _SysBase",
        "##bias 30",
        "##public",
        "OpenLibrary(name,version)(a1,d0)",
        "OpenResource(name)(a1)",
        "##end",
        "",
    ])
    (fd_13 / "EXEC_LIB.FD").write_text(exec_fd_13, encoding="ascii")
    (fd_31 / "EXEC_LIB.FD").write_text(exec_fd_31, encoding="ascii")

    include_kb = {
        "library_lvo_owners": {
            "exec.library": {
                "kind": "native_include",
                "canonical_include_path": "exec/exec_lib.i",
                "assembler_include_path": "exec/exec_lib.i",
                "source_file": "D:/NDK/NDK_3.1/INCLUDES&LIBS/INCLUDE_I/EXEC/EXEC_LIB.I",
            }
        }
    }
    structs = {
        "RT": {
            "source": "EXEC/RESIDENT.I",
            "base_offset": 0,
            "base_offset_symbol": None,
            "size": 10,
            "fields": [
                {"name": "RT_MATCHWORD", "type": "UWORD", "offset": 0, "size": 2},
                {"name": "RT_BOOTINIT", "type": "APTR", "offset": 2, "size": 4},
                {"name": "RT_NEWFIELD", "type": "APTR", "offset": 6, "size": 4},
            ],
        },
        "LIB": {
            "source": "EXEC/LIBRARIES.I",
            "base_offset": 0,
            "base_offset_symbol": None,
            "size": 2,
            "fields": [
                {"name": "LIB_VERSION", "type": "UWORD", "offset": 0, "size": 2},
            ],
        },
    }

    payload = build_os_compatibility_kb(
        {"1.3": str(tmp_path / "NDK_1.3"), "3.1": str(tmp_path / "NDK_3.1")},
        include_kb,
        structs,
        {
            "LIB_VERSION": "0",
            "RT_NEWFIELD": "0",
        },
    )

    payload_versions = cast(list[str], payload["compatibility_versions"])
    function_min_versions = cast(dict[str, str], payload["_function_min_versions"])
    include_min_versions = cast(dict[str, str], payload["include_min_versions"])
    constant_min_versions = cast(dict[str, str], payload["_constant_min_versions"])
    rt_struct = structs["RT"]
    rt_fields = cast(list[dict[str, object]], rt_struct["fields"])

    assert payload_versions == ["1.3", "3.1"]
    assert function_min_versions["exec.library/OpenLibrary"] == "1.3"
    assert function_min_versions["exec.library/OpenResource"] == "3.1"
    assert include_min_versions["exec/resident.i"] == "1.3"
    assert include_min_versions["exec/libraries.i"] == "1.3"
    assert constant_min_versions["LIB_VERSION"] == "1.3"
    assert constant_min_versions["RT_NEWFIELD"] == "3.1"
    assert rt_struct["available_since"] == "1.3"
    assert rt_fields[0]["available_since"] == "1.3"
    assert "names_by_version" not in rt_fields[0]
    assert rt_fields[1]["available_since"] == "1.3"
    assert cast(dict[str, str], rt_fields[1]["names_by_version"]) == {
        "1.3": "RT_INIT",
        "3.1": "RT_BOOTINIT",
    }
    assert rt_fields[2]["available_since"] == "3.1"


def test_build_fd_function_min_versions_records_earliest_fd_presence(tmp_path: Path) -> None:
    fd_13 = tmp_path / "NDK_1.3" / "FD"
    fd_31 = tmp_path / "NDK_3.1" / "FD"
    fd_13.mkdir(parents=True)
    fd_31.mkdir(parents=True)
    (fd_13 / "EXEC_LIB.FD").write_text(
        "\n".join([
            "##base _SysBase",
            "##bias 30",
            "##public",
            "OpenLibrary(name,version)(a1,d0)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )
    (fd_31 / "EXEC_LIB.FD").write_text(
        "\n".join([
            "##base _SysBase",
            "##bias 30",
            "##public",
            "OpenLibrary(name,version)(a1,d0)",
            "OpenResource(name)(a1)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    payload = build_fd_function_min_versions(
        {"1.3": str(tmp_path / "NDK_1.3"), "3.1": str(tmp_path / "NDK_3.1")}
    )

    assert payload[("exec.library", "OpenLibrary")] == "1.3"
    assert payload[("exec.library", "OpenResource")] == "3.1"


def test_collect_raw_constants_from_include_dir_records_generated_constants(tmp_path: Path) -> None:
    exec_dir = tmp_path / "INCLUDE_I" / "EXEC"
    exec_dir.mkdir(parents=True)
    (exec_dir / "types.i").write_text(
        "\n".join([
            "UWORD MACRO",
            "SOFFSET SET SOFFSET+2",
            " ENDM",
            "APTR MACRO",
            "SOFFSET SET SOFFSET+4",
            " ENDM",
            "",
        ]),
        encoding="ascii",
    )
    (exec_dir / "resident.i").write_text(
        "\n".join([
            " STRUCTURE RT,0",
            "    UWORD RT_MATCHWORD",
            "    APTR  RT_INIT",
            "    LABEL RT_SIZE",
            "",
        ]),
        encoding="ascii",
    )

    raw_constants, _constant_source_files, parsed_include_paths = collect_raw_constants_from_include_dir(
        str(tmp_path / "INCLUDE_I"),
        scan_type_macros(str(tmp_path / "INCLUDE_I")),
    )

    assert raw_constants["RT"] == "0"
    assert raw_constants["RT_MATCHWORD"] == "0"
    assert raw_constants["RT_INIT"] == "2"
    assert raw_constants["RT_SIZE"] == "6"
    assert str(exec_dir / "resident.i") in parsed_include_paths


def test_scan_fd_function_names_handles_legacy_fd_signatures_without_args(tmp_path: Path) -> None:
    fd_path = tmp_path / "EXEC_LIB.FD"
    fd_path.write_text(
        "\n".join([
            "##base _SysBase",
            "##bias 30",
            "##public",
            "RawDoFmt()(A0/A1/A2/A3)",
            "OpenLibrary(name,version)(a1,d0)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    assert scan_fd_function_names(str(fd_path)) == ["RawDoFmt", "OpenLibrary"]


def test_build_os_compatibility_kb_records_resident_autoinit_contract(tmp_path: Path) -> None:
    ndk_13 = tmp_path / "NDK_1.3" / "INCLUDES1.3" / "INCLUDE.I" / "EXEC"
    ndk_20 = tmp_path / "NDK_2.0" / "NDK2.0-4" / "INCLUDE" / "EXEC"
    doc_20 = tmp_path / "NDK_2.0" / "NDK2.0-4" / "DOC"
    ndk_13.mkdir(parents=True)
    ndk_20.mkdir(parents=True)
    doc_20.mkdir(parents=True)
    resident_text = "\n".join([
        " STRUCTURE RT,0",
        "    UWORD RT_MATCHWORD",
        "    APTR  RT_INIT",
        "    LABEL RT_SIZE",
        "",
        "    BITDEF RT,AUTOINIT,7",
        "",
    ])
    libraries_text = "\n".join([
        "LIB_VECTSIZE EQU 6",
        "LIB_BASE EQU $FFFFFFFA",
        "LIB_USERDEF EQU LIB_BASE-(4*LIB_VECTSIZE)",
        "LIBINIT MACRO",
        " ENDM",
        "LIBDEF MACRO",
        " ENDM",
        " LIBINIT LIB_BASE",
        " LIBDEF LIB_OPEN",
        " LIBDEF LIB_CLOSE",
        " LIBDEF LIB_EXPUNGE",
        " LIBDEF LIB_EXTFUNC",
        "",
    ])
    io_text = "\n".join([
        " LIBINIT",
        " LIBDEF DEV_BEGINIO",
        " LIBDEF DEV_ABORTIO",
        "",
    ])
    exec_doc = "\n".join([
        "exec.library/InitResident",
        "AUTOINIT FEATURE",
        "An automatic method of library/device base and vector table",
        "initialization is also provided by InitResident().",
        "RTF_AUTOINIT set in rt_Flags, and an rt_Init pointer which points",
        "to four longwords.  These four longwords will be used in a call",
        "to MakeLibrary();",
        "",
        "- The size of your library/device base structure including initial",
        "  Library or Device structure.",
        "- A pointer to a longword table of standard, then library",
        "  specific function offsets, terminated with -1L.",
        "  (short format offsets are also acceptable)",
        "- Pointer to data table in exec/InitStruct format for",
        "  initialization of Library or Device structure.",
        "- Pointer to library initialization function, or NULL.",
        "",
        "exec.library/MakeLibrary",
        "vectors - pointer to an array of function pointers or function",
        "displacements. If the first word of the array is -1, then",
        "the array contains relative word displacements (based off",
        "of vectors); otherwise, the array contains absolute",
        "function pointers. The vector list is terminated by a -1",
        "(of the same size as the pointers).",
        "",
        "exec.library/MakeFunctions",
        "functionArray - pointer to an array of function pointers or",
        "function displacements. If funcDispBase is zero, the array",
        "is assumed to contain absolute pointers. If funcDispBase is not zero,",
        "then the array is assumed to contain word displacements to functions.",
        "In both cases, the array is terminated by a -1 (of the same size as the",
        "actual entry).",
        "",
    ])
    for root in (ndk_13, ndk_20):
        (root / "resident.i").write_text(resident_text, encoding="ascii")
        (root / "libraries.i").write_text(libraries_text, encoding="ascii")
        (root / "io.i").write_text(io_text, encoding="ascii")
    (doc_20 / "EXEC.DOC").write_text(exec_doc, encoding="ascii")
    type_macros = "\n".join([
        "UWORD MACRO",
        "SOFFSET SET SOFFSET+2",
        " ENDM",
        "APTR MACRO",
        "SOFFSET SET SOFFSET+4",
        " ENDM",
    ])
    (ndk_13 / "types.i").write_text(type_macros, encoding="ascii")
    (ndk_20 / "types.i").write_text(type_macros, encoding="ascii")
    include_kb = {
        "library_lvo_owners": {
            "exec.library": {
                "kind": "include",
                "canonical_include_path": "exec/libraries.i",
                "assembler_include_path": None,
                "source_file": str(ndk_20 / "libraries.i"),
            }
        }
    }
    structs = {
        "RT": {
            "source": "EXEC/RESIDENT.I",
            "base_offset": 0,
            "base_offset_symbol": None,
            "size": 6,
            "fields": [
                {"name": "RT_MATCHWORD", "type": "UWORD", "offset": 0, "size": 2},
                {"name": "RT_INIT", "type": "APTR", "offset": 2, "size": 4},
            ],
        }
    }

    payload = build_os_compatibility_kb(
        {"1.3": str(tmp_path / "NDK_1.3"), "2.0": str(tmp_path / "NDK_2.0")},
        include_kb,
        structs,
        {
            "LIB_VECTSIZE": "6",
            "LIB_BASE": "$FFFFFFFA",
            "LIB_USERDEF": "$FFFFFFE2",
        },
    )

    assert cast(list[str], payload["resident_autoinit_words"]) == [
        "base_size",
        "vectors",
        "structure_init",
        "init_func",
    ]
    assert cast(dict[str, str], payload["resident_autoinit_word_stream_formats"]) == {
        "structure_init": "exec.InitStruct",
    }
    assert cast(bool, payload["resident_autoinit_supports_short_vectors"]) is True
    assert cast(dict[str, list[str]], payload["resident_vector_prefixes"]) == {
        "device": [
            "LIB_OPEN",
            "LIB_CLOSE",
            "LIB_EXPUNGE",
            "LIB_EXTFUNC",
            "DEV_BEGINIO",
            "DEV_ABORTIO",
        ],
        "library": [
            "LIB_OPEN",
            "LIB_CLOSE",
            "LIB_EXPUNGE",
            "LIB_EXTFUNC",
        ],
    }
    resident_entry_register_seeds = cast(
        dict[str, dict[str, list[dict[str, object]]]],
        payload["resident_entry_register_seeds"],
    )
    assert resident_entry_register_seeds["library"]["init"] == [
        {
            "register": "D0",
            "kind": "library_base",
            "named_base_source": "current_target",
        },
        {
            "register": "A6",
            "kind": "library_base",
            "named_base_source": "fixed",
            "named_base_name": "exec.library",
        },
    ]
    assert resident_entry_register_seeds["device"]["DEV_BEGINIO"] == [
        {"register": "A1", "kind": "struct_ptr", "struct_name": "IOStdReq"},
    ]

def test_parse_asm_include_extracts_typed_data_stream_format_from_initializers(
    tmp_path: Path,
) -> None:
    include_dir = tmp_path / "INCLUDE_I" / "EXEC"
    include_dir.mkdir(parents=True)
    include_path = include_dir / "INITIALIZERS.I"
    include_path.write_text(
        "\n".join([
            "** Macros for creating InitStruct() tables",
            "",
            "INITBYTE MACRO ; &offset,&value",
            "        IFLE    (\\1)-255",
            "        DC.B    $a0,\\1",
            "        DC.B    \\2,0",
            "        MEXIT",
            "        ENDC",
            "        DC.B    $e0,0",
            "        DC.W    \\1",
            "        DC.B    \\2,0",
            "        ENDM",
            "",
            "INITWORD MACRO ; &offset,&value",
            "        IFLE    (\\1)-255",
            "        DC.B    $90,\\1",
            "        DC.W    \\2",
            "        MEXIT",
            "        ENDC",
            "        DC.B    $d0,0",
            "        DC.W    \\1",
            "        DC.W    \\2",
            "        ENDM",
            "",
            "INITLONG MACRO ; &offset,&value",
            "        IFLE    (\\1)-255",
            "        DC.B    $80,\\1",
            "        DC.L    \\2",
            "        MEXIT",
            "        ENDC",
            "        DC.B    $c0,0",
            "        DC.W    \\1",
            "        DC.L    \\2",
            "        ENDM",
            "",
            "INITSTRUCT MACRO ; &size,&offset,&value,&count",
            "        DS.W    0",
            "        IFC     '\\4',''",
            "COUNT\\@ SET    0",
            "        ENDC",
            "        IFNC    '\\4',''",
            "COUNT\\@ SET    \\4",
            "        ENDC",
            "CMD\\@   SET     (((\\1)<<4)!COUNT\\@)",
            "        IFLE    (\\2)-255",
            "        DC.B    (CMD\\@)!$80",
            "        DC.B    \\2",
            "        MEXIT",
            "        ENDC",
            "        DC.B    CMD\\@!$0C0",
            "        DC.B    (((\\2)>>16)&$0FF)",
            "        DC.W    ((\\2)&$0FFFF)",
            "        ENDM",
            "",
        ]),
        encoding="ascii",
    )

    payload = parse_asm_include(str(include_path), {}, {})

    stream = cast(dict[str, object], payload["typed_data_stream_formats"]["exec.InitStruct"])
    command_byte = cast(dict[str, object], stream["command_byte"])
    constructors = cast(list[dict[str, object]], stream["constructors"])

    assert cast(str, stream["include_path"]) == "exec/initializers.i"
    assert cast(int, stream["alignment"]) == 2
    assert cast(int, stream["terminator_opcode"]) == 0
    assert cast(dict[str, int], command_byte["destination_modes"]) == {
        "next_count": 0,
        "next_repeat": 1,
        "byte_offset_count": 2,
        "long_offset_count": 3,
    }
    assert constructors == [
        {
            "name": "INITBYTE",
            "unit_size": 1,
            "count": 1,
            "destination_mode": "byte_offset_count",
            "opcode": 0xA0,
        },
        {
            "name": "INITBYTE",
            "unit_size": 1,
            "count": 1,
            "destination_mode": "long_offset_count",
            "opcode": 0xE0,
        },
        {
            "name": "INITWORD",
            "unit_size": 2,
            "count": 1,
            "destination_mode": "byte_offset_count",
            "opcode": 0x90,
        },
        {
            "name": "INITWORD",
            "unit_size": 2,
            "count": 1,
            "destination_mode": "long_offset_count",
            "opcode": 0xD0,
        },
        {
            "name": "INITLONG",
            "unit_size": 4,
            "count": 1,
            "destination_mode": "byte_offset_count",
            "opcode": 0x80,
        },
        {
            "name": "INITLONG",
            "unit_size": 4,
            "count": 1,
            "destination_mode": "long_offset_count",
            "opcode": 0xC0,
        },
    ]


def test_canonicalize_json_sorts_nested_dict_keys() -> None:
    payload = {
        "z": {"b": 2, "a": 1},
        "a": [{"y": 2, "x": 1}],
    }

    canonical = canonicalize_json(payload)

    assert list(canonical) == ["a", "z"]
    assert list(cast(dict[str, object], canonical["z"])) == ["a", "b"]
    nested = cast(list[object], canonical["a"])
    assert list(cast(dict[str, object], nested[0])) == ["x", "y"]


def test_parse_fd_file_preserves_register_groups(tmp_path: Path) -> None:
    fd_path = tmp_path / "MATHIEEEDOUBBAS_LIB.FD"
    fd_path.write_text(
        "\n".join([
            "##base _MathBase",
            "##bias 30",
            "##public",
            "IEEEDPFix(parm)(D0/D1)",
            "IEEEDPCmp(leftParm,rightParm)(D0/D1,D2/D3)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    payload = parse_fd_file(str(fd_path))

    assert payload["functions"]["IEEEDPFix"]["regs"] == [["D0", "D1"]]
    assert payload["functions"]["IEEEDPCmp"]["regs"] == [["D0", "D1"], ["D2", "D3"]]


def test_parse_fd_file_supports_flat_slash_separated_argument_registers(tmp_path: Path) -> None:
    fd_path = tmp_path / "AMIGAGUIDE_LIB.FD"
    fd_path.write_text(
        "\n".join([
            "##base _AGBase",
            "##bias 30",
            "##public",
            "OpenAmigaGuideA(nag,*)(a0/a1)",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    payload = parse_fd_file(str(fd_path))

    assert payload["functions"]["OpenAmigaGuideA"]["regs"] == [["A0"], ["A1"]]


def test_parse_fd_file_rejects_missing_register_spec_for_arguments(tmp_path: Path) -> None:
    fd_path = tmp_path / "BROKEN_LIB.FD"
    fd_path.write_text(
        "\n".join([
            "##base _BrokenBase",
            "##bias 30",
            "##public",
            "Broken(arg)()",
            "##end",
            "",
        ]),
        encoding="ascii",
    )

    import pytest

    with pytest.raises(ValueError, match="no register spec"):
        parse_fd_file(str(fd_path))

from pathlib import Path

from kb.ndk_parser import (
    _extract_input_constant_domains,
    _map_clib_args_to_inputs,
    build_os_include_kb,
    evaluate_all_constants,
    parse_callback_typedefs,
    parse_clib_prototypes,
    parse_fd_file,
    parse_include_value_domains,
    parse_synopsis,
    reconcile_clib_callback_types,
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


def test_parse_include_value_domains_extracts_exec_io_domains(tmp_path: Path) -> None:
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

    value_domains, field_domains, field_contexts = parse_include_value_domains(
        str(include_path),
        constants,
    )

    assert value_domains["exec.io.command"] == [
        "CMD_INVALID",
        "CMD_RESET",
        "CMD_READ",
        "CMD_WRITE",
        "CMD_NONSTD",
    ]
    assert value_domains["exec.io.flags"] == ["IOF_QUICK"]
    assert field_domains == {
        "IO.IO_COMMAND": "exec.io.command",
        "IO.IO_FLAGS": "exec.io.flags",
    }
    assert field_contexts == {}


def test_parse_include_value_domains_extracts_trackdisk_context_domains(tmp_path: Path) -> None:
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

    value_domains, field_domains, field_contexts = parse_include_value_domains(
        str(include_path),
        constants,
    )

    assert field_domains == {}
    assert value_domains["trackdisk.device.io_command"] == [
        "TD_MOTOR",
        "TD_RAWREAD",
        "ETD_READ",
        "ETD_RAWREAD",
    ]
    assert value_domains["trackdisk.device.io_flags"] == ["IOTDF_WORDSYNC"]
    assert field_contexts == {
        "IO.IO_COMMAND": {"trackdisk.device": "trackdisk.device.io_command"},
        "IO.IO_FLAGS": {"trackdisk.device": "trackdisk.device.io_flags"},
    }


def test_parse_include_value_domains_extracts_generic_device_context_domains(tmp_path: Path) -> None:
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

    value_domains, field_domains, field_contexts = parse_include_value_domains(
        str(include_path),
        constants,
    )

    assert field_domains == {}
    assert value_domains["timer.device.io_command"] == ["TR_ADDREQUEST"]
    assert value_domains["timer.device.io_flags"] == ["IOTRF_QUICK"]
    assert field_contexts == {
        "IO.IO_COMMAND": {"timer.device": "timer.device.io_command"},
        "IO.IO_FLAGS": {"timer.device": "timer.device.io_flags"},
    }


def test_extract_input_constant_domains_uses_input_sections_when_available() -> None:
    doc = {
        "inputs_text": (
            "handle - file handle\n\n"
            "mode - OFFSET_BEGINNING, OFFSET_CURRENT or OFFSET_END\n\n"
            "flags - ignored here\n"
        )
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["handle", "mode", "flags"],
        ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END", "CONFLAG_DEFAULT"],
    )

    assert input_domains == {
        "mode": ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    }


def test_extract_input_constant_domains_uses_named_description_paragraphs() -> None:
    doc = {
        "description": (
            "Seek() sets the file position.\n\n"
            "'mode' can be OFFSET_BEGINNING, OFFSET_CURRENT or OFFSET_END.\n"
            "It specifies the relative start position.\n"
        )
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["file", "position", "mode"],
        ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    )

    assert input_domains == {
        "mode": ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    }


def test_extract_input_constant_domains_handles_wrapped_named_description_sentence() -> None:
    doc = {
        "description": (
            "Seek() sets the read/write cursor for the file 'file' to the\n"
            "position 'position'. This position is used by both Read() and\n"
            "Write() as a place to start reading or writing. The result is the\n"
            "current absolute position in the file, or -1 if an error occurs, in\n"
            "which case IoErr() can be used to find more information. 'mode' can\n"
            "be OFFSET_BEGINNING, OFFSET_CURRENT or OFFSET_END. It is used to\n"
            "specify the relative start position.\n"
        )
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["file", "position", "mode"],
        ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    )

    assert input_domains == {
        "mode": ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    }


def test_extract_input_constant_domains_attaches_nested_input_section_constants_to_attributes() -> None:
    doc = {
        "inputs_text": (
            "byteSize - requested size\n\n"
            "attributes -\n"
            "    requirements\n\n"
            "\tMEMF_CHIP:\tchip memory\n\n"
            "\tMEMF_FAST:\tfast memory\n\n"
            "\tMEMF_PUBLIC:\tpublic memory\n"
        )
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["byteSize", "attributes"],
        ["MEMF_CHIP", "MEMF_FAST", "MEMF_PUBLIC"],
    )

    assert input_domains == {
        "attributes": ["MEMF_CHIP", "MEMF_FAST", "MEMF_PUBLIC"],
    }


def test_extract_input_constant_domains_uses_unquoted_named_description_lines() -> None:
    doc = {
        "description": (
            "If the accessMode is ACCESS_READ, the lock is a shared read lock;\n"
            "if the accessMode is ACCESS_WRITE then it is an exclusive write\n"
            "lock.\n"
        )
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["name", "accessMode"],
        ["ACCESS_READ", "ACCESS_WRITE"],
    )

    assert input_domains == {
        "accessMode": ["ACCESS_READ", "ACCESS_WRITE"],
    }


def test_extract_input_constant_domains_uses_examples_for_signal_masks() -> None:
    doc = {
        "synopsis": (
            "oldSignals = SetSignal(newSignals, signalMask)\n"
            "D0                 D0          D1\n"
        ),
        "inputs_text": (
            "newSignals - the new values for the signals specified in\n"
            "             signalMask.\n"
            "signalMask - the set of signals to be affected.\n"
        ),
        "description": "This function can query or modify the current task's signals.",
        "examples": (
            "SetSignal(0L,SIGBREAKF_CTRL_C);\n"
            "if(SetSignal(0L,SIGBREAKF_CTRL_C) & SIGBREAKF_CTRL_C)\n"
        ),
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["newSignals", "signalMask"],
        ["SIGBREAKF_CTRL_C"],
    )

    assert input_domains == {
        "signalMask": ["SIGBREAKF_CTRL_C"],
    }


def test_extract_input_constant_domains_does_not_infer_open_device_domains_from_generic_docs() -> None:
    doc = {
        "inputs_text": (
            "devName - requested device name\n\n"
            "unitNumber - the unit number to open on that device. If the device does\n"
            "not have separate units, send a zero.\n\n"
            "iORequest - request block to initialize\n\n"
            "flags - additional driver specific information. This is sometimes\n"
            "used to request opening a device with exclusive access.\n"
        )
    }

    input_domains = _extract_input_constant_domains(
        doc,
        ["devName", "unitNumber", "iORequest", "flags"],
        ["CONFLAG_DEFAULT", "CONU_STANDARD", "CMD_WRITE"],
    )

    assert input_domains == {}


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


def test_input_constant_domains_follow_synopsis_prototype_argument_names() -> None:
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
    input_domains = _extract_input_constant_domains(
        {
            "inputs_text": (
                "file - file handle\n\n"
                "position - byte offset\n\n"
                "mode - OFFSET_BEGINNING, OFFSET_CURRENT or OFFSET_END\n"
            )
        },
        [str(inp["name"]) for inp in parsed["inputs"]],
        ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    )

    assert input_domains == {
        "mode": ["OFFSET_BEGINNING", "OFFSET_CURRENT", "OFFSET_END"],
    }


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
    assert owner["include_path"] == "exec/exec_lib.i"
    assert owner["comment_include_path"] == "exec/exec_lib.i"


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
    assert owner["include_path"] is None
    assert owner["comment_include_path"] == "graphics/graphics_lib.i"
    assert owner["source_file"].endswith("/GRAPHICS_LIB.FD")


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

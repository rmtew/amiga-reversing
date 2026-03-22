import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from parse_ndk import parse_clib_prototypes, reconcile_clib_callback_types


def test_parse_clib_prototypes_preserves_function_pointer_args(tmp_path):
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


def test_reconcile_clib_callback_types_updates_semantics_from_headers(tmp_path):
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
                            {"name": "userFunction", "reg": "A5", "type": "void *",
                             "semantic_kind": "code_ptr", "semantic_note": "manual"},
                        ],
                    },
                    "SetFunction": {
                        "inputs": [
                            {"name": "library", "reg": "A1", "type": "struct Library *"},
                            {"name": "funcOffset", "reg": "A0", "type": "LONG"},
                            {"name": "newFunction", "reg": "D0", "type": "APTR",
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

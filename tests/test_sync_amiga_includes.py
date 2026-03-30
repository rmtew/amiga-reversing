from pathlib import Path

from scripts.sync_amiga_includes import sync_amiga_includes


def test_sync_amiga_includes_replaces_raw_lib_i_from_fd(tmp_path: Path) -> None:
    ndk_root = tmp_path / "ndk"
    include_dir = ndk_root / "INCLUDES&LIBS" / "INCLUDE_I" / "EXEC"
    fd_dir = ndk_root / "INCLUDES&LIBS" / "FD"
    include_dir.mkdir(parents=True)
    fd_dir.mkdir(parents=True)
    (include_dir / "EXEC_LIB.I").write_text(
        "FUNCDEF Foo\nFUNCDEF Bar\nFUNCDEF Baz\n",
        encoding="utf-8",
        newline="",
    )
    (fd_dir / "EXEC_LIB.FD").write_text(
        "##base _ExecBase\n##bias 12\nBar()()\nBaz()()\n##end\n",
        encoding="utf-8",
    )
    dest_root = tmp_path / "out"

    sync_amiga_includes(ndk_root, dest_root)

    generated = (dest_root / "include" / "exec" / "exec_lib.i").read_text(encoding="utf-8")
    assert generated == "_LVOFoo\tEQU\t-6\n_LVOBar\tEQU\t-12\n_LVOBaz\tEQU\t-18\n"


def test_sync_amiga_includes_adds_generated_device_lib_i(tmp_path: Path) -> None:
    ndk_root = tmp_path / "ndk"
    include_dir = ndk_root / "INCLUDES&LIBS" / "INCLUDE_I" / "DEVICES"
    fd_dir = ndk_root / "INCLUDES&LIBS" / "FD"
    include_dir.mkdir(parents=True)
    fd_dir.mkdir(parents=True)
    (include_dir / "TIMER.I").write_text("UNIT_VBLANK EQU 0\n", encoding="utf-8", newline="")
    (fd_dir / "TIMER_LIB.FD").write_text(
        "##base _TimerBase\n##bias 42\nAddTime()()\nSubTime()()\nCmpTime()()\n##end\n",
        encoding="utf-8",
    )
    dest_root = tmp_path / "out"

    sync_amiga_includes(ndk_root, dest_root)

    copied = (dest_root / "include" / "devices" / "timer.i").read_text(encoding="utf-8")
    generated = (dest_root / "include" / "devices" / "timer_lib.i").read_text(encoding="utf-8")
    assert copied == "UNIT_VBLANK EQU 0\n"
    assert generated == "_LVOAddTime\tEQU\t-42\n_LVOSubTime\tEQU\t-48\n_LVOCmpTime\tEQU\t-54\n"

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from src.real_target_fixtures import get_real_target_fixture
from src.tests._build_helpers import prepare_test_exe
from src.tests._build_helpers import require_built_tools

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "src" / "build"
ASM_EXE = BUILD_DIR / "m68k_assembler_app.exe"
GENAM_INCLUDE_DIR = Path(get_real_target_fixture("GenAm")["include_dir"])
BIN_GEN_INCLUDE_DIR = Path(get_real_target_fixture("BIN_GEN")["include_dir"])


class M68kSourceIncludeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        require_built_tools()
        cls.asm_exe = prepare_test_exe(ASM_EXE)

    def _render_source_text(self, source_text: str,
                            include_dir: Path) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            source_path = Path(tmp) / "render_probe.s"
            source_path.write_text(source_text, encoding="utf-8")
            return subprocess.run(
                [
                    str(self.asm_exe),
                    "render-source-file",
                    "--syntax",
                    "genam",
                    "--include-dir",
                    str(include_dir),
                    str(source_path),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_amiga_include_preprocessor_supports_exec_types_builtins(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            include_root = Path(tmp) / "include"
            exec_dir = include_root / "exec"
            exec_dir.mkdir(parents=True)
            (exec_dir / "types.i").write_text(
                (GENAM_INCLUDE_DIR / "exec" / "types.i").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (include_root / "custom_types.i").write_text(
                """\
INCLUDE "exec/types.i"

IFC '',''
EMPTY_OK SET 1
ENDC
IFNC 'LEFT','RIGHT'
DIFF_OK SET 2
ENDC

STRUCTURE Foo,0
    BYTE foo_b
    WORD foo_w
    ALIGNLONG
    APTR foo_p
    LABEL foo_SIZE
BITDEF FOO,BAR,3
""",
                encoding="utf-8",
            )
            render = self._render_source_text(
                """\
INCLUDE "custom_types.i"

    SECTION section,code
start:
    move.l #EMPTY_OK,d0
    move.l #DIFF_OK,d1
    move.l #foo_b,d2
    move.l #foo_w,d3
    move.l #foo_p,d4
    move.l #foo_SIZE,d5
    move.l #FOOB_BAR,d6
    move.l #FOOF_BAR,d7
    rts
""",
                include_root,
            )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$1,d0", render.stdout)
        self.assertIn("move.l #$2,d1", render.stdout)
        self.assertIn("move.l #$0,d2", render.stdout)
        self.assertIn("move.l #$1,d3", render.stdout)
        self.assertIn("move.l #$4,d4", render.stdout)
        self.assertIn("move.l #$8,d5", render.stdout)
        self.assertIn("move.l #$3,d6", render.stdout)
        self.assertIn("move.l #$8,d7", render.stdout)

    def test_amiga_include_preprocessor_supports_dos_i_structs_and_bitdefs(self) -> None:
        render = self._render_source_text(
            """\
INCLUDE "dos/dos.i"

    SECTION section,code
start:
    move.l #fib_Size,d0
    move.l #fib_DateStamp,d1
    move.l #fib_SIZEOF,d2
    move.l #id_VolumeNode,d3
    move.l #id_SIZEOF,d4
    move.l #FIBB_SCRIPT,d5
    move.l #FIBF_SCRIPT,d6
    move.l #TICKS_PER_SECOND,d7
    rts
""",
            GENAM_INCLUDE_DIR,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$7C,d0", render.stdout)
        self.assertIn("move.l #$84,d1", render.stdout)
        self.assertIn("move.l #$104,d2", render.stdout)
        self.assertIn("move.l #$1C,d3", render.stdout)
        self.assertIn("move.l #$24,d4", render.stdout)
        self.assertIn("move.l #$6,d5", render.stdout)
        self.assertIn("move.l #$40,d6", render.stdout)
        self.assertIn("move.l #$32,d7", render.stdout)

    def test_amiga_include_preprocessor_supports_angle_wrapped_struct_sizes(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            include_root = Path(tmp) / "include"
            include_root.mkdir(parents=True)
            (include_root / "angle_struct.i").write_text(
                """\
FIELD_MAX EQU 17
STRUCTURE Demo,0
    STRUCT demo_bits,<(FIELD_MAX+7)/8>
    ALIGNWORD
    LABEL Demo_SIZEOF
""",
                encoding="utf-8",
            )
            render = self._render_source_text(
                """\
INCLUDE "angle_struct.i"

    SECTION section,code
start:
    move.l #demo_bits,d0
    move.l #Demo_SIZEOF,d1
    rts
""",
                include_root,
            )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$0,d0", render.stdout)
        self.assertIn("move.l #$4,d1", render.stdout)

    def test_include_preprocessor_strips_inline_block_comments_from_constants(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            include_root = Path(tmp) / "include"
            include_root.mkdir(parents=True)
            (include_root / "block_comment.i").write_text(
                "MASK_VALUE EQU $3f\t      /* 2^6 -- 1 */\n",
                encoding="utf-8",
            )
            render = self._render_source_text(
                """\
INCLUDE "block_comment.i"

    SECTION section,code
start:
    move.l #MASK_VALUE,d0
    rts
""",
                include_root,
            )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$3F,d0", render.stdout)

    def test_amiga_include_preprocessor_supports_ifd_blocks(self) -> None:
        with tempfile.TemporaryDirectory(dir=BUILD_DIR) as tmp:
            include_root = Path(tmp) / "include"
            include_root.mkdir(parents=True)
            (include_root / "conditionals.i").write_text(
                """\
DEFINED_FLAG SET 1
    IFD DEFINED_FLAG
IFD_VALUE EQU $11
    ENDC
    IFND MISSING_FLAG
IFND_VALUE EQU $22
    ENDC
""",
                encoding="utf-8",
            )
            render = self._render_source_text(
                """\
INCLUDE "conditionals.i"

    SECTION section,code
start:
    move.l #IFD_VALUE,d0
    move.l #IFND_VALUE,d1
    rts
""",
                include_root,
            )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$11,d0", render.stdout)
        self.assertIn("move.l #$22,d1", render.stdout)

    def test_amiga_include_preprocessor_parses_dosextens_bptr_aliases(self) -> None:
        render = self._render_source_text(
            """\
INCLUDE "dos/dosextens.i"

    SECTION section,code
start:
    move.l #di_ResList,d0
    move.l #di_DevInfo,d1
    move.l #di_DevLock,d2
    move.l #fh_Arg1,d3
    move.l #cli_SetName,d4
    move.l #fl_Volume,d5
    move.l #fl_SIZEOF,d6
    rts
""",
            GENAM_INCLUDE_DIR,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$0,d0", render.stdout)
        self.assertIn("move.l #$4,d1", render.stdout)
        self.assertIn("move.l #$14,d2", render.stdout)
        self.assertIn("move.l #$24,d3", render.stdout)
        self.assertIn("move.l #$4,d4", render.stdout)
        self.assertIn("move.l #$10,d5", render.stdout)
        self.assertIn("move.l #$14,d6", render.stdout)

    def test_amiga_include_preprocessor_allows_case_distinct_symbols(self) -> None:
        render = self._render_source_text(
            """\
INCLUDE "intuition/screens.i"

    SECTION section,code
start:
    move.l #DRI_VERSION,d0
    move.l #dri_Version,d1
    move.l #DETAILPEN,d2
    move.l #NUMDRIPENS,d3
    rts
""",
            GENAM_INCLUDE_DIR,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$1,d0", render.stdout)
        self.assertIn("move.l #$0,d1", render.stdout)
        self.assertIn("move.l #$0,d2", render.stdout)
        self.assertIn("move.l #$9,d3", render.stdout)

    def test_atari_include_preprocessor_supports_gemdos_equates(self) -> None:
        render = self._render_source_text(
            """\
INCLUDE "GEMDOS.I"

    SECTION section,code
start:
    move.l #p_term0,d0
    move.l #c_conout,d1
    move.l #p_pause,d2
    move.l #p_getegid,d3
    move.l #s_alert,d4
    move.l #EINVFN,d5
    rts
""",
            BIN_GEN_INCLUDE_DIR,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$0,d0", render.stdout)
        self.assertIn("move.l #$2,d1", render.stdout)
        self.assertIn("move.l #$121,d2", render.stdout)
        self.assertIn("move.l #$139,d3", render.stdout)
        self.assertIn("move.l #$13C,d4", render.stdout)
        self.assertIn("move.l #$FFFFFFE0,d5", render.stdout)

    def test_atari_include_preprocessor_supports_bios_equates(self) -> None:
        render = self._render_source_text(
            """\
INCLUDE "BIOS.I"

    SECTION section,code
start:
    move.l #getmpb,d0
    move.l #bconout,d1
    move.l #kbshift,d2
    rts
""",
            BIN_GEN_INCLUDE_DIR,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$0,d0", render.stdout)
        self.assertIn("move.l #$3,d1", render.stdout)
        self.assertIn("move.l #$B,d2", render.stdout)

    def test_atari_include_preprocessor_supports_xbios_equates_and_aliases(self) -> None:
        render = self._render_source_text(
            """\
INCLUDE "XBIOS.I"

    SECTION section,code
start:
    move.l #setscreen,d0
    move.l #vsetscreen,d1
    move.l #setpallete,d2
    move.l #setpalette,d3
    move.l #supexec,d4
    move.l #vsetmask,d5
    rts
""",
            BIN_GEN_INCLUDE_DIR,
        )
        self.assertEqual(render.returncode, 0, render.stderr)
        self.assertIn("move.l #$5,d0", render.stdout)
        self.assertIn("move.l #$5,d1", render.stdout)
        self.assertIn("move.l #$6,d2", render.stdout)
        self.assertIn("move.l #$6,d3", render.stdout)
        self.assertIn("move.l #$26,d4", render.stdout)
        self.assertIn("move.l #$96,d5", render.stdout)

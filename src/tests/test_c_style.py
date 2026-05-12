from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import textwrap
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "src" / "scripts" / "check_c_style.py"


def _load_checker_module():
    spec = importlib.util.spec_from_file_location("src_check_c_style_test", CHECKER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER_MODULE = _load_checker_module()


@dataclass
class CheckerResult:
    returncode: int
    stdout: str
    stderr: str = ""


class CStyleCheckerTests(unittest.TestCase):
    def _run_checker(self, source: str) -> CheckerResult:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.c"
            path.write_text(source, encoding="utf-8")
            issues = CHECKER_MODULE.check_file(path, CHECKER_MODULE.DEFAULT_LINE_LENGTH)
            return CheckerResult(0 if not issues else 1, "".join(issue + "\n" for issue in issues))

    def test_accepts_wrapped_signature_style(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(uint32_t a, uint32_t b,
                    size_t *out_index) {
                    uint32_t a_size = 0, b_size = 0, c_size = 0;
                    return (int)(a + b + (uint32_t)(out_index != 0));
                }
                """
            ).strip()
            + "\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_plain_long_types(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                static int demo(long value) {
                    return (int)value;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixed-width", result.stdout)

    def test_rejects_bad_multiline_signature_indent(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                static int demo(
                  uint32_t a, uint32_t b,
                    uint32_t c) {
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("multiline signature args must use 4-space indent", result.stdout)

    def test_rejects_standalone_closing_signature_line(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                static int demo(
                    uint32_t a, uint32_t b,
                    uint32_t c
                ) {
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("multiline signature continuation must preserve comma placement", result.stdout)

    def test_rejects_sparse_multiline_signature_wrap(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                static int demo(
                    uint32_t a,
                    uint32_t b,
                    uint32_t c,
                    uint32_t d) {
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wrap is too sparse", result.stdout)

    def test_rejects_empty_opening_signature_line(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                static int demo(
                    uint32_t a, uint32_t b,
                    uint32_t c) {
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("opening signature line is too sparse", result.stdout)

    def test_rejects_tall_local_declaration_block(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>
                #include <stddef.h>

                static int demo(void) {
                    uint32_t a = 0;
                    uint32_t b = 0;
                    uint32_t c = 0;
                    uint32_t d = 0;
                    uint32_t e = 0;
                    uint32_t f = 0;
                    return (int)(a + b + c + d + e + f);
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("declaration block is too tall", result.stdout)

    def test_rejects_unnecessary_multiline_call_wrap(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdlib.h>

                static void demo(char **ptr) {
                    char *copy = realloc(
                        *ptr,
                        64);
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("multiline call wrap is unnecessary", result.stdout)

    def test_accepts_dense_multiline_call_wrap(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(uint32_t very_long_argument_name_a, uint32_t very_long_argument_name_b,
                    uint32_t very_long_argument_name_c, uint32_t very_long_argument_name_d) {
                    if (other_call(very_long_argument_name_a, very_long_argument_name_b,
                            very_long_argument_name_c, very_long_argument_name_d) != 0) {
                        return -1;
                    }
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_multiline_printf_with_string_literal_continuation(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdio.h>

                static int demo(unsigned value_a, unsigned value_b) {
                    printf("prefix:%u,"
                        "\"more\":%u",
                        value_a,
                        value_b);
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_sparse_multiline_call_wrap(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(uint32_t very_long_argument_name_a, uint32_t very_long_argument_name_b,
                    uint32_t very_long_argument_name_c, uint32_t very_long_argument_name_d) {
                    if (other_call(
                            very_long_argument_name_a,
                            very_long_argument_name_b,
                            very_long_argument_name_c,
                            very_long_argument_name_d) != 0) {
                        return -1;
                    }
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("multiline call wrap is too sparse", result.stdout)

    def test_rejects_under_indented_multiline_call_continuation(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(uint32_t very_long_argument_name_a, uint32_t very_long_argument_name_b,
                    uint32_t very_long_argument_name_c, uint32_t very_long_argument_name_d) {
if (other_call(very_long_argument_name_a, very_long_argument_name_b,
        very_long_argument_name_c, very_long_argument_name_d) != 0) {
                        return -1;
                    }
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("multiline call continuation must stay indented", result.stdout)

    def test_rejects_standalone_closing_multiline_call_line(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(uint32_t very_long_argument_name_a, uint32_t very_long_argument_name_b,
                    uint32_t very_long_argument_name_c, uint32_t very_long_argument_name_d) {
                    if (other_call(
                            very_long_argument_name_a, very_long_argument_name_b,
                            very_long_argument_name_c, very_long_argument_name_d
                        ) != 0) {
                        return -1;
                    }
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("closing ')' must stay on the last call line", result.stdout)

    def test_rejects_unindented_wrapped_boolean_continuation(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(const uint8_t *buffer) {
                    if (buffer[0] != 0
|| buffer[1] != 0) {
                        return 1;
                    }
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wrapped boolean continuation must stay indented", result.stdout)

    def test_ignores_comment_and_string_content_for_integer_type_check(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stdint.h>

                static int demo(uint32_t value) {
                    const char *text = "unsigned long in a string";
                    /* long in a comment should not trip the checker */
                    if (value != 0) return 1;
                    return 0;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_single_clause_if_on_one_line(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stddef.h>

                static int demo(const void *info) {
                    if (info == NULL) return 0;
                    return 1;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_gratuitous_three_line_single_clause_if(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stddef.h>

                static int demo(const void *info) {
                    if (info == NULL) {
                        return 0;
                    }
                    return 1;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_gratuitous_three_line_single_clause_if_else(self) -> None:
        result = self._run_checker(
            textwrap.dedent(
                """
                #include <stddef.h>

                static int demo(int value) {
                    if (value != 0) {
                        value = 1;
                    } else {
                        value = 0;
                    }
                    return value;
                }
                """
            ).strip()
            + "\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("single-clause if/else should stay compact", result.stdout)

    def test_repo_selected_c_files_pass_style_check(self) -> None:
        paths = CHECKER_MODULE._iter_default_paths()
        failures = []
        for path in paths:
            issues = CHECKER_MODULE.check_file(path, CHECKER_MODULE.DEFAULT_LINE_LENGTH)
            if issues:
                failures.append("".join(issue + "\n" for issue in issues))
        self.assertEqual(failures, [], "".join(failures))

    def test_rejects_raw_allocation_in_migrated_source_model(self) -> None:
        original_guards = CHECKER_MODULE.SOURCE_MODEL_RAW_ALLOCATION_GUARDS
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m68k_source_model.c"
            path.write_text("static void guard_probe(void) { free(0); }\n", encoding="utf-8")
            CHECKER_MODULE.SOURCE_MODEL_RAW_ALLOCATION_GUARDS = {path.resolve()}
            issues = CHECKER_MODULE.check_file(path, CHECKER_MODULE.DEFAULT_LINE_LENGTH)
            CHECKER_MODULE.SOURCE_MODEL_RAW_ALLOCATION_GUARDS = original_guards
        self.assertTrue(any("Result Arena allocation" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()


def load_tests(loader, tests, pattern):
    if os.environ.get("AMIGA_INCLUDE_EXPLICIT_TESTS") == "1":
        return tests
    suite = unittest.TestSuite()

    def append_filtered(test):
        if isinstance(test, unittest.TestSuite):
          for item in test:
            append_filtered(item)
          return
        if getattr(test, "_testMethodName", "") == "test_repo_selected_c_files_pass_style_check":
          return
        suite.addTest(test)

    append_filtered(tests)
    return suite

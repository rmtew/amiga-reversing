"""Manual presentation facts grow without losing native metadata or source bytes."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path, count):
    if not (ROOT / "src/build/platform_file_lib.dll").exists():
        pytest.skip("native backend must be built")
    original = bytes.fromhex("4e75") + bytes((index * 19 + 3) % 256 for index in range(count * 2))
    binary = tmp_path / "representations.bin"
    binary.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY, path=binary, address_model=RawAddressModel.LOCAL_OFFSET,
        load_address=0, entrypoint=0, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path / "analysis",
    )
    metadata = tmp_path / "metadata.json"
    entries = [{"hunk": 0, "addr": 2 + index * 2, "end": 4 + index * 2, "style": "hex"}
               for index in range(count)]
    metadata.write_text(json.dumps({"target_type": "raw_binary", "manual_representations": entries}))
    return source, metadata, entries, original


def policy(source, metadata):
    return c_backend.effective_policy_project_source_with_c_backend(source, metadata_path=metadata)["analysis_policy"]


def test_more_than_inline_and_previous_limit_renders_losslessly_and_exact(tmp_path):
    source, metadata, entries, original = fixture(tmp_path, 160)
    exported = policy(source, metadata)
    assert exported["manual_representation_count"] == 160
    assert [(e["section_index"], e["offset"], e["size"], e["style"]) for e in exported["manual_representations"]] == [
        (0, e["addr"], 2, "hex") for e in entries
    ]
    text = c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)
    assert "$" in text
    rebuilt, _profile = c_backend.assemble_platform_source_text_with_c_backend("amiga-raw", text)
    assert rebuilt == original
    vasm = ROOT / "ext/vasm/vasmm68k_mot"
    if not vasm.exists():
        pytest.skip("native vasm must be built for independent source verification")
    assembly = tmp_path / "source.s"
    assembly.write_text(text, encoding="ascii")
    output = tmp_path / "rebuilt.bin"
    result = subprocess.run([str(vasm), "-quiet", "-Fbin", "-m68000", "-o", str(output), str(assembly)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert output.read_bytes() == original


def test_representation_capacity_duplicates_and_conflicts(tmp_path):
    source, metadata, entries, _original = fixture(tmp_path, 4096)
    metadata.write_text(json.dumps({"manual_representations": entries + [entries[0]]}))
    assert policy(source, metadata)["manual_representation_count"] == 4096
    metadata.write_text(json.dumps({"manual_representations": entries + [{**entries[0], "style": "decimal"}]}))
    with pytest.raises(RuntimeError, match="manual representation"):
        policy(source, metadata)
    metadata.write_text(json.dumps({"manual_representations": entries + [{"hunk": 0, "addr": 0, "end": 2, "style": "hex"}]}))
    with pytest.raises(RuntimeError, match="manual representation"):
        policy(source, metadata)


def test_representation_out_of_range_is_refused(tmp_path):
    source, metadata, entries, _original = fixture(tmp_path, 160)
    entries[-1]["end"] = 99999
    metadata.write_text(json.dumps({"manual_representations": entries}))
    with pytest.raises(RuntimeError, match="out of range|range exceeds"):
        c_backend.render_project_source_with_c_backend(source, metadata_path=metadata)


def test_native_allocation_failure_preserves_policy_and_cleans_copy(tmp_path):
    """Interpose allocation in a separate Linux process without production hooks."""
    import shutil
    import sys

    compiler = shutil.which("cc")
    if sys.platform != "linux" or compiler is None:
        pytest.skip("allocation interposition uses the Linux host C toolchain")
    driver = tmp_path / "failure.c"
    driver.write_text(r'''
#include "m68k_ir.h"
#include <dlfcn.h>
#include <stdlib.h>
static int fail_after = -1;
static int outstanding;
static void *tracked[8];
void *calloc(size_t count, size_t size) {
  static void *(*real_calloc)(size_t, size_t);
  void *result;
  if (!real_calloc) real_calloc = dlsym(RTLD_NEXT, "calloc");
  if (fail_after == 0) return NULL;
  if (fail_after > 0) --fail_after;
  result = real_calloc(count, size);
  if (result && fail_after >= 0) tracked[outstanding++] = result;
  return result;
}
void free(void *pointer) {
  static void (*real_free)(void *);
  int index;
  if (!real_free) real_free = dlsym(RTLD_NEXT, "free");
  for (index = 0; index < outstanding; ++index)
    if (tracked[index] == pointer) { tracked[index] = tracked[--outstanding]; break; }
  real_free(pointer);
}
int main(void) {
  M68kAnalysisPolicy source, copy = {0}, zero = {0};
  M68kAnalysisManualRepresentation *saved;
  m68k_analysis_policy_init_default(&source);
  if (m68k_analysis_policy_reserve_manual_representations(&source, 129)) return 1;
  source.manual_representation_count = 129;
  source.manual_representations[128].offset = 256;
  saved = source.manual_representations;
  fail_after = 0;
  if (m68k_analysis_policy_reserve_manual_representations(&source, 4096) != -1 ||
      source.manual_representations != saved || source.manual_representation_count != 129 ||
      source.manual_representations[128].offset != 256) return 2;
  if (m68k_analysis_policy_reserve_manual_representations(&zero, 129) != -1 ||
      zero.manual_representations || zero.manual_representation_capacity) return 3;
  fail_after = -1;
  if (m68k_analysis_policy_reserve_named_labels(&source, 5) ||
      m68k_analysis_policy_reserve_structured_data_items(&source, 5)) return 4;
  source.named_label_count = source.structured_data_item_count = 5;
  copy.max_cpu = 42;
  fail_after = 2; /* Earlier collections allocate, representation allocation fails. */
  if (m68k_analysis_policy_copy(&copy, &source) != -1 || copy.max_cpu != 42 ||
      copy.manual_representations || outstanding != 0) return 5;
  fail_after = -1;
  m68k_analysis_policy_destroy(&source);
  m68k_analysis_policy_destroy(&copy);
  m68k_analysis_policy_destroy(&zero);
  return 0;
}
''')
    executable = tmp_path / "failure"
    compiled = subprocess.run([
        compiler, "-std=c11", f"-I{ROOT / 'src'}", str(driver), f"-L{ROOT / 'src/build'}",
        "-lamiga_backend", "-ldl", "-Wl,--export-dynamic", f"-Wl,-rpath,{ROOT / 'src/build'}",
        "-o", str(executable),
    ], capture_output=True, text=True, timeout=30)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, (result.returncode, result.stderr)

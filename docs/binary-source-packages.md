# Binary asset source packages

Source export can place evidenced opaque bytes in deterministic files and emit
whole-file `INCBIN` references. This is an additive projection of the existing
native listing artifact, not a second renderer or an analysis pass. Plain source
exports, target facts and canonical listings are unchanged.

## Use

```sh
.venv/bin/python -m amiga_reversing.tools.source_export TARGET \
  --binary-assets --minimum-asset-size 256 --output export.zip --json
# Optional: existing reproduction and vasm oracle policies, full-file exactness only
.venv/bin/python -m amiga_reversing.tools.source_export TARGET \
  --binary-assets --output export.zip --verify-package --json
```

The existing UI Export Source choice grid has `vasm + binary assets (ZIP)`.
The existing HTTP source-export route accepts `binary_assets=true` and
`minimum_asset_size=256`; its JSON contains the package and a base64 ZIP download.
The shared restoration client routes its read-only `export` operation to that
same endpoint. CLI: `amiga-restoration --target TARGET export --binary-assets`.
MCP: `restoration_export(project, binary_assets=True)`. Export is not verification.
These adapters do not introduce a new restoration mutation or review operation.

Unzip into a fresh directory. The entry `.s`, its `assets/` files, literal SDK
INCLUDE dependencies and `manifest.json` travel together. Vasm must run with the
package directory as CWD, preventing unrelated CWD files from shadowing assets.
Internal C assembly uses `assemble_platform_source_path_with_c_backend`; assets
resolve from the source parent and SDK includes from the package root. There are
no absolute paths or timestamps in the archive. The source file remains at its
root; assets/includes can be nested.

## Eligibility and identity

Native exclusive `bitmap` and `sound_sample` roles are eligible. The size threshold
applies to adjacent native rows with matching section, region and classification.
Unknown bytes, executable statements, reserves/BSS, strings, palettes, sprite
control data, typed structures, pointer/lookup/audio tables, relocation overlaps
and all planned address expressions stay source. Numeric address expressions
also block extraction. Merely being large does not establish eligibility.

Classification remains a native analysis fact or accepted manual seed through
the existing action catalog. There is no force-by-size option that can bypass
code, typed-data or pointer protection. Labels, section/region boundaries,
directives and gaps stop coalescing. A row containing an interior label or an
unsupported layout remains source; adjacent safe runs may still export. A strict
numeric-directive layout check only rejects rows after native eligibility; it
never infers classification or byte boundaries from text.

Files use section/offset/size names. Original section storage supplies bytes,
not rendered numeric statements. Manifest entries retain section/offset, native
role, row provenance, length and SHA-256. The manifest also binds source bytes,
SDK dependencies, original binary identity, metadata hash and export policy.
Its canonical SHA-256 is the package identity and is stored in the ZIP comment.
Hashes detect changes; they are not signatures or proof that classifications
are semantically correct.

The public artifact is a single deterministic ZIP, so regeneration cannot leave
obsolete asset files beside the new source. It atomically replaces only an intact
generated archive. Modified source, asset, manifest, extra files or unrelated
output cause refusal and preserve the existing artifact; choose a fresh output
name. Verification stages a fresh package, validates all bytes before assembly,
and keeps immutable content-addressed evidence under `bin/rebuilt/`. Reusing
modified evidence is refused. As with ordinary filesystem operations, this is
not a sandbox against concurrent hostile filesystem mutation.

## Compatibility and limits

See [directive conformance](source-package-dialect-conformance.md) for primary
references and measured vasm/default versus vasm `-devpac` behavior.

* Packages currently require the vasm profile. Plain Devpac export remains
  supported. Actual Amiga GenAm 3.18 and `vamos` are absent; no native Devpac
  compatibility claim is made. Historical Devpac INCBIN alignment differs from
  vasm's compatibility mode.
* The C core supports whole-file INCBIN with double/single-quoted relative names,
  including spaces/commas, mixed directive case and empty files. It rejects
  offset/length operands explicitly. Vasm's range and search extensions are
  characterized, not claimed as implemented. Export uses exact slices instead.
* Source-package paths use an ASCII portable subset; unsafe/traversal/absolute,
  case-colliding, reserved, ancestor-colliding and symlink output paths are refused.
* Literal double-quoted SDK INCLUDE dependencies are collected recursively from
  the configured platform include root and hashed into the package. Dynamic
  INCLUDE names are refused. Broad assembler macro/include semantics remain the
  existing assembler's responsibility.
* Existing vasm oracle container policy is unchanged. For Amiga HUNK fixtures
  with long relocation records, `-kick1hunks` is required for full-file equality;
  default vasm may choose short relocation records and yield content equality.
  `--verify-package` honestly reports this existing distinction and exits 3
  unless both complete files match; it does not silently normalize containers.
* Complex interior-label rows may limit savings. Canonical inline listings and
  source-only exports stay available for inspection.

## Evidence and reproduction

Synthetic native integration: a 17,284-byte hunk program containing code, two
bitmap regions, a sample, palette, relocation-bearing pointer table, interior
label and unknown potential-pointer data. Two eligible assets total 8,704 bytes.
Source falls **60,329 → 24,603 bytes (59.2%)**. The interior-label region, palette,
pointer table, unknown bytes and code remain visible. Internal C and actual
vasm (`-Fhunkexe -kick1hunks -no-opt -nosym`) each match the complete original.
The tests also move a package with nested SDK dependencies away from the SDK and
compare raw output with both assemblers. No original target binary was modified.

```sh
make -j4
make -C ext/vasm CPU=m68k SYNTAX=mot -j4
cp ext/vasm/vasmm68k_mot tools/vasmm68k_mot.exe
.venv/bin/python -m pytest -q -s tests/test_source_package_integration.py
.venv/bin/python -m pytest -q tests/test_source_package.py \
  tests/test_source_package_interfaces.py tests/test_source_export.py \
  tests/test_incbin_assembler.py tests/test_incbin_oracle_conformance.py \
  tests/test_reproduction.py tests/test_oracle_compatibility.py
src/build/m68k_c_unit_tests.exe
```

Implementation validation: native package suite 5/5, IR suite 637/637; independent
review's focused package/parser/oracle/reproduction run 118 passed. The full Python
suite: **1,581 passed, 66 skipped, 355 deselected, one known failure** reading absent
`resources/platform_macos/MPW-GM.img.bin`. The C runner has the existing external
provider failure `decompression_identify_reports_unknown_payload_without_failure`.
These are recorded in the Linux baseline and separated from introduced failures.
Targeted Ruff/mypy, JavaScript syntax and diff checks pass. No repository CI
workflow is configured; Windows compilation is updated but not executed here.

A bounded check of existing target metadata found no accepted bitmap/sample roles.
Therefore no target-specific savings are claimed. The primary reversing task can
measure savings after accepting genuine native asset facts; this task does not
invent classifications, change Pandora facts, modify ctennis or download extra
proprietary tools/data. Parent coordination owns merge and primary adoption.

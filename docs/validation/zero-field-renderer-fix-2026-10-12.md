# Typed zero-offset fields: exact external assembly

Original address-register indirect operands now render as `(An)`, with the
meaningful structure field retained in an operand annotation and the structured
symbol-access record (`comment_only`). An original explicitly encoded d16 zero
still renders as `field.w(An)`; nonzero field displacements remain symbolic.
No target facts, queue behavior, emulator control, or internal assembler
normalization rules changed.

The earlier behavior was intentional in commit
`6cb75dddb7f2c34151528723731b3277a38bf913`: the C assembler normalizes an
unqualified symbolic zero displacement to indirect addressing. vasm with
`-no-opt` instead preserves a displacement word. Internal roundtrips therefore
missed the external mismatch. Seven Pandora operands each added two bytes,
moving subsequent labels; the first binary difference at `0x497` was an earlier
reference to such a moved label, not the root cause.

## Verification

From the repository root:

```sh
make -j4
.venv/bin/python -m pytest tests/test_zero_field_encoding.py -q
src/build/m68k_c_unit_tests.exe
```

- Six focused fixtures pass through the real renderer and both the C assembler
  and vasm `-no-opt`: source and destination operands, bare indirect, explicit
  zero displacement, and nonzero displacement. Before the fix, the two bare
  indirect fixtures failed.
- Native suite: 772 passed (including 635 IR tests); the existing Ancient
  provider identification failure remains. This is not a clean full-suite claim.
- Independent review reran the six fixtures, checked the full binary equality,
  and found no blocking issues.

Fresh Pandora reproduction used the official rendering entry point:

```sh
TARGET=amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
SOURCE=targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8/pandora_3e1ee0f1_bk_00_000000e8.s
OUT=.runtime-state/zero-field-fix
mkdir -p "$OUT"
.venv/bin/python -m amiga_reversing.tools.rendered_source_roundtrip_report \
  --target "$TARGET" --update-rendered-source \
  --report-path "$OUT/framework-reproduction.json" --json
cp "$SOURCE" "$OUT/pandora.s"
tools/vasmm68k_mot.exe -Fbin -m68000 -no-opt -quiet -nosym \
  -Iext/amiga_includes/ndk_2.0/include \
  -o "$OUT/pandora-rebuilt.bin" "$OUT/pandora.s"
cmp "${SOURCE%/*}/binary.bin" "$OUT/pandora-rebuilt.bin"
sha256sum "$OUT/pandora-rebuilt.bin"
```

The rendering command generates fresh source but reports `assembler_error` for
its subsequent full-target C assembly: the existing include loader joins paths
with a Windows backslash on Linux (`src/m68k_source_include.c`). That separate
limitation remains; the six include-free C fixtures do pass. Actual external
assembly above succeeds: **376832 bytes**, byte-for-byte identical, SHA256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
No instruction or data was manually patched; only line endings were normalized.

The fresh source is retained locally with the receipts. Compared with a fresh
pre-fix render, exactly seven instruction lines change. The tracked generated
source was restored after validation because it also contains older projection
drift unrelated to this fix; committing that refresh would introduce unrelated
queue/display changes. Regenerate using the command above to obtain the fixed
source. The original payload and manual actions remain untouched.

## Rebuilt execution

The newly assembled file was passed to `build_boot_adf` and
`HeadlessCopperlineSession` using the existing `pandora` contract, the existing
compiled gameplay scenario, Copperline 1.0.0, and the user-supplied Kickstart
34.5 ROM described in [the runtime guide](../copperline-runtime.md). The full
rebuilt payload passed contract validation and handoff verification. Result:
`ok`, with all four phases hit:

| Phase | PC |
| --- | --- |
| Title/menu | `0x10ba8` |
| UI initialization | `0x1079e` |
| Gameplay | `0x105d6` |
| Inventory input handler | `0x128d4` |

Local receipts are `.runtime-state/zero-field-fix/{pandora.s,
vasm-reproduction.json,copperline.json,compiled-gameplay.json,verify_copperline.py}`.
The bounded runtime check can be repeated in this saved environment with
`PYTHONPATH=. .venv/bin/python .runtime-state/zero-field-fix/verify_copperline.py`.
It uses the rebuilt file, not a substituted original. The emulator exited after
the check. No queue correction was made or claimed, and original-loader parity
is outside this verification.

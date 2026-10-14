# Narrow prevention of premature absolute-code promotion

The source-only root containing Pandora caller `0x896C` acquired an inferred
numeric runtime address and prematurely accepted source `0x3D310` as code. A
later copied view changed the final address lookup to source `0x4D310`, without
establishing execution of either body. The approved fix prevents that premature
promotion; it does not implement complete copied-code reconciliation.

The active native change is 66 additions and seven deletions in one file. One
internal entry-lineage flag distinguishes uniquely established initial/runtime
entries from source-only roots. Numeric fallthrough addresses do not establish
lineage. Unphased absolute and runtime-derived control promotion is refused in
nonidentity executable policy domains. Explicit source seeds, source-relative
targets, indexed source dispatch and relocations retain their existing paths.
Pointer-only views do not become executable policy ranges. No public ABI,
copy-history, return-state, replay-generation or pruning model was added.

The unapproved 900-addition experiment is preserved locally under
`.runtime-state/pandora-analysis/failed-copy-context-experiment/`: a recoverable
tracked-source patch, all seven source/test files, a hash manifest and 21 isolated
build/test evidence files. The working source was reset to verified commit
`da5a10df94fdf2856b87f6dc60a2682470ffe676` before implementing the smaller fix.
Pandora's original binary, accepted Manual Action Log, Decision Journal and
project metadata hashes were unchanged. The reviewed scene/audio ZIP was retained.

## Verification

Independent implementation review approved this narrowed scope. The focused
native fixture passed 11 cases, including unphased refusal, established entry,
identity/pointer-only mappings, PC-relative and source-register paths, source
indexed stubs, runtime-entry ambiguity, and Hunk relocation. Nine outputs also
passed native C and independent vasm full-byte reconstruction. The direct native
IR suite passed all 638 cases; unrelated provider/default suites were not rerun.

One frozen Pandora artifact supplied both the scoped inspection and source for
the isolated full C/vasm proof. Both outputs equal all 376,832 original bytes,
SHA256 `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
Source SHA256:
`d6b6f240346ca74ff7867ef97799c1c373666d55823db215e951627a8184fe85`.
Isolated backend SHA256:
`c269dfa09c10e538fb0fe4435437b5a6a8210020102cd76b2bf124b06c7a4b5f`.
The independent reviewer checked both output files, source/backend/metadata
hashes and unchanged target histories. Evidence is in
`.runtime-state/pandora-analysis/entry-lineage-gate/receipt.json` and
`scoped-native-result.json`; no full analysis JSON or instruction trace was saved.

Source `0x896C` remains accepted, while `0x3D310` and `0x4D310` are unaccepted.
The existing final address lookup still records `0x4D310`, but its CFG target
block is unresolved (`UINT32_MAX`); this is not accepted helper execution.
Neither disputed body nor its overlapping resource banks was reclassified.

After this gate, the owned service was stopped for one production build and
restarted on `http://127.0.0.1:8123/` (PID 39298, HTTP 200). All four library
aliases resolve to the rebuilt backend. The production build hash is
`defcd54a5279798a4d04919030f82ba0892c0b589f9427c67ae92b6aabbbf911`.
The production backend was compiled separately from the isolated build.
Service/build evidence is beside the gate receipt.

```sh
make -j4
.venv/bin/python -m pytest tests/test_native_entry_lineage.py -q
printf '%s\n' 'int m68k_c_ir_tests(void);' \
  'int main(void) { return m68k_c_ir_tests(); }' > /tmp/pandora-ir-main.c
cc /tmp/pandora-ir-main.c src/build/linux/test_m68k_ir.o \
  src/build/linux/m68k_c_unit_test.o src/build/libamiga_backend.so \
  -Wl,-rpath,"$PWD/src/build" -o /tmp/pandora-ir-suite
/tmp/pandora-ir-suite
.venv/bin/python -m amiga_reversing.tools.rendered_source_roundtrip_report \
  --target amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8 \
  --update-rendered-source --no-write-report --json
```

The last command is a future reproduction command, not an additional run used
for this gate. The original UI/package/gameplay receipts remain valid for their
recorded inputs; they are not claims about alternate layouts.

## Explicit limitations

Copy-helper returns, temporal overwrites, copy completion and stale-code support
withdrawal remain unsupported. An established path arriving after a source
instruction was already accepted may not be replayed, so a genuine helper can
remain unresolved. The existing coordinate resolver is not a complete phase or
memory-content model. No general correctness, full restoration or relocatability
claim follows from this fix. The earlier 76.42% ownership map is a pre-fix
snapshot, not a freshly recomputed current percentage. Independent text/audio
restoration can proceed; disputed code/resource intervals remain excluded.

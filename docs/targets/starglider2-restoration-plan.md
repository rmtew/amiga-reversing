# Starglider II: original source restoration

Goal: readable canonical original assembly and assets, rebuilding the absolute
412736-byte raw image. This is not relocation, an AmigaDOS replacement, or a
claim of complete gameplay/hardware equivalence.

## Current validated baseline

Current validated export: 3514 app references, 2802 typed accesses, 175 unresolved
accesses; 9951 unclassified bytes in 279 intervals. These are analysis counts,
not semantic completion percentages. Sparse inventory/ingredient layouts project
39 additional accesses. The 25 new diagnostics expose dynamic counter indexes;
all 150 prior unresolved accesses and prior typed facts are retained.
Original payload SHA256:
`662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9`.

## Active queue

1. Exact tag stores, bounded MOVEM cursors and opaque leading-record address
   identities are supported. Undeclared prefix bytes retain no field meaning.
   Next: stored-pointer lifetime in item 2; do not add per-reader type seeds
   or assume disjoint allocations.
2. Player rotation stores use a three-field type-30 format contract and decoded
   LEA/write-disjointness proof. The slot already declares SG2WorldObject;
   adding another pointee annotation would duplicate existing semantic input.
   Final caller-flow tracing identifies the APP write barrier at all three
   stronger-base readers (3C40, BA96, BE1A), despite retained workspace identity.
   Structural upstream paths include barrier transitions at the initial
   diagnostic write at 1064 and bus/address-error hex-writer calls at C62E/C66C;
   this is not a normal-game reachability witness. Those handlers can resume
   gameplay. The helper preserves A6 but has unknown memory/escape effects;
   register preservation does not establish live-slot preservation. A6 fallback
   alone does not reproduce the loss; the same straight-line reader works.
   Copy/rebase accepts other record tags from supplied saved state without format
   validation; this neither disproves the conditional role declaration nor proves
   a permanent subtype. Next: test call-site write footprints with proved
   workspace/buffer/stack separation and constructor slot postconditions,
   retaining unknown-alias and exception-resume refusals. Current summaries
   cannot supply that separation; no reader seed or unconditional type follows.
3. Optional model-header extension: keep face-count mutation separate from
   the format discriminator. The original viewer can select outside the
   104-entry model prefix. Next: isolate an evidenced caller domain and its
   writes; neither initial bytes nor directory length supply that invariant.
4. Indexed accesses: register guards now retain signed/unsigned WORD bounds,
   including existing direct-call preservation effects. Memory cells retain
   bits only. The scan mask admits eight offsets for seven stored pointers;
   its countdown needs a writer/entry bound. The eight audio-ring reads also
   need an entry invariant: equality-only wrapping does not bound arbitrary
   initial cursors. Literal/copy/equality index probes already resolve fields.
   Counter readers lose BYTE-directory values before AND #255; the 104-byte
   backing supplies no value bound. Next: a bounded BYTE-value transfer probe
   with mutation/unknown-call refusals, then actual directory-write preservation.
   Do not enlarge a directory or assume original bytes persist.
5. Residual regions: prioritize accepted data readers and incoming code edges.
   Do not decode apparent instructions or declare arrays from plausible bytes.
   Zero-fill writers and write-only app flags do not establish field purpose.
   The debug-key99 toggle has no static reader; the viewer auxiliary WORD has
   no known producer or role. Next: targeted read/write observation during
   debug/model-viewer input, rather than speculative names.

## Evidence and limits

Canonical inputs and decisions remain in `target_metadata.json`,
`manual_actions.jsonl`, and `decision_journal.jsonl`. Reproducible regressions
live in `tests/test_starglider2_*.py` and the shared analysis tests. Retain
[normal-input flight evidence](../../runtime/observations/starglider2-flight-input-evidence.json)
and [memory-span evidence](../../runtime/observations/starglider2-app-memory-spans.json).
Detailed prior investigations remain in Git history through `c8e6fe1a`; this
file is the current queue, not an append-only batch log.

Exact C/vasm and clean standalone rebuilding are required at coherent output
checkpoints. Run focused fixtures while iterating; broaden tests for changed
shared behavior. `python targets/amiga_raw_starglider2_game/build.py --vasm <vasm>`
rebuilds the exported source independently. Keep checksums/backend/receipt
identities in export provenance, not duplicated progress narratives.

Normal-input flight and finite CPU fixtures cover their observed paths only.
Physical disk/DMA/audio delivery, full alternate-platform startup, arbitrary
save/restore inputs, queue lifetimes and complete gameplay remain unqualified.
The wider HUNK regression
`test_real_dll_data_block_custom_struct_unaligned_repeated_field_reassembles`
was reproduced before these raw-target changes; its pointer relocation/address
semantics require a separate repair, not a changed expected byte sequence.

# Starglider II: original source restoration

Goal: readable canonical original assembly and assets, rebuilding the absolute
412736-byte raw image. This is not relocation, an AmigaDOS replacement, or a
claim of complete gameplay/hardware equivalence.

## Current validated baseline

Current validated export: 3514 app references, 2754 typed accesses, 153 unresolved
accesses; 9967 unclassified bytes in 279 intervals. These are analysis counts,
not semantic completion percentages. The 108 corrected inline-member catalogue
names exposed existing source knowledge; they did not resolve typed accesses.
Original payload SHA256:
`662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9`.

## Active queue

1. Exact tag stores and bounded MOVEM cursors are supported. MOVEM recovers
   three original state-frame accesses, with no old typed access lost. Known
   tag-store gains are fixture-only so far. Next: the publication barrier in
   item 2; do not add per-reader type seeds or assume disjoint allocations.
2. Player rotation writes: trace the type-30 constructor through publication
   of `player_object_reference`. Current A6 app coordinates are fallback
   interpretations, insufficient for a disjoint-write proof. Next experiment:
   a real caller/entry identity, or a qualified canonical cell identity; do not
   promote a new layout solely to reduce the unresolved count.
3. Optional model-header extension: keep face-count mutation separate from
   the format discriminator. The original viewer can select outside the
   104-entry model prefix. Next: isolate an evidenced caller domain and its
   writes; neither initial bytes nor directory length supply that invariant.
4. Indexed accesses: register guards now retain signed/unsigned WORD bounds,
   including existing direct-call preservation effects. Memory cells retain
   bits only. The scan mask admits eight offsets for seven stored pointers;
   its countdown needs a writer/entry bound. The eight audio-ring reads also
   need an entry invariant: equality-only wrapping does not bound arbitrary
   initial cursors. Do not enlarge a directory or assume original bytes persist.
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

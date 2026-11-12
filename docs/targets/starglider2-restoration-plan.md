# Starglider II: original source restoration

Goal: readable canonical original assembly and assets, rebuilding the absolute
412736-byte raw image. This is not relocation, an AmigaDOS replacement, or a
claim of complete gameplay/hardware equivalence.

## Current validated baseline

Current validated export: 3517 app references, 2813 typed accesses, 183 unresolved
accesses; 9839 unclassified bytes in 276 intervals. These are analysis counts,
not semantic completion percentages. The phrase-counter
references retain declared-layout A6 fallback; the role declaration adds no
stronger base proof. The projector report arrays expose three additional
dynamic-index reads; all prior typed/unresolved facts are retained.
The scalar object-type domain exposes constructors, collision exclusions and
eighteen choice/cycle/drop/trade/ingredient/projector/spawn tables (290 stored IDs).
Grouped tables retain native
count/stride; their symbols and one role per visible run remain readable.
This is semantic presentation, not a value/lifetime bound. Directory placeholders
and unsupported IDs remain numeric; zero is named only as an absence marker.
The bounded pirate-drop read is recovered automatically; the retirement-table
read still needs a cursor invariant. All prior app and field attributions remain.
Four trade/ingredient/projector directories expose another 82 stored object IDs;
three bounded ingredient reads resolve. Six newly exposed trade/projector/read
sites remain unresolved; none of the prior 179 unresolved records were lost.
Five bounded spawn/drop readers resolve; primary/secondary update references
now name 38 accepted dispatch tails and 38 JMP bridges to already known bodies.
These names add no code, target-set completeness or lifetime proof; original
diagnostic stores and register/stack effects remain intact.
Five remaining generated-name entry candidates now have local roles, backed by
37 CPU cases. Their ambiguous CFG ownership remains unchanged; numeric record
operands remain where native pointer context does not establish a field view.
Airborne launch names its WORD+$26 proximity-response countdown. BYTE+$29
remains unknown; ground $AA64 at +$28 is separate from Tank WORD+$26.
Original payload SHA256:
`662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9`.

## Active queue

1. Exact tag stores, bounded MOVEM cursors and opaque leading-record address
   identities are supported. Undeclared prefix bytes retain no field meaning.
   Next: stored-pointer lifetime in item 2; do not add per-reader type seeds
   or assume disjoint allocations.
   Of 60 Core gaps, 33 are LONG zeroing stores spanning multiple fields in
   three 68-byte clears. Other Core bytes are polymorphic: rotations overlap
   spheroid colour/delay state. Do not widen Core to WorldObject; obtain a
   specific tagged or caller context for the remaining role interpretations.
2. Player rotation stores use a three-field type-30 format contract and decoded
   LEA/write-disjointness proof. The slot already declares SG2WorldObject;
   adding another pointee annotation would duplicate existing semantic input.
   Final caller-flow tracing identifies the APP write barrier at all three
   stronger-base readers (3C40, BA96, BE1A), despite retained workspace identity.
   Structural upstream paths include barrier transitions at the initial
   diagnostic write at 1064 and bus/address-error hex-writer calls at C62E/C66C;
   this is not a normal-game reachability witness. Those handlers can resume
   gameplay. The helper preserves A6 but has unknown memory/escape effects;
   register preservation does not establish live-slot preservation. Callable
   write subjects retain complete An/Dn entry identities after lossless copies;
   this supplies no allocation-separation or stored-pointer lifetime proof. A6 fallback
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
   initial cursors. The pirate-drop read now uses `bounded_cfg_mask`: AND15
   stays within its 16-record BYTE array, without enumerating a larger finite
   set. The shared proof checks fixed record residues and complete field/owner
   coverage; arbitrary residues and negative/modular domains remain outside this
   lane. Retirement still reads its cursor before wrapping; naming its 32 stored
   IDs adds no caller bound. Its direct references show only the increment and
   mask writers; the original image seeds zero and the inspected game resets do
   not reset it. This absolute cell is outside the saved app prefix, but a
   supplied serialized free slot rebases to it without a pool-range check.
   Original encounter pop/type-store instructions then write above 31. Thus no
   arbitrary-restored-state bound holds. Next: a validated-pool caller context
   (or a context excluding unvalidated load) is required; ordinary-save
   reachability is not established by the local counterexample.
   Literal/copy/equality index probes already resolve fields.
   Zero-extended BYTE loads now retain intrinsic 0..255 WORD bounds; complete
   plain-WORD owners can expose scalar table consumers without losing ownership.
   This supplies the disk encoder's even 0..510 lookup, not directory contents.
   Ingredient loops retain 0..7, but their loaded IDs still need a specific
   writer/entry domain for the 104-entry inventory; preserve alias and call refusals.
   Do not enlarge a directory or assume original bytes persist: the shared
   heat/pressure notice WORD overwrites secondary spheroid colour bytes30/31.
   Indexed field display now transports explicit scalar EQU identities; missing
   identity retains the raw displacement with a resolved-field annotation.
   Projector report selection uses two stored 56-pointer arrays. Local supplied
   cases cover all slots and the four-attempt retreat/wrap; the first candidate
   is read before that retreat. Supplied cursor56 reads past both tables;
   $4000 wraps the WORD index to zero and $FFFF indexes four bytes before them.
   Save/restore copies app+$6B4..+$6598, including cursor+$858, without validating
   that value. Next: establish a specific validated-state caller context; ordinary
   initialization/decrement/wrap and table extent alone cannot supply the bound.
5. Residual regions: prioritize accepted data readers and incoming code edges.
   Incoming-reference review separates address formation from actual memory
   effects. Some named globals lack backing declarations; investigate connected
   record roles/extents while protecting runtime namespaces, code and views.
   Nominal address-formation width or scalar formatting supplies no owner.
   Do not decode apparent instructions or declare arrays from plausible bytes.
   Zero-fill writers and write-only app flags do not establish field purpose.
   The four-frame normal-flight coverage probe retired 40,053 instructions at
   3,474 canonical starts; no missing start was observed. Raw $553E..$57F4 and
   $B9B8..$BB80 matched original bytes, had no writes and did not execute in
   this window. This does not establish dead code or qualify other paths.
   The debug-key99 toggle has no static reader; the viewer auxiliary WORD has
   no known producer or role. Normal Painting entry was reached with debug
   cleared; a 120-frame CPU watch saw no auxiliary read with key8 held through
   that window. Next: identify a real writer or a normal debug-enabled viewer
   context before another probe; the default Painting reset clears the guard.

## Evidence and limits

Canonical inputs and decisions remain in `target_metadata.json`,
`manual_actions.jsonl`, and `decision_journal.jsonl`. Reproducible regressions
live in `tests/test_starglider2_*.py` and the shared analysis tests. Retain
[normal-input flight evidence](../../runtime/observations/starglider2-flight-input-evidence.json)
and [memory-span evidence](../../runtime/observations/starglider2-app-memory-spans.json).
The [Painting entry scenario](../../runtime/scenarios/starglider2-painting-viewer-entry.json)
reproduces the normal-media title/options handoff through the canonical runner.
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

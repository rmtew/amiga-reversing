# Starglider II: original source restoration

Goal: readable canonical original assembly and assets, rebuilding the absolute
412736-byte raw image. This is not relocation, an AmigaDOS replacement, or a
claim of complete gameplay/hardware equivalence.

## Current validated baseline

Current validated export: 3517 app references, 2841 typed accesses, 183 unresolved
accesses; 9681 unclassified bytes in 271 intervals. These are analysis counts,
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
Pilot-rating thresholds and verdict selection are reconstructed. The actual
reader now has an automatically inferred aligned 16-entry prefix; CPU cases
qualify the tighter local rank clamp to 0..10. The known-bit abstraction is
conservative; physical pointer ownership and arbitrary-entry limits remain.
Options preserve loaded BYTEs, distinct toggle encodings and partial status
updates. Ratings retain signed tie handling, fifteen visible entries plus
sixteenth-slot shift scratch, and unvalidated six-nibble formatting.
Original payload SHA256:
`662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9`.

## Active queue

GBML/cannon scheduling, tag selection and selected-target missile construction
have 318 original-CPU cases plus 91 connected tracked-update cases. Selection
preserves D1; construction uses creator yaw and retains the cadence WORD. The
shared GBML/Junk initializer does not justify a common counter field for Junk.
Access totals are unchanged. Launcher BYTE+$29/+$2B writes and capsule
WORD+$20/+$24 initial values remain unnamed without a role-bearing consumer;
celestial projection aliases belong to a separate phase/type.

1. Exact tag stores, bounded MOVEM cursors and opaque leading-record address
   identities are supported. Undeclared prefix bytes retain no field meaning.
   Next: stored-pointer lifetime in item 2; do not add per-reader type seeds
   or assume disjoint allocations.
   Of 60 Core gaps, 33 are LONG zeroing stores starting in unnamed portions
   of three 68-byte clears. Known starting-field operands already resolve.
   Other Core bytes are polymorphic: rotations overlap spheroid colour/delay state. Do not widen Core to WorldObject; obtain a
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
   a permanent subtype. A supplied free-stack/player alias at countdown 180
   changes that same record to couch tag 71; this does not establish normal-save
   reachability or invalidate the conditional type-30 view. Next: test call-site
   write footprints with proved workspace/buffer/stack separation and constructor slot postconditions,
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
   Pirate theft doubles that selector before a BYTE read: offsets 8..14 cross
   into the following WORD table. Original-image zero selections test inventory
   slot0 and can allocate a zero-tag child under supplied nonzero slot0 state.
   Do not widen the eight-byte owner or infer normal-play reachability.
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
   The decoded protection view now uses its parent formatter cursor and named
   text targets. The imported cracked-disk bootblock installs a return-address
   gated selector shim at $380: return $13C06 selects record 145, other callers
   forward to the shared PRNG. This is conditional installed-media behavior,
   not a guarantee for arbitrary low-memory state or complete boot execution.
   Dante type47 phase2 enters retirement before motion; with one list and the
   unchanged limit10, eight increments precede release on call9. Volcano phaseFF
   records supply velocities but retain flags that can alter/suppress motion.
   A supplied duplicate-list pointer is released twice; normal list uniqueness
   and free-slot flag producers remain separate obligations. Name entry47 is empty.
   Six two-BYTE pairs per volcano colour bank now have twelve automatically
   bounded readers via shared masked-record WORD transport. Refill storage is
   one BYTE; its neighbor remains unknown. No visual identity or scanout claim.
   The world-pool rebuild gate at app+$7EE has a reader and a zeroing finalizer.
   Bulk save restoration covers it; a positive normal-game producer is still
   unknown. Its consumer name supplies no activation or lifetime invariant.
   Incoming-reference review separates address formation from actual memory
   effects. Some named globals lack backing declarations; investigate connected
   record roles/extents while protecting runtime namespaces, code and views.
   Source-backed scalars and prefixes own only witnessed bytes. The two stored
   24-BYTE space-colour ramps are numeric RG values, including Millway's printable
   bytes; their unchecked reader aliases remain. Coordinate formatting owns its
   exact28-BYTE clear prefix, not the adjacent zeros or an output-capacity bound.
   The 22-byte alternate palette packet supplies six sparse transfer fields and
   16 typed accesses. Its 40-byte text-column companion has a stored extent, not
   a proven runtime index bound; supplied out-of-prefix reads remain unchanged.
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
`AMIGA_REVERSING_PROFILE_SOURCE_QUALITY=1` traces classifier and finalization
costs, including validated source-domain refinement, to stderr. Keep derived
timing traces local.

Normal-input flight and finite CPU fixtures cover their observed paths only.
Physical disk/DMA/audio delivery, full alternate-platform startup, arbitrary
save/restore inputs, queue lifetimes and complete gameplay remain unqualified.
The wider HUNK regression
`test_real_dll_data_block_custom_struct_unaligned_repeated_field_reassembles`
was reproduced before these raw-target changes; its pointer relocation/address
semantics require a separate repair, not a changed expected byte sequence.

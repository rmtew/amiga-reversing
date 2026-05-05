# ORG code ranges

This document is for implementers, including junior programmers learning this
part of the project. It describes how analysis should discover runtime-copied
absolute code ranges and how rendering should decide whether an `ORG` view is
legitimate.

The goal is not to make prettier comments. The goal is to recover source that a
user can work with like original Amiga game source: code ranges, labels, tables,
hardware accesses, and copied runtime code should be formalised when the binary
evidence supports it, while exact reproduction remains unchanged.

## Non-negotiable rules

- C analysis is authoritative. Python wrappers and renderers may consume facts,
  but they must not own the analysis.
- Do not hardcode M68K instruction knowledge. Use generated decode/effect data
  and generic value-flow/backtracking.
- Generic behavior belongs in typed flow/analysis. Amiga behavior belongs in
  platform facts, generated platform metadata, platform file handling, or Amiga
  runtime/platform code.
- Target metadata is allowed only for fixture-backed target-local facts.
- Do not add an `ORG`, label, or EQU just to work around missing analysis.
- Preserve direct source correctness and exact binary reproduction.
- A rendering change is only useful if the analysed source code improves.
  Comments are only a side benefit.

## Address spaces

ORG handling must keep three addresses separate:

- Storage address: where bytes appear in the loaded hunk or file payload.
- Runtime address: where copied code executes after the program moves it.
- Rendered logical PC: the assembler address after an `ORG` directive.

An absolute address is not automatically a source label. Address `$4`, vector
address `$80`, custom chip address `$DFF000`, and a copied payload address are
different kinds of facts.

Runtime entrypoints do not have to equal the base of the runtime range. A range
can start at `$400` while the first proven instruction entered is `$45C`.
Analysis must keep the range base, entrypoint, and labels separate.

## Evidence model

Each discovered runtime code range should have a fact record with:

- Source storage range: section, offset, and size when known.
- Runtime destination range: absolute base and size when known.
- Entrypoints: explicit control-transfer targets into the runtime range.
- Provenance: copy loop, vector install, trap/vector dispatch, jump table,
  policy seed, metadata seed, or fallback seed.
- Confidence: strong, medium, or weak.
- Conflict state: overlaps accepted code, overlaps another runtime view, or has
  no conflict.
- Reproduction status: whether direct binary reproduction and source reassembly
  still pass.
- Corpus tags: pattern tags used to find comparator targets later.

`code_start_refs` must stay provenance-first, but they must not suppress
explicit policy, target metadata, or fallback seeds. The entity model should use
the union:

```
entry_points = set(_c_section_code_entry_points(section))
entry_points.update(policy_metadata_and_fallback_seeds)
```

Then use reason and confidence to avoid weak fallthrough noise.

## Strong and weak ranges

A strong runtime code range usually has:

- A concrete source address.
- A concrete destination address.
- A bounded size.
- Accepted code at the source bytes.
- A control transfer into the runtime destination.
- No incompatible overlap with accepted code.

A weak runtime range usually has only partial evidence. Common examples are
small low-memory trampolines, vector stubs, or copied fragments that immediately
enter a larger runtime payload.

Do not materialize an `ORG` for every weak range. Weak ranges should remain
numeric or become explicit absolute symbols unless they are proven to be
independent source-level ORG ranges.

Multiple ORGs are valid only when analysis proves they represent independent
absolute code ranges from the original source and the assembler's `ORG`
semantics preserve intended references between and around those ranges.

## Real target examples

Keep these examples tied to real corpus targets. They are requirements, not
simplified illustrations.

### Bloodwych

Target: `targets/amiga_hunk_bloodwych/bloodwych.s`

External manually disassembled, human-prettied references:

- `resources/clone_amiga/Bloodwych-68k/asm/BLOODWYCH439_relabel_data.asm`
- `resources/clone_amiga/Bloodwych-68k/asm/Bloodwych439.asm`

These external sources are inspiration only. They can show what a human found
useful, but the project must prove its own facts through analysis and
reproduction.

Observed pattern:

- Bootstrap copies a small routine to `$90`.
- The trap 0 vector at `$80` is set to `$90`.
- The trap routine copies the main payload to `$400`.
- Execution jumps to `$400`.

Representative shape:

```
	lea.l local_payload_START(pc),a6
local_bootstrap:
	move.l #absolute_END-absolute_START,d0
	lea.l absolute_START.l,a0
loc_0_00000046:
	move.b (a6)+,(a0)+
	subq.l #1,d0
	bcc.b loc_0_00000046

	jmp absolute_START.l
	dc.b $00,$00
local_payload_START:
	ORG $400
absolute_START:
	move.w #INTF_CLRALL,_custom+intena.l
	...
absolute_END:
```

Rendering implication:

- `$90` is a trampoline/control mechanism.
- `$400` is the meaningful ORG payload if source bytes and reproduction prove
  it.
- References before the ORG may need storage labels for copy-source bytes.
- References inside the ORG should use runtime labels.
- The copy loop shape must be handled as shipped, including awkward bounds and
  trampoline code.

### Conqueror

Target:
`targets/amiga_disk_conqueror-1990-rainbow-arts-de-en/targets/amiga_hunk_conqueror_cf971606/conqueror_cf971606.s`

Observed problems:

- A copied routine was reached through address `$4`.
- A larger runtime range around `$40/$64` was also present.
- Rendering `ORG $4` caused duplicate or confusing cross-range labels.
- Address `$4` was conflated with a location label.
- Hardware base `_custom` offsets were incorrectly rendered as app slots.

Rendering implication:

- A weak low-memory trampoline should not force its own ORG when it exits into a
  larger accepted runtime range.
- Address `$4` can remain numeric or become an explicit absolute symbol.
- The larger runtime range can be materialized only if backed by accepted source
  bytes and exact reproduction.
- `_custom`, `_ciaa`, `_ciab`, audio, sprite, and display accesses must resolve
  through Amiga platform metadata, not app-slot inference.

### Carrier Command

Target:
`targets/amiga_disk_carrier-command-1994-kixx-budget/targets/amiga_hunk_carrier_91b0ba24/carrier_91b0ba24.s`

Observed pattern:

- Early code copies routines to low absolute addresses such as `$00C0` and
  `$0100`.
- Other runtime views appear around `$5000` and `$328`.
- The target also contains packed or transformed payloads.

Rendering implication:

- Carrier is useful as a stress target.
- Packed-data awareness and reproduction checks are required before using it as
  a clean ORG policy comparator.

## Analysis requirements

Runtime range discovery should come from C analysis:

- Use generated instruction decode and generic value-flow/backtracking.
- Track copy source, destination, and length through registers, stack slots,
  app/global/base slots, and reloads where evidence is strong.
- Recognise vector installs by backtracking stored values, not by fixed adjacent
  instruction pairs.
- Promote explicit policy, metadata, and fallback seeds even when no
  `code_start_ref` found them.
- Queue installed interrupt/vector handlers as code when their targets are
  proven.
- Identify abstract indirect jumps first, then work backward to classify jump
  tables, lookup tables, relative offsets, and absolute targets.
- Use "must not overlap accepted code" gates before auto-classifying data,
  tables, or copied payloads.

Do not solve this in Python. Python may render, index, or materialize facts that
C has already produced.

## Rendering requirements

The rendered source should have this order:

1. Include region, alphabetically sorted.
2. RSSET regions.
3. EQU/symbol region.
4. Sections and code/data.

Label namespace policy:

- `loc_` labels name storage/source offsets in the current section.
- `abs_` labels name materialized runtime addresses inside an accepted ORG view.
- Non-materialized absolute addresses remain numeric or use explicit EQU
  symbols.
- Storage labels and runtime labels must not share visible names unless they
  truly name the same logical source location.

Reference policy:

- Pre-ORG references to copied bytes as source data should use storage labels.
- Branches/calls inside a materialized ORG should use runtime labels.
- Cross-range references must remain correct under assembler `ORG` semantics.
- External absolute memory should not be converted into runtime code labels.

Hardware/platform policy:

- Custom chip, CIA, audio, sprite, copper, display, and interrupt accesses
  should use platform metadata.
- App-slot inference must not claim offsets from known hardware bases.
- Useful aliases should exist where they match the hardware layout, for example
  audio channels and sprite register blocks.

Known useful platform aliases:

```
aud   EQU $0A0
aud0  EQU $0A0
aud1  EQU $0B0
aud2  EQU $0C0
aud3  EQU $0D0

sprpt EQU $120
spr   EQU $140

sd_pos    EQU $00
sd_ctl    EQU $02
sd_dataa  EQU $04
sd_dataB  EQU $06
sd_SIZEOF EQU $08
```

## Implementation workflow

Implement ORG support as a pipeline. Do not skip directly to rendering.

1. Discover code normally from all accepted entry seeds.
2. Run C value-flow/backtracking to find copy, vector, and indirect-control
   evidence.
3. Build runtime-copy candidate facts with source, destination, size,
   entrypoint, confidence, and provenance.
4. Reject candidates that overlap accepted code or conflict with a stronger
   runtime view.
5. Classify the remaining candidates as materialized ORG range, suppressed weak
   trampoline, absolute symbol, or unresolved problem.
6. Render only accepted facts. The renderer should not invent analysis facts.
7. Reassemble and binary-diff the rendered source where supported.
8. Index tags and annotations so later corpus scans can find the pattern again.

For a junior implementer, the important separation is:

- Analysis answers "what does the binary prove?"
- Policy answers "is this evidence strong enough to materialize?"
- Rendering answers "how do we express accepted facts as source?"
- Reproduction answers "did the expression preserve the binary?"

## Table requirements

Jump and lookup tables should be rendered according to how the program computes
the target:

- Absolute relocated entries should use target labels when relocation evidence
  proves them.
- Absolute non-relocated entries should remain absolute or use explicit absolute
  symbols.
- Relative entries should be rendered relative to the correct base label when
  the calculation proves the base.
- Unresolved table targets should be emitted as analysis problems, not hidden by
  guessed labels.

Corpus indexing should tag indirect jump/table shapes so later heuristic changes
can be tested across all matching targets.

## Required annotations

For every accepted ORG/materialized runtime range, record:

- `runtime-copied-code`
- `trap-vector-bootstrap` when applicable.
- `multi-runtime-range` when applicable.
- `materialized-org-range`
- Source storage section/offset/range.
- Runtime base/range.
- Entrypoint addresses and provenance.
- Copy-loop/vector/jump-table evidence.
- Conflict and overlap result.
- Reproduction result.
- Comparator targets used, if any.

For rejected or suppressed candidates, record why:

- `suppressed-weak-org-range`
- `low-vector-trampoline`
- `overlaps-accepted-code`
- `conflicts-with-runtime-range`
- `source-bytes-not-accepted-code`
- `packed-or-transformed-payload`

These annotations should be available through corpus indexing so future work can
search for real examples instead of rediscovering them manually.

## Regression cases

Known bad outputs that must stay guarded:

- Includes mixed into EQU or RSSET regions.
- Conqueror-style `ORG $4` for a weak trampoline.
- Duplicate labels such as storage `loc_0_00000004` and runtime
  `loc_0_00000004`.
- Address `$4` rendered as a normal code location label when it is an absolute
  vector/address.
- `_custom` offsets rendered as app slots.
- Installed illegal/interrupt/vector handlers not queued as code.
- Fixed adjacent move/store matching instead of value backtracking.
- Jump tables emitted as raw values when the base/target calculation is known.
- Data/table classification overlapping accepted code.

## Tests and acceptance

ORG range changes need isolated tests plus corpus proof where possible:

- Bloodwych-style trap/vector trampoline to a larger ORG payload.
- Conqueror-style low trampoline suppressed in favor of the larger runtime view.
- At least one GenAm/MonAm or other non-Bloodwych comparator for each generalized
  heuristic.
- Direct binary reproduction exactness.
- Source reassembly exactness where supported.
- No duplicate label names across storage/runtime namespaces.
- No ORG range overlapping accepted code in an incompatible view.
- Corpus tags proving the target patterns are indexed.

Before retaining a change:

1. Add isolated regression tests.
2. Rebuild relevant corpus targets.
3. Compare Bloodwych and comparator before/after output.
4. Keep only source-code analysis/rendering gains, not comment-only churn.
5. Run reproduction/source reassembly checks.
6. Run the project precommit when the implementation is ready.

## Open implementation questions

- How should the facts schema represent multiple proven independent ORGs in one
  source section?
- Should weak absolute symbols be emitted as EQU values or left numeric until a
  UI problem list can surface them?
- What exact confidence thresholds should allow table target labelisation?
- Which existing corpus targets besides Bloodwych, Conqueror, and Carrier are
  clean non-packed comparators for each pattern?

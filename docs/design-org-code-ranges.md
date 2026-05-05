# ORG code ranges

TODO: Check and update this document for lacking detail or incorrectness.

The goal of reversing a target is to obtain the code and data in a form that the
user will be able to use like the original developers. This will use a
combination of analysis and rendering to produce that reformalised code and
data.

Where this relates to ORG code ranges is that some of these targets contain code
written to run at a fixed absolute address. Sometimes that code was originally
assembled with `ORG`. Sometimes it is stored elsewhere in the file, copied to
the absolute address at runtime, and then entered there. The renderer should
recover the form that is most useful as source while still reproducing the
original binary exactly.

It is not guaranteed that the runtime entrypoint is the base address of the
runtime range.

## ORG usage nuances

A label reference from before the ORG section will be converted to the relevant
absolute address within the ORG section. Here `local_payload_START` stays a
local PC-relative reference to the current segment's data. `absolute_START` is
replaced by its ORG value, in this case $400.

This loop shape is intentionally preserved from a real Bloodwych bootstrap style
example. It is not an idealized copy loop. The design needs to cover what games
actually shipped, including awkward loop bounds and trampoline code.

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
  ....
absolute_END
```

It is not generally valid to use multiple ORG sections just because the runtime
analysis found multiple copied ranges. We are not rewriting the program into a
new layout. We are trying to recover source that resembles the original
developer's layout and still reproduces exactly.

Multiple ORGs can assemble, but they can also change the meaning of cross-range
references. A copied low-memory trampoline can be a means of reaching a larger
absolute payload, not source that should be rendered as a first-class ORG range.
In those cases the low runtime address should remain numeric or become an
external absolute symbol, while the larger payload can become the rendered ORG
view.

Multiple ORGs are valid when analysis can prove that they represent independent
absolute code ranges from the original source, and that the assembler's `ORG`
semantics preserve the intended references between and around those ranges. In
that case the extra ORGs are evidence of understanding the source layout and the
tool constraint, not a workaround.

The implicit requirement is that each materialized ORG must represent a stable
runtime view of source bytes, not every transient copied address.

```
	lea.l local_bootstrap(pc),a0
	lea.l $00000090.l,a1
	moveq.l #40,d0
copy_trap0:
	move.b (a0)+,(a1)+
	dbf.w d0,copy_trap0

	lea.l local_payload_START(pc),a6
	move.l #$90,$80.l ; Trap 0 instruction vector
	trap #0

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
  ....
absolute_END
```

## Address spaces

ORG rendering has to keep these address spaces separate:

- Storage address: where bytes appear in the loaded hunk or file payload.
- Runtime address: where copied code executes after the program moves it.
- Rendered logical PC: the assembler's address after an `ORG` directive.

Labels before an ORG are storage/source labels. Labels inside a materialized ORG
are runtime labels. Rendering must not let a storage label accidentally become a
runtime label with the same text, or let a weak runtime address suppress the
stronger source label needed to describe the copy source.

Label prefix policy:

- `loc_` labels name storage/source offsets in the current section.
- `abs_` labels name materialized runtime addresses inside an accepted ORG view.
- Non-materialized absolute addresses remain numeric or use explicit EQU symbols.
- A storage label and runtime label must not share the same visible name unless
  they truly name the same logical source location.

Runtime entrypoints do not have to equal the base of the ORG range. For example,
an accepted range can start at `$400` while the first reached instruction is
`$45C`. The renderer should still model the range base, interior entrypoint,
and labels separately.

## Observed variations

Observed examples should be kept here so the implementation is tested against
real targets, not simplified patterns.

### Bloodwych

Target: `targets/amiga_hunk_bloodwych/bloodwych.s`

Observed pattern:

- Bootstrap copies a small routine to `$90`.
- The trap 0 vector at `$80` is set to `$90`.
- The trap routine copies the main payload to `$400`.
- Execution jumps to `$400`.

Rendering implication:

- The `$90` trap routine is a trampoline/control mechanism.
- The `$400` payload is the meaningful ORG code range.
- References from before the payload to payload bytes must preserve the storage
  source where needed and runtime absolute labels where appropriate.

### Conqueror

Target:
`targets/amiga_disk_conqueror-1990-rainbow-arts-de-en/targets/amiga_hunk_conqueror_cf971606/conqueror_cf971606.s`

Observed pattern:

- A small copied runtime routine is reached through address `$4`.
- That routine enters a larger copied runtime range around `$40/$64`.
- Rendering a separate `ORG $4` created confusing duplicate/cross-range labels.

Rendering implication:

- A weak low-memory trampoline should not force its own ORG view when it exits
  into a larger accepted runtime range.
- The low address can remain numeric.
- The larger runtime range can be materialized if it is backed by accepted source
  bytes and reproduces exactly.

### Carrier Command

Target:
`targets/amiga_disk_carrier-command-1994-kixx-budget/targets/amiga_hunk_carrier_91b0ba24/carrier_91b0ba24.s`

Observed pattern:

- Early code copies routines to low absolute addresses such as `$00C0` and
  `$0100`.
- Later output currently shows ORG-like runtime views around `$5000` and `$328`.
- The target also appears to involve packed or transformed payload data, so it
  may not be a clean comparator for every ORG rule.

Rendering implication:

- This is useful as a stress target, but ORG decisions here need reproduction
  checks and probably packed-data awareness before being treated as a clean
  policy example.

## Rendering rules

- Only materialize an ORG for a strong accepted runtime range.
- A strong accepted runtime range needs concrete evidence: copied source,
  destination, and size where possible; accepted code at the mapped source bytes;
  and a concrete control transfer into the runtime destination.
- A weak trampoline is usually short copied code, often at a low/vector address,
  with little meaningful internal structure and an exit into a larger runtime
  range.
- Do not materialize an ORG for weak trampoline ranges that only reach a larger
  runtime range.
- Multiple ORGs are allowed only when the ranges are proven independent and the
  rendered references still match the recovered source intent.
- Do not materialize overlapping or conflicting runtime ranges.
- Do not materialize a runtime range that is not backed by accepted source bytes.
- Do not let runtime labels overlap accepted code in another incompatible view.
- Keep external absolute memory as numeric operands or explicit absolute EQU
  symbols unless there is enough evidence for a runtime code view.
- When pre-ORG code refers to copied bytes as source data, prefer storage labels.
- When code inside a materialized ORG branches or calls within the runtime view,
  prefer runtime labels.
- Copied data mixed with copied code should not force an ORG by itself. Render it
  as part of the same ORG only when it belongs to the recovered source layout and
  reproduction remains exact.
- Preserve exact binary reproduction first. Source readability improvements are
  only retained when reproduction remains exact.

Direct reproduction of the original bytes is mandatory. Reassembling rendered
source back to exactly the same binary is also expected for targets where source
reassembly is supported. ORG changes should not make source reassembly worse.

## Test requirements

ORG range changes should have isolated tests plus corpus proof where possible:

- Bloodwych-style trap/vector trampoline to a larger ORG payload.
- Conqueror-style low trampoline suppressed in favor of the larger runtime view.
- A comparator target using similar runtime copied code.
- Direct reproduction exactness.
- Source reassembly exactness where that target supports it.
- No duplicate label names across storage and runtime namespaces.
- No ORG range that overlaps accepted code in an incompatible view.

Known bad outputs should stay as regression examples:

- Conqueror-style `ORG $4` for a weak trampoline.
- Duplicate or conflicting `loc_0_00000004` and `abs_0_00000004` style labels.
- Cross-range references that switch from source storage labels to the wrong
  runtime labels.

## Corpus tags

Targets with ORG/runtime-copy patterns should be tagged so later analysis work
can find real comparators. Useful tags include:

- `runtime-copied-code`
- `low-vector-trampoline`
- `trap-vector-bootstrap`
- `multi-runtime-range`
- `materialized-org-range`
- `suppressed-weak-org-range`
- `packed-or-transformed-payload`

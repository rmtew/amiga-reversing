# Proposal 045: Behavioural validation

Status: implementation authorised; no commitment is complete. Baseline:
`1ed6643022fb906cacc5abc56e6836fa8b51299e`. Proposal number checked against the
local proposal directory before creation. This roadmap coordinates work in the
existing reversing framework; it is not another fact store or acceptance log.

## Evidence and authority

Contracts and acceptance belong to canonical function summaries/facts, the
revision-checked Manual Action Log and Decision Journal. Captured fixtures and
results are evidence artifacts, not authority to alter a contract. Reuse
`copperline_session.compile_scenario`, runtime capture/run, checkpoint identity
binding, full bus traces and `restoration_verification` receipts. CLI, MCP and UI
must invoke shared services, rather than implement different comparison rules.

Existing starting points:

- [CPU volume comparison](../../amiga_reversing/tools/pandora_volume_local_compare.py):
  original versus manifest-derived assembly under modeled local CPU calls.
- [Scratch tracing](../../runtime/observations/pandora-unknown-span-tracing.json):
  canonical renderer entry `$16C60`, return `$17090`, and ordered physical DMA
  observations, including 256 WORD writes and 128 reads in the full-scratch probe.
- [Complete filtered gap transfers](../../runtime/observations/pandora-cursor-gap-chip-bus-transfers.json).
- [Existing restoration workflow](../agents/reversing-loop.md) and
  [runtime constraints](../copperline-runtime.md).

## Commitments

Capability status and target coverage are separate. The table records the baseline
assessment; the current status index below records implementation and coverage.
All commitments remain
**open**: existing foundations are not a completion claim. Advance an entry only
with implementation, positive/boundary/failing tests, named contract coverage
and content-addressed evidence. Dependencies establish implementation order,
not a requirement to finish a universal framework before using a bounded slice.

| ID | Commitment / dependencies | Baseline existing versus missing | Acceptance criteria | Initial action / evidence |
| --- | --- | --- | --- | --- |
| B01 | Bounded original-routine execution; none | Existing generated Motorola-derived concrete CPU runner and canonical Copperline scenarios. Missing shared admission of bounds and outcomes. | Exact binary/backend/profile identities, explicit input/return/control-flow budget, refused unsupported execution, and live bounded CPU and DMA cases. | Adapt the volume runner first; then run the captured scratch entry. Starting evidence above. |
| B02 | Reusable identity-bound captured-state fixtures; B01 | Checkpoint receipts bind guest state/media/context. Volume projection silently fills uncaptured bytes from image or zero. | Distinguish captured-known, immutable-image-known, modeled and unknown ranges; reject conflicting/stale identities and required unknown reads. Keep ROM, payload and checkpoint bytes local. | Inventory the volume donor's admitted code/data/stack inputs and expose provenance through the existing fixture/manifest mechanisms. |
| B03 | Reviewed evidence-backed behaviour contracts; B01, B02 | Canonical summaries, MAL and DJ already carry facts and decisions. Missing a demonstrated behaviour-contract reference and review lifecycle. | Contract names preconditions, effects, ordering, arithmetic, exclusions and obligations; receipt binds the reviewed canonical identity/revision. No private contract database or silent promotion from observations. | Discover the existing command catalog before adding the volume contract, then the scratch producer/consumer contract. |
| B04 | Ordered comparison and first divergence; B01–B03 | Volume comparison sorts/deduplicates final effects; bus captures retain order. | Compare ordered semantic events and identify the earliest differing event with input/PC/address/old-new context. Equal final memory after reordered effects must fail. Explicit normalization may alter only reviewed logical identities. | Preserve volume writes at each instruction before final-state coalescing; test duplicates, transient writes and reordered DMA. |
| B05 | Producer/consumer, scratch, alias and lifetime checks; B02–B04 | Scratch trace proves bounded reads follow writes and identifies a caller. Missing reusable checks and reviewed lifetime limits. | Check write-before-read, selected WORD/stride, aliases and bounded clobbers; deliberate read-before-write fails despite equal final buffer. State unknown initial bytes and unobserved callers/lifetimes explicitly. | Apply the shared ordering seam to Copperline scratch events; do not extrapolate original seed meaning or whole allocation. |
| B06 | Explicit original arithmetic semantics; B01, B03 | Generated Motorola-derived CPU backend is present; volume contract checks BYTE lanes. | Width, signedness, extension, wrapping, shifts and CCR obligations are explicit where relevant. Boundary/overflow cases exercise generated semantics; no target opcode patches. | Admit the volume WORD/BYTE arithmetic and guard/distance boundaries; fix extraction/generation upstream if a backend defect is reproduced. |
| B07 | Deterministic valid/boundary cases and small reproducers; B02–B06 | Volume has deterministic guarded cases and exhaustive BYTE inputs. Missing shared failure preservation and minimization evidence. | Reproduce fixed cases/seeds, preserve a failing seed and exact assumptions, and reduce failures without leaving valid contract inputs. Deliberately failing tests exercise diagnostics. | Preserve the first ordered CPU mismatch as a small instruction/call reproducer; add valid guard, byte-lane and arithmetic boundary cases. |
| B08 | Behaviour coverage separate from accounting; B03, B04 | Byte, purpose and relocation accounting exist. Missing behaviour coverage in existing batch reports. | Report contracts/cases/input partitions/paths/engines/windows/limits separately from byte exactness, purpose and relocation. A successful self-replay counts repeatability only. | Add a bounded coverage section to the existing receipt/report; no new tracker. |
| B09 | Strict outcomes and fail-closed evidence; B01–B04 | Runtime has explicit timeout, identity and capture guards. Missing uniform comparison outcomes and staleness admission. | Distinguish pass, mismatch, missing prerequisite, timeout/not observed within bounds, unsupported, incomplete/truncated, stale and explicitly accepted deviation. Skips never imply equivalence. Changed binary, fixture, contract, backend or profile invalidates prior receipts. | Bind those identities into existing verification receipts and test every outcome. Accepted deviation requires a DJ decision and is not equivalence. |
| B10 | Adoption in connected subsystem batches; B01–B09 | Existing connected reversing batches and histories. Missing this checklist and two-case adoption evidence. | Each batch names B IDs/contracts advanced, exact receipts, remaining obligations and next evidence question; function, structures and consumers advance together. No ID closes on documentation alone. | Land the roadmap plus tested CPU slice, then the genuinely DMA-dependent scratch case before extracting further abstractions. |

## Initial implementation batches

1. **CPU volume slice** — B01/B02/B04/B06/B07/B09, with B03/B08/B10
   integration. Preserve the original/manifest-derived ASM comparison. Keep a
   locally modeled call frame and guard inputs explicit. Unknown dependencies
   cannot become known through zero shadow. Original self-replay proves
   repeatability only. An ordered effect stream must include unchanged and
   repeated writes, not just the final differences. Instruction/control-flow
   budget exhaustion is a non-pass outcome.
2. **Shared-scratch slice** — B01/B02/B04/B05/B07/B09, with B03/B08/B10
   integration. Use Copperline and its existing full bus trace. Bind the captured
   renderer entry/caller, profile, requested ranges, partial frame boundaries and
   truncation limits. Validate the producer/consumer order and byte values. A
   deliberately reordered trace with an equal final buffer must fail.
3. Extract only seams demonstrated by both cases: evidence identity admission,
   ordered semantic-event comparison, strict outcomes and receipt/coverage
   reporting. Do not replace either execution engine or invent a C candidate.

## Receipt and batch obligations

Content-address results to original/candidate binaries, fixture, reviewed
contract, generated backend and machine/profile assumptions. Preserve the
existing verification/acceptance service and histories. A prior result is stale
when any bound assumption changes; re-running its hash calculation does not
retroactively validate new assumptions. Publish manifests, identities, bounded
target-only events and results, never proprietary payloads, ROMs or guest states.

Every batch records capability changes separately from target behaviour
coverage, B IDs and canonical contract identities, positive/boundary/failing
tests, exact evidence identities, outcomes, remaining obligations and the next
evidence question. Source changes additionally require byte-exact reconstruction;
behaviour tests neither replace that check nor inherit correctness from it.

## Deliberate limits and current status

CPU-local calls do not establish normal gameplay reachability, IRQ behaviour,
Paula/DMA timing or relocation safety. Scratch observations do not establish
original seed meaning, the unobserved remainder, whole-span stack reservation,
all-callers lifetime or relocation safety. Bank 30 remains unresolved. Fonts,
bank-45 layout speculation and EQU/RS emission policy are outside this programme.

The first tested batch is recorded in
[pandora-behavioural-validation-first-slice.json](../validation/pandora-behavioural-validation-first-slice.json).
It preserves full evidence identities and the two accepted canonical contract
summary/action/decision identities. The CPU slice passes 19 modeled original versus
manifest-derived ASM calls plus all 65,536 WORD inputs to the single BYTE store.
The DMA slice passes one original fixture and self-replay: 256 D-channel WORD
writes followed by 128 A-channel reads, every read matching a preceding write.
This is not a candidate DMA comparison. The final suite passes 180 Python tests
and 30 native simulator tests; one optional live MCP SDK transport test skips
because that SDK is absent. Adapter registration/forwarding and real HTTP CLI
operations are tested. C and independent vasm reproduce all 376,832 original
bytes; generated assembly is unchanged. Unknown payload bytes remain 6,446.

## Current status by commitment

The follow-up correctness batch hardens B01/B02/B04/B07/B09 rather than
expanding target coverage: all admitted CPU helper bytes now come from the
selected image, the current native relocation proof is checked before execution,
and manifest/plan identities enter the receipt profile. Executed backend identity
is retained, and cached Python checker code is pinned at import with restart
required after disk edits. See the
[identity regression evidence](../validation/pandora-behavioural-validation-identities.json)
for reproductions, affected historical receipt profiles and fresh revalidation.
This adds no new canonical contracts, gameplay paths or DMA candidate coverage.

The [warm audio-start batch](../validation/pandora-behavioural-validation-warm-start.json)
then adds a separately reviewed CPU predicate for the previously excluded
alive-near/unarmed composition: six modeled calls, 141–143 instructions each,
with four channel records and 40 ordered initialization field writes. It uses a
private identity-bound capture and a 256-instruction limit; legacy v1 retains
128. Three predicates now share two canonical function summaries, with distinct
selected-predicate identities and review bound to each summary's latest active
producer. Coverage is 25 CPU cases plus the unchanged 65,536 BYTE inputs and one
original DMA fixture. The focused suite passes 223 tests with one optional live
MCP SDK skip. No normal-gameplay, cold sample, live CIA/Paula/DMA or later audio
consumer proof follows from the new CPU calls.

Every row is **partial/open**, including rows with an implemented first seam.
No commitment is complete on documentation or one successful fixture. Evidence
for these rows is the batch receipt summary above and its linked
[deterministic negative reproducers](../../runtime/observations/pandora-behaviour-negative-reproducers.json).

| ID | Capability implementation | Current target behaviour coverage | Next action |
| --- | --- | --- | --- |
| B01 | Partial: opt-in ordered ordinary-68000 observer; existing Copperline capture retained. | 25 bounded modeled calls per ASM layout; one original DMA fixture/replay. | Extend the DMA consumer observation before claiming wider behaviour. |
| B02 | Partial: explicit known/modeled/unknown memory manifests, unknown-read refusal and existing identity-bound checkpoints. | Legacy and private warm-start donors; private original scratch checkpoint. CIAA snapshot delivery is explicitly a CPU input model. | Admit a second renderer fixture from its owned full sidecars; keep raw guest data local. |
| B03 | Partial: named predicates use canonical summary notes, MAL and DJ; latest effective producer and selected predicate are bound separately. | Legacy volume, warm-start volume and scratch predicates accepted within their exclusions. | Review the next DMA predicate through the same histories; no older action's inherited acceptance. |
| B04 | Partial: ordered architectural events, semantic bus comparison and first differing event; transient/duplicate writes retained. | 25 CPU comparisons, including 40 ordered channel writes per warm case; 384-transfer original self-replay and deliberate order failures. | Follow the scratch reads into destination writes, respecting prefetched FIFO order. |
| B05 | Partial: exact scratch address/channel order and write-before-read value checks. | One 32-row, shift-4 second-word renderer fixture. Pixel/mask bounds, destination bitmap and other callers are outside coverage. | Add a second boundary fixture and destination/source observations before broader alias/lifetime claims. |
| B06 | Partial: explicit wrapped WORD, BYTE-lane and signed relative-address arithmetic checked against generated execution. | Signed extrema, sum wrapping, distance255/256 and all 65,536 WORD inputs to one BYTE store; fixed captured warm tables have nonnegative offsets. | Do not infer coverage of negative table values or cold sample arithmetic. |
| B07 | Partial: deterministic cases, small preserved negative streams and failure recipes. | Reordered/equal-final streams; missing device/table inputs; cold guard/far inputs; old-budget timeout; predicate-set and review-provenance negatives. No broad fuzzer or automatic minimizer. | Preserve the next real failure and minimize only within its valid preconditions. |
| B08 | Partial: separate behaviour coverage in existing verification receipts and batch reports. | Three predicates, 25 CPU cases, 65,536 BYTE inputs and one adopted DMA fixture. No new byte or purpose credit. | Keep unqualified probes separate from adopted contract coverage. |
| B09 | Partial: strict outcomes, identity bindings, native-proof and loaded-code guards, private fixture hashes, selected predicates and review/deviation gates. | Positive/negative tests and fresh pre-review non-pass/post-review receipts. | Admit full-sidecar partitions without silently accepting a truncated report. |
| B10 | Partial: per-batch checklist integrated into the existing reversing loop. | Initial CPU/DMA, identity correction and warm composition batches; shared HTTP evaluator, thin CLI/MCP adapters. No dedicated UI results panel. | Apply the checklist to the next DMA consumer fixture; keep later work queued here. |

Next evidence question: can the scratch consumer be followed into the alternate
destination buffer without misattributing later blits in the same window? The
second natural entry has the same H32/shift4 geometry, so it adds no height/shift
boundary coverage yet. Its retained full sidecars permit bounded partitioned
analysis beyond the truncated report. Bank 30, fonts, bank-45 layout and EQU/RS
policy remain outside this batch.

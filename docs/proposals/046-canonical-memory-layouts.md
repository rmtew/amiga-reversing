# Proposal 046: Canonical memory regions and layout export

Status: **Functional original/image/cursor/display delivery and measured native reuse are evidenced. Shared placement geometry is consolidated; the semantic data-relocation adapter remains. Strict original HAND-cycle equality is still not met, so unconditional first-delivery closure is unclaimed.**
Audit baseline: master `a814a2a47bbd87abb6d06e11d8b69908e8dfd9d5`, 2026-10-23.

## Implementation checkpoint (2026-10-24)

### OS-host environment prerequisite; game lifecycle still pending

[The normal DOS entry probe](../../runtime/observations/pandora-OS-entry-prerequisite.json)
boots an own OFS disk under the available Kickstart1.3/ECS1MiB profile. Two own
HUNK executables print in sequence and return to the CLI prompt, visually
reviewed at frame1500. Existing vasm and external amitools0.8.1 suffice; no new
filesystem implementation, Workbench media or original Pandora ADF was needed.
The builder intentionally reports capture completion, not an automatic pass.

This is not an OS-hosted game or game-cleanup receipt. The next bounded source
contract is an input-owned copy helper instead of the fixed `$300` helper,
retaining initialization and explicit source lifetime. Actual DOS-loaded input,
all RAM owners, an exit hook, hardware/vector/stack restoration and DMA-safe
release remain required. No blind bootstrap stripping or address-word scan is
admitted by this probe.

### Natural priest completion: four-store exercise

[The bounded cold route](../../runtime/observations/pandora-priest-passage-natural-qualification.json)
now exercises the startup reset, combat-open, completion-close and priest-open
stores at actual app `$7080`, cell `$9B44`. All230 phases complete at frame6094,
HP35, with zero event loss. The original combat dispatch returns to `$87A02`;
A6 stays `$7080` at all eight before/after hooks. The completion pair changes
`$8E928 → $94C28 → $8E928`. Reset/open can rewrite an already present value;
these are matched instruction/cell snapshots, not a write-event trace.

The first attempt exposed an optional-symbol-catalogue observer assumption;
the next met the chamber's west wall while still alive. Retained failures and
the existing17-pose terrain model produced a southern-doorway approach which
then completed without state injection.151 relevant runtime/mapping/walkthrough
tests pass; five altered-report witness checks refuse. The natural ranged
callback caller remains unexercised, with only the earlier conditional static
contract. No new byte classification or graphics/PCM equality is claimed here.
Next is actual OS-friendly entry/loading, ownership and DMA-safe return; the
current boot shim does not provide that lifecycle.

### Guest-selected CPU bases: route and scoped output qualified

[CPU allocation qualification](../../runtime/observations/pandora-CPU-allocation-qualification.json)
records real Exec `AllocMem(MEMF_CHIP)` returns `$6080` and `$7080`. A genuine
4,096-byte prior lease selects the latter; neither base is supplied to Exec.
Native admission and complete guest-patched input/prefix readback pass. Both
cold controlled runs complete all576 phases, saved Earth plus escape, at
HP49/frame14465; an unheld cold run completes at HP49/frame14351. Both loss
counters are zero. Before/after-owner failure probes complete guest unwind.

[Strict output comparison](../../runtime/observations/pandora-CPU-allocation-output-comparison.json)
passes all576 phase clocks,509 controller calls, eight exact RGBA frames and
24,726,568 float32 PCM samples through EOF. Known null-sprite0/2 findings remain;
no new sampled DMA bound finding appears. Keyboard stays `$6000`, display stays
`$E0000..$ED000` and cursor stays `$65370`. The loader variants differ in size:
raw pre-GO PCs differ34bytes. Full code/listing binding establishes the same
instruction in identical40-byte wait blocks; clocks and all other registers
match exactly. This is explicit loader-relative identity, not raw-PC equality
or clock fitting. Original-to-image eight-CCK HAND equality remains unfulfilled.

66 focused tests pass without skips. The subsequent partial-static unwind
observer fix handles uninitialized record RAM without changing guest bytes or
any completed gameplay artifact. The later natural-priest checkpoint above closes the combat four-store
exercise; successful DMA-safe OS return and the natural ranged caller remain
separate obligations. This ending route alone did not exercise them.

### Four-site target adoption (earlier export checkpoint)

[Adoption and corrected input validation](../../runtime/observations/pandora-passage-address-frame-adoption.json)
record full restored export C/vasm agreement and unchanged, byte-exact original
source. Native allocation now admits seven fields plus four frame guards:
four absolute-L operands and three typed MOVE.L grid-base immediates at
`$90A8/$9CB4/$9EE0`. The immediate family surfaced at the first allocation
check; it is admitted using generated extension coordinates and explicit runtime
symbols, not numeric guessing. Native probes admit `$6080/$7080/$8080`, refuse
NULL and colliding `$59E8`. These are placement checks, not allocation/gameplay.

Review found the initial A6 auditor only length-checked decoded facts. Its
corrected checker now validates retained fact/graph hashes against the published
review inputs and requires unique identical coordinates/sizes plus original
bytes. Seven input-validation tests pass and reproduce the same conditional APP
result. The original contract artifact/hash is retained; this supplements its
evidence without silently rewriting it. CPU guest lease/patch implementation,
normal-input passage coverage and new route/output qualification remain pending.

### Explicit address-frame implementation (earlier fixture checkpoint)

[Four-site review and scoped timing evidence](../../runtime/observations/pandora-passage-address-frame-contract.json)
now support a conditional A6-relative candidate covering both original priest
callback paths. Native region annotations bind the full input, each original
instruction and the review contract. Moved owners render an explicit same-size
IR transformation; original owners retain their absolute-W instruction. Used
cell/base symbols and expected symbol-access checks remain intact. Frozen reuse
requests a new plan when activation changes; runtime plans expose opcode and
displacement guards. Numeric/scalar, stale, unaccepted and unsupported forms
refuse. The regression suite passes161 cases plus3 added negatives, without skips.

Independent C/vasm/Musashi checks match eight bytes,24cycles and scoped state
semantics for all four sites across four modeled app bases and32CCRs. The
isolated Chip-bus pair matches recorded slot phases and9782cellWORDwrites;
only expected code fetch values differ. The profile is marked partial, so no
full-frame/all-contention or natural gameplay timing claim is made. This fixture checkpoint preceded full target adoption above; normal-input
passage coverage and CPU allocator-selected gameplay remain pending. These
diagnostics do not substitute for them.

### Priest-passage reference correction and CPU encoding boundary

[Correction and allocation diagnostic](../../runtime/observations/pandora-passage-relocation-boundary.json)
records three canonical address-domain corrections via the revision-checked API:
cell `$64C0` (4 bytes), open pixels `$1E928` and closed pixels `$24C28` (128 bytes
each). Original source stays unchanged and full C/vasm equality holds. The
exporter and frozen projection now share an absolute-W reach guard; emitting the
low word of an unrepresentable positive RAM address is refused, not a pass.
38 focused and 108 adjacent layout regressions pass without skips. A fresh
corrected real CPU export refuses with `absolute_word_layout_overflow` after
179.6s; no broken alternate payload is admitted or runtime-qualified.

The 48,051-byte owner probe returns `$59E8` / `$5A28` on independent cold boots
with 0/64 prior scratch bytes. Both owners are freed; Pandora is never entered.
Their cells would be `$84AC` / `$84EC`. Retaining absolute-W requires an app base
no higher than `$553B` (at most `$5538` at the owner's alignment4), plus all
ownership/collision constraints. These two observations do not rule out every
possible low OS placement. The formerly qualified fixed `$6080` export has a
known reference gap, not a new all-path pass: its scalar EQUs kept the cell and
pixel pointers at old values. Existing captured outputs remain historical.

CPU guest fixup execution is blocked on a legal address-form contract. A bounded
candidate is an explicitly reviewed same-size A6-relative lowering for the four
stores, if original caller/callback contexts establish the app base. That
contract is not implemented or assumed here. No absolute-L widening, general
branch relaxation or hidden opcode rewrite is introduced. Normal successful OS
return and DMA-safe lifecycle cleanup remain open.

### CPU allocation projection: implementation tested, target refused

[Native projection evidence](../../runtime/observations/pandora-CPU-fixup-projection.json)
records 20 passing focused tests. Generated encoder metadata supplies exact
absolute-W/L extension coordinates; plans retain source instruction, operand,
opcode, width and symbol identity, validate original bytes, preserve CPU child
aliases and enforce positive Chip absolute-W reach. Numeric/unbound operands,
unsupported forms and DMA children refuse. The existing guest descriptor still
rejects CPU scope; no CPU allocator-selected gameplay has run.

The real target refuses at source `$78C4`, operand 1. Four known writers
(`$78C4`, `$79F2`, `$9F38`, `$4B0CE`) use fixed priest-passage cell `$64C0`,
app offset `$2AC4`. At app base `$6080` the actual cell is `$8B44`, beyond
positive absolute-W reach. At that recorded head, the slot and open/closed pixel EQUs (`$1E928`,
`$24C28`) were scalar in the alternate export; the correction above now binds
their runtime domains. This is a concrete
reference gap despite the passing route/output sample below: reset's old-cell
write falls inside reused backing excluded by the guard; optional/warm-restart
passage behaviour is not certified. No prior observation is relabelled as a pass
for these references. Next: canonical address-domain correction and a legal
encoding/placement contract, then CPU guest fixups and real allocation.

### CPU workspace plus display: qualified fixed placement

**Keyboard lease correction qualified:** the first captures acquired app/grid
backing but omitted the independent keyboard storage root. The corrected adapter
requests both, coalescing only Exec backing through `$11C38`. Fresh control and
candidate runs both complete all576 phases at HP49/frame14465; the unheld run
finishes at HP49/frame14353. All phase/input clocks, eight frames and post-GO PCM
match, with zero loss counters. 121 tests pass; game bytes remain unchanged. The
old captures remain historical and are not evidence of the previously absent lease.

[Current qualification](../../runtime/observations/pandora-canonical-cpu-workspace-qualification.json)
combines image `$80000`, display `$E0000..$ED000`, independent keyboard `$6000`
and app/raster base `$6080` with grid `$6684`. The app/grid parent preserves the
actual `APP_STATE_BASE + $604 == grid base` alias. Keyboard remains a separate
root; physical adjacency or rounded lease overlap is not mandatory co-placement.
Normal export and C/vasm agree. Both controlled roles complete all 576 phases at
HP49/frame14465; the unheld candidate completes at HP49/frame14353. Phase clocks,
509 controller calls, eight RGBA frames and 24,726,568 float32 PCM samples through
EOF match exactly. The two event-loss counters are zero. Current framework and
independent vasm checks reproduce all 376,832 original bytes; tracked source is
unchanged. 120 focused tests pass, without skips.

The first moved run stopped at frame1999: source `$2904` read `$11C32` from
A4=`$11BEC`. This is the already-documented stale-A4 inventory path, not a new
table. Grid extent stays unchanged at `$4000..$F568`. Only parent backing now
extends through the conditional byte `$F5AE` (exclusive `$F5AF`), translated to
`$11C32` (exclusive `$11C33`). The intervening suffix is unclassified; no seed,
new producer, bit-7 consumer or original-file classification credit is invented.
Changing this envelope changes zero game bytes. Both earlier failure and passing
captures are retained privately with published identities.

Observation reads and typed pointer expectations consume native coordinates.
CPU guards exclude only explicitly live canonical roots and report excluded
reuse as uncovered; they are not complete fetch or DMA coverage. Core-region
changes cost a new native baseline (202.4s for the envelope correction); the
layout-only projection reused its frozen plan in22.7s. No second planner or
rendered-text patch engine was added.

This is fixed placement with pre-I/O Exec backing. Next: native generated
operand fixups and allocator-returned CPU bases, preserving the low-address
encoding limits, then persistent ownership/entry/cleanup. Other low scratch,
vectors/hardware lifecycle and successful OS return remain open. The original-
to-image eight-CCK criterion remains unfulfilled. No all-path claim is made.

### Historical M5 body-allocation qualification

[Qualification and exact evidence identities](../../runtime/observations/pandora-runtime-allocation-qualification.json)
record real Exec-selected `$F568` and `$F5A8` placements under the earlier model for the 2,304-byte body
snapshot. Both complete all 576 phases, saving Earth and escaping at HP49 / frame
14465. The strict pair matches all phase clocks, 509 controller calls, eight
selected RGBA frames and 24,726,568 float32 PCM samples through EOF, without
alignment fitting or tolerances. Both loss counters are zero. This is the same
1-MiB Chip/ECS profile, image80000/displayE0000/cursor65370, not arbitrary placement.

The current model adds the conditional grid-end probe `$F5AE` above. Both old
body bases overlap that footprint, so their independent-placement assumptions
are superseded. Recorded route/output observations remain historical evidence;
new allocation admission must consume the updated canonical plan.

The finite body DMA episode captures 1,152 producer WORD writes and 1,148 consumer
WORD reads; every observed read matches its preceding captured write. Four reads
are outside the recorded consumer window. No old-body access was observed in
these windows. No claim of all-callers lifetime or no intervening unrecorded write
is made. A separate fixed-E measurement matches eight selected frames and captured
post-GO PCM; its different pre-GO CPU fixture is explicit, not a strict boot pass.

Review found and reproduced a second-collision unwind bug: the first scratch
lease could be freed with the second exclusion's size. The corrected guest code
frees the rejected owner once and refuses before overwriting the live scratch
size. All 60 focused tests pass, including executable assembly/Exec-stub refusal,
comparison admission and incomplete/wrong-value DMA negatives. A fresh corrected-
loader unheld cold run completes at HP49 / frame14351; both real pre-entry faults
unwind at the byte-verified completion label. The strict PCM pair above predates
this error-path repair; it is not relabelled as a new-loader paired capture.

The [native implementation](../../runtime/observations/pandora-runtime-allocation-implementation.json)
retains typed pointer domains, actual-base admission and shared service/CLI/MCP.
Original source and its retained full C/vasm exact receipt are unchanged. The
owner/scratch remain leased through post-ending observation; normal OS return,
DMA-quiescent successful cleanup and ownership of all fixed RAM are still pending.
A loader-only next-step probe returns NULL for fixed keyboard, raster-table and
grid leases. The connected fixed CPU movement is now qualified above; allocator-
selected CPU placement and OS-safe takeover remain next. M5/M6 and all-path closure are not claimed.
The separate original-to-image eight-CCK criterion remains unfulfilled.

### Earlier display continuation (qualified)

[Independent display qualification](../../runtime/observations/pandora-canonical-display-qualification.json)
now records the normal-export E0000..ED000 display group, independently of image
80000, with cursor still at 65370. Fresh common-loader control/candidate runs both
complete all 576 phases at HP49 / frame14465. The unheld cold candidate completes
at HP49 / frame14353, with both loss counters zero. All576 phase clocks, 509 controller
calls, eight selected RGBA frames and 24,726,568 float PCM samples through EOF
match exactly. Six sampled core DMA frames match; the same eight NULL-sprite
reads at 0/2 remain outside asset bounds. Raw unchanged asset bytes total 295,492.

Four additional committed startup profile frames contain 54,744 bitplane WORDs
per role with zero normalized address/data mismatches. The two hybrid witnesses
now read zero at E0002/E0006 inside the first 40 CPU-zeroed bytes. HAND/init/title
PCs and clocks match the retained diagnostic control exactly. The new invariant
test asserts low16 preservation for every child, both witness offsets and their
complete WORD containment; three cases pass. Children retain 2-byte alignment;
the 64-KiB restriction belongs only to the parent and retained live Copper sequence.

The historical D8000 comparator remains a 14-pixel mismatch and that placement
now refuses. No timing padding, cropping, tolerance or extra seed was used.
Original full C/vasm remains exact (`743e95a4…`). This does not resolve the separate
original-to-image eight-CCK pre-GO finding, certify all paths, qualify simultaneous
cursorE0000/display movement, or implement allocation/OS cleanup. The later body-allocation evidence and combined
CPU movement are described above; allocator-selected CPU placement is next.

Historical causal failures and their canonical repairs remain in
[the live-pointer receipt](../../runtime/observations/pandora-display-live-pointer-constraint.json),
[status aliases](../../runtime/observations/pandora-display-status-aliases.json) and
[initialization contract](../../runtime/observations/pandora-display-initialization-contract.json).
The current pass supersedes their pending-qualification statements, preserving
the failed runs and exact original receipts. M5/M6 continuation is authorized;
M5 now has the bounded implementation above; OS lifecycle remains unimplemented. Do not reopen the eight-CCK probe without new evidence.

### Earlier M5 preparation: typed sites and allocator collision

[Native evidence and allocator probe](../../runtime/observations/pandora-allocation-preparation.json)
identify the body descriptor's one typed LONG at source `$3402`, pointing to
`UI_BODY_BACKGROUND_STORAGE` (`$7F0`, 2,304 bytes). The region API now exposes
frozen typed data-pointer sites separately from instruction candidates; it does
not turn them into admitted runtime fixups. The existing 28 numeric instruction
candidates and legacy proof refusal are retained. Scalar lookalikes, end-exclusive
addresses and unresolved pointer namespaces have focused negative coverage;
162 relevant tests pass. Native inspection took 161.75 seconds; no whole-target
source generation or new walkthrough was performed for this read-only projection.

A small reproducible guest diagnostic uses real Exec `AllocMem(MEMF_CHIP)` and
`FreeMem`, via the existing verified direct-payload boot path. With full native
staged-input backing reserved, requests return `$59E8` and `$5A28` (the latter
with a prior 64-byte scratch lease). Both free calls complete. Neither result is
admitted for the game: both overlap the fixed world-pointer grid `$4000..$F568`.
The diagnostic never starts Pandora or patches its pointer. This is capability
and collision evidence, not two successful M5 layouts or OS-friendly loading.

That preparation led to the historical body allocation above. Its required
contract was: acquire or avoid live fixed ranges, validate the actual returned base
with the canonical planner, apply only reviewed typed source-coordinate fixups,
verify initialized materialization, and unwind owned resources on failure.
The body's capture and restore routines return before the new blit completes;
its lease must survive the final DMA read. No immediate `FreeMem` at routine or
modal return is justified. Two legal allocated layouts and relevant normal-input
completion/output evidence remain required. OS takeover/return remains M6.

[Workspace qualification](../../runtime/observations/pandora-canonical-workspace-qualification.json)
records normal-export saved-Earth completion with image `$80000` and an
independently moved 140-byte cursor workspace at `$E0000`. The unheld cold run
completes all 576 phases at HP49 / frame14353, with both loss counters zero. The
controlled original, image-only and cursor runs each complete at HP49 / frame14465;
these are fresh runs with an explicit common guest loader program, not a reuse
of the earlier image-only frame14351 receipt.

The independent cursor move is compared against the canonical image-only
control, keeping image/bootstrap and every other region fixed. All 576 phase
clocks, 509 controller calls, eight selected rendered frames and 24,726,568
float samples from HAND through recording EOF match. Six core DMA frames match,
retaining the identical eight NULL-sprite WORD reads at addresses0/2 outside
certified asset bounds. Two separate inventory DMA frames have no bounds
findings and identical ordered streams; three stopped 140-byte snapshots and
typed app pointers also agree. See the
[scoped output receipt](../../runtime/observations/pandora-canonical-cursor-output.json).
This does not certify every frame, optional path or unobserved DMA continuation.

The original-to-image strict comparator still refuses an eight-CCK natural
HAND-stop difference, despite identical stopped registers. Do not call that
check passed. Independently, all 576 game phase/controller clocks and eight
selected images match. PCM compared from each actual HAND clock through EOF is
exact: both clocks select sample441704, so there is no fitted shift, tolerance,
resampling or title-only crop. The pre-entry timing cause remains unresolved;
recorded-output equality does not establish exact bootstrap-cycle identity.

The earlier [136-byte mismatch](../../runtime/observations/pandora-cursor-inventory-boundary.json)
was an incomplete consumer/initialization model: inventory sprite DMA read
`$A000/$4000` at original `$653F8/$653FA`, beyond the buffer snapshots. A distinct
four-byte loader-file seed from `$453F8` and a 140-byte parent preserve this
observed dependency. Guest copies run before HAND; verification reads them
back. Comparison controls use the same explicit seed program/reservations,
including otherwise unused alternate seed backing, and ordinary host GO release.
There is no host seed/gameplay-memory injection or checkpoint restore. Original
deliberate reliance versus accidental values is unknown. No surrounding source,
font/bank45 layout, other seed or unknown-byte purpose is inferred.

All three normal profile builds still pass C/vasm agreement; original output
matches all 376,832 bytes, and the image/cursor payload hashes remain
`5a6f9695…` / `36c1a035…`. Current canonical exact receipt is `da3c4265…`.
306 focused seed/layout/runtime/comparison tests pass. All 126 canonical asset
intervals and 3,772 existing labels remain preserved; the explicit 256-byte
package threshold emits 86 assets and keeps 40 smaller intervals inline.
The known bank-51 pointer difference from the old patched experiment is retained
and explained by its existing typed fact, not masked for comparison.

[Service wiring](../../runtime/observations/pandora-layout-service-wiring.json)
forwards canonical `layout_id` through HTTP, restoration CLI, real MCP stdio and
the existing palette parameter editor. The isolated SDK 2.3.0 interface suite
passes 48 tests plus four server-route tests; the UI handler executes in Node.js,
not browser E2E. Refused exports do not become downloads/runtime qualification.

The superseded source patch builder is now retired: `symbolic_repairs`, ORG/CMPA
string substitutions and the alternate build CLI are deleted. The remaining
normal observer consumes native coordinates, uses shared fixed launcher/audio
options and an explicit phase-observation callback. A finite settled-title smoke
retains the exact boot ADF, HAND CPU/clock and pixels; 181 focused tests pass
(two optional synthetic live probes deselected), and 24 existing DMA frames
retain their identities/transfer totals. Historical source/receipts remain pinned.
The older single-region data relocation planner/build service has not yet been
consolidated; removing the target string builder does not claim that gate done.

[Frozen-plan reuse and performance](../../runtime/observations/pandora-layout-reuse-performance.json)
now records real sequential exports: cold image 203.70 s, two warm cursor exports
21.65/21.00 s, warm image return 22.29 s, clean cursor 290.25 s and cold original
191.87 s. Analysis invocation counts are `[1,0,0,0,1,1]`. Warm source and entire
packages equal clean exports, with all three C/vasm payload identities unchanged.
280 relevant tests pass (240 deselected). No new gameplay replay was necessary:
the executable bytes and native plans remain those already qualified above.

Reuse belongs to the existing disposable projection service under the target
lock. Native projection validates layout-only overlays and borrows the immutable
frozen semantic plan, owning row/declaration copies and changed typed root text.
It visits 49,650 rows and 6,425 declarations; the view owns 123,331,784 bytes,
excluding the baseline and JSON/package buffers. Native projection/package work
alone takes 8.90–9.44 s; this is not a constant-time or low-memory claim. Reported
RSS is the process's cumulative high-water (maximum 1,264,384 KiB), not a measured
independent warm peak. Changing source-mapped placement, materialized code,
bootstrap or machine profile rebuilds; invalid layouts refuse. Core facts/input
changes evict. Loaded Python/backend changes require restart rather than binding
old execution to new file hashes. Structure-macro exports retain the clean path.

Typed reference lookup now uses sorted interval endpoints, membership/ancestor
bitmaps and a prefix maximum moved end: build O(R log R), lookup O(log R + K),
O(R) space at the current explicit 16-region bound. Deterministic 4/8/16-region
fixtures take 4/5/6 point steps and 7/9/11 large-span steps, independent of span
byte length. This does not remove every package containment or legacy proof scan.
The exact executed diagnostic is published as
`amiga_reversing/tools/pandora_layout_reuse_benchmark.py`; its local clean-export
prerequisites and fresh output-directory requirement are in the receipt.

[Boot-only localization](../../runtime/observations/pandora-layout-preentry-clock-probe.json)
finds an 18-CCK difference already at BOOT before CMD_READ, and a -25,193-CCK
image-minus-original difference at natural HAND in those two probes. Both stop
before GO. This bounds the discrepancy to pre-entry execution, but does not
explain the controlled eight-CCK stop difference or prove disk/ROM causality.
Strict equality remains refused; no fitted delay or comparator allowance was added.

**Consolidation disposition:** the canonical layout module now owns finite
extent/domain/alignment checks, overlap and checked base-plus-offset translation.
The older single-region path calls these shared calculations; its independent
geometry expressions are removed. It remains a semantic adapter owning A500
Chip/Slow class choices, eight-byte Exec leases, access/alias/stack proofs,
generated fixed-width rewrite ledgers and initialization manifests. Those are
supported contracts, not an alternate placement engine or newly implemented M5
allocation. The adapter's instruction scans and inverse runtime-view enumeration
remain necessary proof/disambiguation work; forward mappings already use the
shared native runtime map. No duplicate Python placement model was introduced.
289 relevant tests pass, including explicit Chip/Slow boundary and exact-ledger
regressions. A fresh final original export takes 201.85 s and retains the exact
source/package; current C assembly equals the retained independent vasm output
for all 376,832 bytes. The historical benchmark receipt retains its pre-factoring code and
backend identities; this factoring is not claimed as a newly measured speedup.

The [milestone acceptance ledger](../../runtime/observations/pandora-layout-delivery-acceptance.json)
distinguishes delivered mechanisms from the remaining strict original-to-image
HAND-cycle condition. Both cold completions and bounded output comparisons are
available, but exact bootstrap-cycle identity is refused and its cause is not
established. Do not claim unconditional M0–M4 completion. The target string builder
is deleted; shared placement geometry now replaces the overlapping calculations.
Allocation/OS lifecycle remains M5–M6 and is not implemented. Its staged
continuation is authorized. The strict pre-entry criterion remains unfulfilled;
Richard directs independent functional progress. Do not reopen that timing probe
without new relevant evidence.

### Earlier mechanism batches (historical)

The following results retain their per-batch limits; their then-pending steps
are superseded by the current checkpoint above.

[Canonical adoption evidence](../../runtime/observations/pandora-canonical-layout-adoption.json)
records 25 API-applied and reviewed facts: copied image, cursor workspace and
children, display roles, and twelve exact receptacle pointer fields. Explicit
runtime reference points retain their address domain without inferring pointee
extents. All 376,832 original bytes match through C and independent vasm
(receipt `c799cb96d22106b9cb3f47c5759c59c13fcce885c056b7696a1599994a7f2ff9`).
All 126 asset identities and 3,772 existing labels are preserved. Seven missing
SDK companions were restored from the identical tracked include set so the
owned package is reproducible; its ownership guard remains enabled.

The reviewed exporter boundary cases now refuse split materialized views and
typed extents partially intersecting a moved region, rather than silently
emitting a stale ORG/address. The focused final layout/domain suite passes 72
tests (four deselected); the adoption suite passed 125 (four deselected).
Canonical bootstrap variants, target layout profiles and independent-block
qualification remain open. Cursor control initialization/DMA continuation and
the existing snapshot/palette containment must be resolved for that admission.
These facts do not classify previously unknown bytes or qualify an alternate run.

The subsequent bootstrap slice adds one canonical, input-identity-bound retained
prefix-copy contract and layout references to it through the same catalog/MAL
path. Native and disjoint-forward variants retain the initializer; the latter
permutates the contracted two-byte instruction's address-register operands using
the generated encoder in the frozen plan. Input hash, copied image/helper views,
staging bounds, register shape and instruction admission have explicit refusal
tests. A suppressed helper source ORG is distinguished from the actual copied
helper. Synthetic native/variant fixtures assemble independently with vasm;
336 focused integration tests pass (four deselected). No target profile, moved
workspace or new gameplay/output result is qualified by this mechanism batch.
See [the interface contract](../restoration-interfaces.md#retained-bootstrap-layout-contracts).

[Baseline/index evidence](../../runtime/observations/pandora-memory-layout-baseline.json)
records cold native artifact/package measurements and selection of the paired
cursor-sprite workspace for bounded constraint analysis. The first M1 mechanism
indexes existing materialized views in the native artifact; it removes the
per-query view scan and per-byte mapped-span scan while preserving conflicting
and valid aliases. 89 focused tests pass; the full nine-region projection and
native source package are unchanged. Span lookup takes two operations for 16,
349,040 and 8,388,608 bytes; 128/256/512 disjoint intervals take 8/9/10 operations.
The two single artifact timings (202.04 s and 169.49 s) do not establish an
attributable speedup. The region-by-instruction scan remains.

This is not first-delivery closure. Cursor control initialization/DMA continuation
and placement constraints remain under review; canonical layout selection,
base-plus-offset export, bootstrap migration and independent movement are still
pending. No new emulator run or source-layout transformation is in this batch.

The M1 placement batch adds optional region kind/parent facts, identity-preserving MAL
updates, versioned fixed-layout definitions and native placement resolution,
exposed by the existing shared query service. A valid placement explicitly retains
`export_ready: false`; no renderer/bootstrap/reference claim follows. Original
records remain compatible. Both workspace and display participate in this model;
there is no alternate Python placement authority. The legacy builder refuses
extended hierarchical definitions until the normal layout export owns them.
225 focused native/schema/history/catalog/service tests pass. With socket access,
the existing transport suite reports seven passes and one optional-MCP-SDK skip.
The interface tests require socket access; optional MCP SDK absence remains an
explicit transport-validation gap, not a passing skip. Pandora adoption and
M2–M4 acceptance are still pending.

The subsequent source-preview batch selects canonical layouts through the normal
native exporter. Runtime equates, DMA symbols and runtime ORGs use base/offset
expressions; scalar values and source coordinates retain their domains. Synthetic
original/moved fixtures assemble independently with vasm to the expected full
bytes, including an independently moved workspace. This is mechanism evidence,
not Pandora gameplay acceptance. Exports bind the native placement-plan hash and
remain explicitly `source_only_unqualified`. Package export now constructs one
owned native artifact for source and assets, replacing duplicate analysis rather
than adding a cache. Two reviewed importer omissions (mixed/scalar layout entries
and truncated numeric tokens) are fixed with native malformed-input regressions.
335 focused tests pass across layout/region/history, source/export/package and
service operations. No new Pandora payload or emulator result is claimed by this
batch; bootstrap/reference adoption and M2–M4 acceptance remain open.

## Decision and scope

Extend the existing native address-domain, runtime-view and render-plan model
into one canonical layout model. A region describes an object and its storage
requirements; a layout assigns placements; typed references connect source
sites to objects. The normal exporter renders a validated, frozen plan. It must
not infer pointers from numbers or patch rendered strings to make a layout work.

The first delivery models image/code, workspace and display regions canonically,
renders their supported addresses as base-plus-offset relationships, and uses the
normal source-package path for the exact original layout, the demonstrated
`$80000` image layout, and an additional layout moving at least one independently
placed workspace or display block. Both workspace and display kinds must be
represented naturally; physically moving both is not required. Reproducing the
image experiment alone is an internal validation step, not completed delivery.
Block selection requires actual reference, alias, lifetime and DMA constraints;
unknowns restrict specific blocks rather than defer the entire capability.
Runtime allocation and an OS-hosted exporter remain separate, gated work, not
consequences of changing ORG. No universal portability, arbitrary-base safety,
native C port, semantic completion percentage or delivery ETA is claimed.

This document is an architecture/roadmap, not another target fact database.
Canonical facts, Manual Action Log (MAL) and Decision Journal (DJ) continue to
own interpretation and review. The existing working exports and private runtime
evidence remain available during migration. Replacement has explicit deletion
gates; permanent competing production paths are not the intended outcome.

## What exists, and what the experiment actually established

The audit examined the following implementation, not just earlier proposals:

| Existing owner / concrete seam | Implemented scope and limitation | Disposition |
| --- | --- | --- |
| `src/m68k_ir.h`: `M68kMemoryRegionIR`, `M68kRuntimeViewIR`, `M68kRuntimeViewRelationshipIR` | Stable region identity and original extent; mapped/runtime-only distinction; storage-to-runtime materialization. Region array is currently bounded at 16, with persistent CPU RAM and a DMA flag, not a hierarchy or multi-region placement model. | Extend these native identities and projections; do not introduce a parallel Python region graph. Replace fixed-capacity storage when measured use requires it, with explicit limits meanwhile. |
| `amiga_reversing/disasm/memory_regions.py`: `validate_region`, `relocation_plan`, `build_derived_artifact` | Exact supported fields; persistent CPU RAM only; native plan delegation; fixed-width byte rewrite ledger and immutable local artifact. | Retain command/service boundary and strict admission. Migrate definitions with versioned defaults; consolidate layout materialization rather than adding another patch writer. |
| `src/m68k_memory_region.inc`: `memory_region_append_facts`, `platform_file_facts_v2_listing_artifact_memory_region_plan_json_alloc` | Accepted instruction accesses, bounded proofs, overlaps, single-region placement; A500 Chip/Slow address checks and eight-byte Exec lease assumptions. Overlapping source regions refuse a single move. | Reuse proof obligations and diagnostics. Move profile-specific placement/reservation policy out of the generic planner. Retire the single-region planning implementation after its supported cases use the shared layout planner. |
| `src/m68k_memory_region_addresses.inc`: `mr_mapped_span`, `mr_source_address`, `mr_operand_address` | Canonical mapping/provenance, not source-text matching. Contiguity currently checks each byte; region projection scans instructions per region. | Preserve meaning, replace repeated scans with shared interval/reference indexes and equivalence tests. |
| `src/m68k_memory_region_proof.inc`, `src/m68k_memory_pointer_liveness.inc` | Bounded address/frame/alias reasoning with explicit unsupported paths; not whole-program or IRQ/timing closure. | Reuse as evidence providers. Never make their current all-path proof a prerequisite for merely reproducing an accurately restricted original-layout export. Never interpret a refusal as evidence of unused memory. |
| `amiga_reversing/disasm/target_metadata.py`, `manual_actions.py` | Pointer field domains/groups, target equate domains/extents, operand presentations; revision-checked region create/remove history. Existing `source`, `runtime` and `app` uses must retain their actual semantics. | Extend existing commands/schema and replay; no direct history edits or replacement `entities.jsonl`. Add identity-preserving updates rather than remove/recreate churn. |
| `src/m68k_ir.h`: `M68kAnalysisAbstractRegion`; `target_metadata.py`: `AbstractRegionMetadata` | Named non-overlapping source-section ranges used by callable summary effects, distinct from runtime placement regions. Target equate extents and app/record owners also describe different facets of storage. | Link summary/owner ranges to canonical storage identities through their source/view mapping; do not promote an effect range to an allocation or discard its effect semantics. Retire duplicated extent authority only after summary references retain identity and all bounds checks agree. |
| `src/m68k_render_plan.c`, `src/m68k_render_plan.h`; [Proposal 037](037-render-planning-and-symbolic-source-closure.md) | Planned instructions, expressions and declarations; declaration/header closure has remaining work. | One resolver for operands, fields, tables, declarations and packages. Close the affected declaration cases here, not a second layout-specific renderer. |
| `src/m68k_source_package.c`, `src/m68k_source_export.h`; `amiga_reversing/disasm/source_export.py`, `source_package.py` | Native package/export path, asset extraction and assembler profiles. Package eligibility checks consult fixups, expressions, labels and rows. | Add a selected validated layout to this path. Do not hide references inside an INCBIN region containing layout-dependent pointer fields. Share indexes where profiling identifies repeated containment scans. |
| `amiga_reversing/disasm/restoration.py`: `memory_plan`, `memory_build`; CLI/MCP/UI adapters | Shared resident-service admission, current revision and exact verification gates. | Extend once; adapters only serialize requests/results. Old single-region operation may translate to a one-placement request during migration, then lose its duplicate implementation. |
| `amiga_reversing/disasm/derived_artifact.py`: `validate_manifest`, `verify_native_binding` | Payload/manifest identity and fresh native proof binding; syntax validation alone is not proof. `exec_allocabs` is the currently admitted reservation contract. | Reuse identity/staleness safeguards. Version the manifest for layouts; retain read/verification of historical receipts without retaining old build engines. Do not label assembly-time export an Exec allocation proof. |
| `amiga_reversing/disasm/optional_artifact.py`: `validate`, `verify_binding`; `amiga_reversing/tools/optional_patch.py` | Explicit fixed-size correction ledger; validates canonical instruction boundaries, not an interior relocated source map or bootstrap lifecycle. | Keep independent optional corrections supported. Do not repurpose this patch format as the layout authority or treat boundary validation as permission to strip initialization. Remove any layout-only adapter if introduced during migration; do not delete unrelated correction functionality. |
| [Proposal 044](044-runtime-memory-relocation-proof.md) and its audio-volume/keyboard work | Narrow mapped-region execution/proof; keyboard remains conditional. | Preserve bounded results and unresolved facts. Consolidate address resolution; do not revive the deferred proof programme as a prerequisite for fixed-layout export. |
| `amiga_reversing/tools/pandora_minimal_rebase_experiment.py`: `symbolic_repairs`, `build`, `observe` | Successful identity-bound experiment, but source `replace` anchors, target constants and a separate build path; not general native plan admission. | Retired after normal original/image/cursor builds and recorded cold/output evidence. `symbolic_repairs`, alternate source builder/CLI and process/phase monkeypatches are removed; the sole observer is `pandora_layout_runtime.py`. Historical receipts/script links are pinned. Strict original HAND-cycle refusal remains explicit and is not a build-path dependency. |
| `amiga_reversing/tools/pandora_rebase_output_compare.py` and focused tests | Strict output comparator, fixed known route and explicit normalization/bounds limits. | Reuse as integration acceptance, bind the normal export manifest instead of experimental text identity. No new emulator or general verification programme. |

Existing relevant tests include `tests/test_memory_regions.py`,
`tests/test_derived_artifact.py`, `tests/test_source_export.py`,
`src/test_m68k_render_plan.c`, `src/test_m68k_source_package.c`,
`tests/test_pandora_relocated_ending.py` and
`tests/test_pandora_output_comparison.py`. Their existing presence does not mean
the proposed cases below are implemented.

### Pandora migration fixture and non-negotiable distinctions

The [final output receipt](../../runtime/observations/pandora-relocated-output-validation.json)
and [runtime account](../validation/pandora-saved-route-app-watch.md) are the
baseline, with first failures retained in the earlier observation receipts.

* Original input is 376,832 bytes (`$5C000`), SHA-256
  `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
  Original C and vasm reconstruction remain exact.
* The demonstrated alternate profile is A500/ECS/PAL/68000 with **1 MiB Chip,
  512 KiB Slow, no Fast RAM**, not the original 512 KiB Chip/OCS profile. The
  experiment assembles at `$80000`; 7,059 accepted instruction extents retain
  their sizes. Fixed app base `$39FC`, workspaces `$65370`/`$653B4`, and display
  banks at `$70000` and `$78000` remain fixed. This is not relocation of every
  address or resource.
* The full file is staged at `$20000..$7C000`. The native 42-byte helper copied
  to `$300` moves only source `$00000..$55370` into `$80000..$D5370`.
  The final experiment changes the evidenced copy-direction comparison for
  this disjoint destination and retains the copy work/timing. Initialization
  enters at `$8046A`. Replacing that work with a branch completed gameplay but
  did not establish the required matched output.
* Source `$55370..$5C000` is an opaque **loader-only suffix**, initially backed
  at `$75370..$7C000`, later overwritten under the original lifecycle. It is
  not materialized at `$D5370`, not a hidden relocated asset fallback and not
  proven unused. Packaging/storage extent, assembly address and materialized
  execution extent must therefore be separate model properties.
* Existing MAL evidence names `bootstrap_to_fixed_execution_base` at source
  `$0` and `fixed_base_image_copy_stub` at `$28`, including the helper, interrupt/
  DMA quiescence and copy extent (actions at sequences 1014/1015 and comments
  following them). These are interpretations, **not an executable bootstrap
  replacement contract** today. `initialize_runtime_workspace` and subsequent
  trap/SR/vector/IRQ setup must not be stripped with the copy helper.
* Reviewed missed-reference families are the six restart receptacle pointers
  and six interaction-data pointers, player callback/self-jump, eight combat
  geometry references and two descriptors, and blank sprite/mask aliases.
  Examples: moved table `$C88AA` must reference `$C88C2`, not `$588C2`;
  `sprite_0005D5DE` denotes `blank_sprite_data`, not permanently `$5D5DE`.
  Original-base symbolic repairs already reproduce exact original bytes.
  These facts must become typed reference/declaration resolution, not a list
  of replacement strings transplanted into the exporter.

## Canonical design

### Ownership, coordinates and persistence

The native analysis owns discovered extents, references and materialization.
Evidence-backed manual corrections/configurations enter through revision-checked
analysis APIs, append MAL provenance and receive DJ review. An LLM may propose
them with source sites, producers/consumers and restrictions; it cannot establish
facts by editing emitted assembly or a private layout JSON. Target metadata
continues to carry supported import seeds, not a competing mutable authority.

Extend the existing schema with versioned region, layout, reference and bootstrap
records. Persist author intent in the existing target history; derive indexes,
resolved addresses, diagnostic sets and render plans from current facts. A layout
profile is a named canonical configuration referencing those identities, not a
second inventory of copied facts. Replaying old actions supplies only their
existing narrow defaults (persistent, CPU RAM, explicit DMA requirement); it
must not invent parentage, alias permission, relocatability or a phase lifetime.
Schema upgrades are tested, deterministic and explicit; no history rewriting.

Keep coordinate types distinct:

| Coordinate | Meaning |
| --- | --- |
| File/storage section + offset | Identity of input bytes and source annotations; invariant across placements. |
| Logical object/region ID + byte offset | Identity of referenced storage or code; independent of numerical placement. |
| Materialization/view ID + phase | Which storage bytes exist at a runtime location, including copied helpers and overlays. |
| Runtime address under a layout | Concrete CPU/bus address, checked against the selected machine profile. |
| Register-relative/app/record displacement | Offset within a proven base context; not automatically an image-relative pointer. |
| Fixed platform address | Hardware, vectors and explicit fixed memory; never rebased merely because its number falls in an image interval. |

A region has a stable ID, name, extent, optional parent+offset, content/storage
mapping, memory requirements and evidence/restrictions. Parentage describes
containment, not relocation coupling. An explicit placement-group constraint
can require shared translation or adjacency where consumers prove it. Otherwise
neighboring objects can move independently. Existing labels/field identities
survive; changing a placement cannot rename or change the meaning of an object.

Subregion declarations render, for example, `display_front EQU display_base +
front_offset`; source-owned content uses its canonical label where appropriate.
Image/code, workspace and display owners all participate in this first-delivery
model. Original placements may remain fixed where evidence requires them; a
base-plus-offset declaration alone does not establish permission to move it.
The expression tree carries the relation, not a string expression to reparse.
Emit only required declarations plus intentionally requested layout documentation,
in stable dependency order. Resolve genuine aliases to one object/offset; diagnose
incompatible names/domains. Do not turn this into an unrelated EQU/RS policy
rewrite or suppress useful hardware symbols.

### Constraints and valid overlap

Separate requirements from placements. Requirements include extent, alignment,
CPU addressability, Chip visibility for DMA, writable/executable use, fixed
address requirements and explicit distance/encoding constraints. Profiles supply
actual RAM apertures, reserved ranges, hardware capabilities and load protocol.
Do not conflate logical byte extent with allocator padding or an Exec lease.

Overlaps require one of three explicit relations: same storage identity via
alias/subregion, declared simultaneous shared storage with a compatible contract,
or a phase overlay with proved non-overlapping lifetimes and a handoff. Unrelated
conflicting writes refuse. A parent and its child are not a collision; two
different owners sharing bytes are not automatically compatible. An alias is
not a second allocation. A claimed lifetime needs initialization, consumers,
last-use/release and interrupt/DMA observer evidence; unknown lifetime is
conservatively overlapping. Do not infer free memory from absent references.

Distance constraints cover signed PC-relative operands/branches, indexed tables,
relative WORD entries, instruction alignment and representable DMA address bits.
Validate full access widths, not only pointer starts. Original export pins
instruction form/width, directive bytes, fill and branch choices. Alternate M1–M4
also pins the demonstrated widths; any overflow refuses with producer/target,
required range and source identity. No silent branch widening or relaxation.
A future explicit relaxation pass would need its own mapping, fixed-point size
resolution and acceptance; it is outside the first slice. Motorola-derived
encoding metadata remains authoritative, not mnemonic exceptions.

### References and deterministic rendering

Extend the existing planned expression/reference identity with target object +
addend + address domain/view, encoding and evidence. Required kinds are absolute
instruction operands; immediate address producers distinguished from scalars;
typed data/table pointers; relative entries; and grouped split DMA fields.
Preserve width, signedness, endianness, original encoding and any mutable/unknown
target restrictions. Pointer-looking unclassified WORDs/LONGs are not references.

Split high/low Copper/sprite/audio addresses share a single logical reference
with explicit field sites and bit slices. Validate pairing, carry behavior,
alignment, hardware bit availability and access phases. Do not independently
rebase halves or pair nearby numeric words heuristically. CPU writes which
construct pointers need their proven producer relation; unsupported computed or
mutable pointers remain named restrictions. Source pointers into aliases resolve
to the same canonical object, without discarding intentional offset aliases.

Pipeline: current native facts and selected profile -> indexed coordinate/
reference resolution -> placement and bootstrap validation -> frozen expressions,
declarations and materialization plan -> normal assembler-specific source package
-> assembly/verification receipt. Rendering consumes the frozen plan and adds no
facts. vasm is the first supported alternate-layout profile; Devpac and other
profiles must refuse unsupported cases rather than emit a numeric fallback.

Fixed hardware operands remain platform symbols. Fixed RAM may render a named
base+offset while still refusing movement. Raw assets stay byte-identical except
explicit typed relocation fields; packages split or render those fields instead
of hiding them inside immutable asset blobs. Deterministic ordering and identity
must be independent of insertion order, pagination or worker count.

Copied code has a storage identity and separate execution view; source references
and PCs are resolved in the correct phase/view. Self-modifying code requires
explicit write sites, writable extents, generated/reference fields and observers.
Unknown generated code or unresolved aliases block the affected transformation,
not original byte preservation. A full-image single-delta assumption is invalid
for the loader-only suffix and the helper executing at `$300`.

### Bootstrap and profile contracts

Model responsibilities before removal: load/decompress, copy/clear, stack and
workspace initialization, CPU mode/traps/vectors, interrupt/DMA ownership,
display/audio setup, and eventual cleanup. A replacement specifies source ranges,
entry preconditions, guaranteed postconditions, clobbers, resources, continuation,
materialization map and timing requirements. Each responsibility is retained or
replaced explicitly. Dependencies prevent deleting a copy routine while retaining
its implicit initialization assumptions. Merely naming a routine bootstrap does
not authorize stripping its bytes.

The first delivery includes `original`, a separately named fixed `$80000`
diagnostic profile, and a further evidenced fixed layout with an independently
moved workspace or display block. The first two retain the evidenced loader/copy
initialization sequence; the `$80000` profile has an explicit evidenced
copy-direction variant and ECS/1 MiB requirements. The additional block's legal
placement and initialization are selected from its actual constraints, not an
invented destination. It may use the original or known moved image placement;
the block's placement must not merely follow the image's translation.
Alternate builds need not equal original bytes, but each change must originate
in a typed reference, placement or reviewed bootstrap variant. Receipts enumerate
all changed fields/instructions, unmodified assets and remaining restrictions.

Assembly-time rebase solves symbols at build time and produces a fixed binary.
Runtime relocation instead emits fixups and a loader contract for an actual
allocated base. Runtime allocation additionally has failure, ownership, lifetime,
alignment and Chip requirements. OS-hosted operation also needs coherent hardware
takeover/release, vectors/interrupts/Copper/audio/blitter lifecycle, stack/mode and
error unwind. Exec allocation does not alone provide that lifecycle. A future
OS-hosted profile cannot reuse the game's supervisor/bootstrap teardown by
deleting a range and assuming the remainder is friendly.

### Diagnostics, identities and refusal

Every diagnostic names the layout/profile, canonical object/reference/source
site, competing view/owner if any, evidence and smallest missing obligation.
Distinguish conflict, unresolved provenance, unsupported encoding/profile,
out-of-bounds, missing bootstrap prerequisite, stale evidence and incomplete
analysis. Unknowns do not become null pointers, fixed constants or successful
skips. A user may retain a restricted original export; alternate export must
state exactly which unknowns prohibit which movement, without claiming global
safety from the successful route.

An export manifest binds binary, current canonical revision/schema, layout and
constraint set, bootstrap contract, native plan, exporter/backend and assembler
identity, assets and final package/payload. Reuse the existing immutable artifact
and consumed-identity checks. A changed placement, assumption or loaded backend
makes dependent receipts stale. Evidence files describe observations and hashes;
ROMs, media, raw checkpoints and PCM remain private. A historic manifest can be
read as history without being admitted for current execution.

## Performance and invalidation

Do not optimize by maintaining a second reduced-fidelity analysis. Build reusable
indexes in the resident native artifact over the existing facts. Let N be region/
view intervals, R references, I instructions and K returned overlap relations.

* Sorted, domain/phase-partitioned interval indexes resolve containment/overlap
  in `O(log N + K)` per query. A materialized contiguous span is proved by walking
  interval boundaries and consistent affine mappings, not its byte count.
* Build reference indexes by source site, target object/view and owning region
  in `O((N + R) log N + K)` time, with `O(N + R + K)` retained space. Batch overlap
  validation uses a sweep; unavoidable dense alias output can be quadratic and
  must be reported/bounded, not silently truncated.
* Plan a fixed-width layout by visiting affected objects/references once;
  ordinary resolution is `O(R log N + K)`, rather than a full I scan per region.
  Bounded control-flow/alias proof is a separate cost with explicit budgets;
  no claim that all proofs are logarithmic. Output/assembly/byte checks remain
  linear in emitted bytes plus assembler cost.
* Dependency edges link facts -> mappings/references -> expressions/declarations
  -> package chunks/receipts. A placement-only edit invalidates affected targets,
  incoming references, distance constraints and bootstrap products, not opcode
  discovery. A provenance/type edit invalidates its reachable users; profile
  changes invalidate legality and relevant render products. Ambiguous impact
  invalidates the whole plan. Compare incremental results to a fresh rebuild.

Current `mr_mapped_span` loops over every byte and resolves each separately;
`memory_region_append_facts` loops over planned instructions for each region.
`m68k_source_package.c` also has row-containment scans. These are audit leads,
not measured timing attribution. Instrument phase timing/counts/peak retained
bytes first. Avoid speculative global caches: index lifetime follows the native
artifact revision; any persisted derived cache must be content-addressed and
discardable, never authoritative. Share resolution with Proposal 037; follow
[Proposal 041](041-native-corpus-projection-engine.md) ownership boundaries and
[Proposal 039](039-corpus-build-performance-and-memory.md) deterministic resource
discipline without reopening their programmes.

M0 records a benchmark fixture specification: Pandora's 376,832-byte input and
7,059 accepted instructions; its actual current reference/interval counts;
original, known image and selected independent-block exports; cold artifact creation, warm layout-only edit,
one reference change and profile change. Record hardware/tool identities,
phase wall/CPU time, allocations/peak memory, output hashes and repeated-run
variation. Add deterministic synthetic 1x/2x/4x region/reference fixtures,
including nested aliases and sparse/dense overlaps. Report operation counts as
well as time so scaling failures are visible without machine-specific promises.
Accept the interval proof only when increasing span byte length at fixed interval
count does not increase mapping lookup count linearly. Accept reference indexing
when scan counts no longer grow as regions times instructions. Warm edits must
equal clean output and avoid unaffected discovery; report actual savings rather
than a target percentage. The initial design-only revision ran no performance
measurements; the implementation checkpoint above now supplies baseline and
index operation counts. The current checkpoint supplies scoped warm/clean
latency and exact-output evidence; no universal latency guarantee is claimed.

## Milestones and deletion gates

The table defines acceptance, not a claim that every mechanism exists. M0 and M1
have the partial implementation/evidence above; M2 has target profile builds and
M3/M4 now have the scoped runtime/output evidence above; frozen-plan reuse and
its measured performance are evidenced. Placement calculations are shared while
the proof/manifest semantic adapter remains supported. Exact original HAND-cycle
equality is still refused. M5 has the bounded implementation checkpoint above; M6 is not implemented. M1–M4
form the required first delivery. Original, known-image and independent-block
validation are incremental internal steps; M2 or M3 alone cannot close delivery.
M5–M6 are separately authorized continuation gates. Each batch
records mechanism delivered, target scope, tests/evidence, remaining restrictions
and removed implementation. Existing unfinished B07 files are independent and
remain untouched.

| Milestone / dependency | Deliverable and acceptance | Non-goals and deletion gate |
| --- | --- | --- |
| **M0: migration contract, block selection and baselines**; none | Inventory canonical image/code, workspace and display owners, reference families, bootstrap facts and exact experiment variants. Inspect concrete candidate blocks' CPU/alias/DMA/lifetime/initialization constraints and choose a supported independent move, recording specific restrictions on other blocks. Capture exporter/performance identities and focused fixtures; confirm existing exact/output receipts and private evidence availability without unrelated reruns. | No architecture implementation hidden in baseline collection. No experimental path removed yet. If no block can be justified, report the exact missing evidence and keep first delivery open; do not substitute image-only completion. |
| **M1: canonical layout planning**; M0 | Extend native region/view/reference schemas and revision-checked commands for image/code, workspace and display regions from the start. Model base-plus-offset subregions, independent placements, aliases, fixed RAM/hardware separation and indexed resolution. Include original, known-image and selected-block constraints. Test deterministic replay, valid containment/alias, invalid overlaps/alignments, stale edits, missing provenance and interval scaling. | No automatic placement solver or arbitrary overlays. Existing single-region service delegates shared placement/address calculations after positive/refusal parity. Retain its class/lease, proof and immutable-manifest semantics as an adapter; remove duplicate geometry rather than deleting supported capabilities. Historical receipt verification remains. |
| **M2: normal exporter and internal baseline builds**; M1 | Render image/code, workspace and display bases/subregions naturally in the frozen native plan. Admit reviewed Pandora pointer families; resolve image symbols, tables, split sprite/Copper references and fixed buffers. Encode loader prefix/suffix, helper and timing-preserving bootstrap variant. Generate original and `$80000` packages; original C/vasm bytes exact, alternate matches the qualified payload or every difference has a reviewed typed cause. Verify widths and full-file/suffix placement; test overflow, partial split pointer, raw-asset fixups, copied-code view ambiguity and missing initialization refusal. | This is an internal step, not first-delivery completion; the independent block move is required by M4. No runtime allocation. Delete `symbolic_repairs`, ORG/comparison string replacements and experimental source builder only after this normal path passes; a thin observation client may temporarily consume either manifest until M3. No permanent dual build mode. |
| **M3: baseline runtime qualification and experiment retirement**; M2 | Run the existing 576-phase normal-input saved-Earth route on the normal-export known-image payload, actual moved-PC/old-range guards and zero loss counters; qualify unheld cold completion and same-profile controlled output comparison. Retain failure receipts and scoped asset/DMA/output checks below. Wire CLI/MCP/UI to the same service with repeated/stale/non-pass parity checks. | Baseline qualification does not close first delivery. No unrelated proof/fuzzing work. Remove experiment-only build/config admission and duplicate observation address constants once the runner consumes the shared layout map. Keep historic receipts/comparator; preserve reproducible original and alternate exports before deleting obsolete fixtures/code. |
| **M4: independent block move and first-delivery acceptance**; M1–M3 and M0's evidenced block constraints | Export one additional legal fixed layout independently moving at least one workspace or display block. Both kinds remain canonical base-plus-offset regions even if only one physically moves. Validate all relevant producers/consumers, alias/lifetime/initialization and CPU/DMA address construction; run focused negative constraints, existing route, unheld cold completion and matched output acceptance. Observe the actual new block addresses and unchanged or separately selected image placement. Report exact restrictions for blocks not moved. | Delivery closes only with original, known-image and independent-block acceptance plus required debt-removal gates. No requirement to move both workspace and display, no invented arbitrary placement or all-buffer safety claim. Delete selected-block mapping constants only when shared facts replace their consumers. Missing evidence blocks that move and delivery closure, not truthful partial reporting. |
| **M5: runtime allocation/relocation continuation**; evidenced prerequisite contracts and explicit first-delivery limits | Format fixups from typed refs, loader/allocator failure/unwind and initialized materialization, Chip leases and actual-base observation. Positive and refusal fixtures plus relevant existing route/output qualification. | No claim of OS friendliness from AllocMem/AllocAbs alone. Retire fixed-address allocation assumptions in the shared path only after all admitted old cases have explicit policies; keep fixed-layout profiles as supported outputs, not duplicate engines. |
| **M6: OS-hosted profile continuation**; M5 and reviewed lifecycle contracts | Explicit resource takeover/release, vectors/IRQ/DMA/Copper/audio/blitter, CPU mode/stack and restoration on exit/error; reviewed bootstrap replacement; real host integration evidence on a declared platform. | Authorized staged continuation, not universal portability. Never strip bootstrap until each responsibility has a verified replacement. Remove superseded takeover shim only after normal exporter/runner owns the complete contract. |

### Managed continuation gates (2026-10-24)

The following records the completed bounded pre-GO investigation; current continuation is described above.
[HAND causal-boundary evidence](../../runtime/observations/pandora-HAND-causal-boundary.json)
reproduces the qualified stops at 35,525,509/35,525,517 for requested CCK
35,525,500. Both are the same boot-shim BNE at `$1628`; all 17 subsequent
observations have equal complete register sets/PCs and exactly eight CCK offset,
including entry into a ROM interrupt path. The guest bootblock and wait-loop
bytes are equal. The next branch/CMP boundaries are six/fourteen CCK apart, so
these target requests are not evidence of exact-clock stops. Neither run releases
GO or executes the game. Earlier BOOT-before-CMD_READ probes already differed,
but there is no continuous trace proving which earlier instruction or device
schedule caused the final offset. No game-source repair is justified by this
observation. No threshold change, calibrated padding, ROM/emulator rewrite or
new full walkthrough was performed.

The **strict startup gate stays unfulfilled**. Decide whether to accept the
explicit pre-entry deviation for the fixed-layout output claim, or scope a
separate pre-BOOT/trackdisk/interrupt timing investigation. Neither choice can
retroactively turn the strict failed receipt into a pass. Functional cold
completion, eight selected frames, bounded DMA and actual-HAND-to-EOF PCM remain
separate evidence; they are not all-path semantic or cycle-level equivalence.

The display initialization/alias and independent-placement gates below now have
the scoped E-layout qualification above. The remaining CPU workspace, runtime
allocation and OS lifecycle gates remain distinct; the completed timing probe
is not a prerequisite to their independently authorized progress.

| Next acceptance gate / dependency | Concrete evidence and implementation slice | Acceptance / stop boundary |
| --- | --- | --- |
| **M4 display initialization/alias contract**; existing canonical profiles | Follow `run_title_starfield_until_fire` and `start_seeded_zero_copy_blit`, the gameplay call to that clear, `select_initial_gameplay_bank1/bank0`, front/back/display app pointers, lower-screen Copper split and bitmap pointer words. The cold seeded clear spans `$70000..$7CD28`; bank0 is `$70000..$77D00`, bank1's demonstrated world prefix `$78000..$7D000`. Hit snapshot `$77D00..$78000` contains palette-input `$77FE0..$78000`; adjacency alone does not imply a relocation group. | Canonical facts must express proven containment/reuse, full clear/read/write extents and producer/consumer phases. Enumerate typed CPU and split DMA references and distinguish initialized loader-tail dependence. Review all edits before one generation. If a proposed bank move needs an unsupported split clear or an unproved seed/alias, report that exact prerequisite; do not move the prefix and leave initialization at its old address. |
| **M4 additional independent display placement**; preceding contract | Choose a legal Chip RAM placement from the actual whole-image, workspace, fixed-memory and DMA map; no address is preselected here. Change the evidenced block/group only through the normal exporter and typed references. Keep original and qualified cursor profiles reproducible. | Positive/refusal placement cases, actual new CPU/DMA targets, abandoned-range observations, zero event-loss counters, cold normal-input completion and same-state graphics/PCM comparisons. Inspect title, gameplay bank swaps, lower UI and snapshot/modal paths affected by the change. Keep current null-sprite exception explicit. Eight frames/sample DMA remain bounded coverage, not certification of every frame/path. |
| **M4 broader CPU workspace placement**; per-owner closure | Prefer an owner with proven consumers rather than moving the whole app envelope. Raster table `$39FC..$3B8C` is a candidate, not yet admitted: its 200 WORD producer and masked text Y indexing can reach beyond it for Y>=25. Keyboard state `$397C..$39FC` has a separate interrupt-facing lifetime; do not merge owners by adjacency. | Every affected indexed/cursor/absolute alias, interrupt consumer and initialization extent is accounted for, or explicitly restrict/refuse the move. Preserve unchecked-domain caveats instead of claiming arbitrary-input safety. A new move must add an independent placement obligation, not repeat the existing cursor route as new progress. |
| **M5 bounded allocation/loading slice**; first-delivery disposition plus explicit owner/fixup contracts | Start with one already-qualified owner and explicit CPU/Chip requirement, not a whole-game allocator. Separate fixed assembly-time placement from runtime base selection. Reuse native typed references to define actual-base fixups/materialization, including split DMA fields only when required. The existing fixed AllocAbs boot backing is not AllocMem portability. | Demonstrate at least two genuine legal allocator-selected bases, actual-base observations, identity-bound input/suffix/seed handling and complete owner lifetime. Inject allocator failure only as a declared loader failure test, never gameplay progression; verify failure return/unwind and no use-before-initialization. Preserve fixed-layout output and refuse unsupported reference forms. Implement the bounded slice only after its owner/fixup and failure contracts are explicit. |
| **M6 OS-friendly entry and exit**; M5 plus reviewed responsibility inventory | Map retained bootstrap responsibilities to replacements: CPU mode/stack, app globals, vectors/IRQ, DMA/Copper/audio/blitter, allocated resources, device/file ownership, exit/error paths. Name which remain game-owned and which return to Exec; do not strip startup based on its address range alone. | On a declared host/profile, loading and normal exit restore required hardware/OS ownership, stop DMA before releasing Chip buffers, restore vectors/interrupt state and free only owned resources. Qualify failure and cancellation paths and actual return to the host. A successful game in a boot shim or an AllocAbs reservation is not evidence of this gate. |

No percentage or ETA is assigned. Each implementation batch records the concrete
owner/reference family changed, exact output identity, observations gained,
remaining restrictions and next evidence question in this plan and its existing
receipts. Keep the nine unfinished B07 files unchanged; native-C conversion and
generic verification machinery remain outside these gates.

### Integration acceptance and limits

Reuse the existing evidence-producing route; do not count tests or extra fixtures
as gameplay progress. The baseline has 576 phases, 509 controller API calls
including release/cleanup, and 375 authored input events. The controlled pair
matches phase clocks and inputs, while the independent unheld cold run establishes
completion without the comparison clock fixture. Both use normal inputs, no
gameplay-state injection or restored checkpoints. Expected actual main-image PCs
shift by `$70000`; fixed helper/vector/hardware contexts are not false failures.

The comparison fixture is explicit startup provisioning: fresh reset/custom
direct-payload boot, natural HAND wait, common pregame CCK boundary, then the
existing HAND-to-GO host marker write at `$7FFF8`; no host game-register writes.
It is not original packed-disk boot or proof of identical pregame device state.
Keep the independent unheld run; no calibrated waveform shift may manufacture
an audio pass. Copy timing alone was insufficient without the common pregame
phase fixture. Changes to that contract require new evidence, not silent offsets.

Acceptance reuses asset identity checks (excluding enumerated typed reference
fields), eight exact RGBA frames and exact mixed 44,100 Hz stereo float32 PCM
over the declared post-GO interval. Existing eight points cover initial title
transition, overlay, proximity, Engineer transfer, first sonicdriver hit, console,
ending and settled title. The final baseline compares 24,726,568 float samples
without fitting, resampling, gain or omitted interior samples. Frame selection
must describe actual video state, not misread a per-star helper as a frame loop.

Six complete sampled DMA frames per layout are an additional bounded check,
not continuous DMA surveillance. CPU old-address observations are not DMA
coverage. Audio/Copper/bitplane/sprite checks and blitter physical Chip legality
retain their separate scopes. Eight unchanged original NULL sprite control reads
at addresses `$0`/`$2` remain an explicit bounds finding, **not certified sprite
asset safety**. The baseline verdict is `pass_with_original_bounds_findings`;
do not silently widen that exception to new invalid pointers. Eight matching
frames, sampled DMA and this route do not certify every frame, asset, optional
path, OS lifecycle or original OCS profile.

For the independently moved block, reuse these route/output gates and add the
specific CPU/DMA address observations required by its contract. Do not assume
the known image's sampled DMA coverage observes the new block's consumers.
Equivalent state/outputs do not alone prove all aliases relocated; combine them
with the selected block's typed reference ledger and explicit remaining limits.

## Decisions still requiring evidence

1. M0 must pin the exact canonical reference and bootstrap records needed for
   the existing alternate payload, including whether current typed facts suffice
   or need corrections. A successful patched export is not proof those facts
   already exist. No wider opcode or semantic reconstruction is presumed.
2. Choose stable profile/phase identifiers and schema migration details within
   existing MAL/native interfaces in M1. The proposed record contents above are
   a design contract, not an implemented public API spelling.
3. Retain fixed widths for the first slice. Any future instruction relaxation,
   overlay scheduler or general placement solver needs a separate justified
   decision rather than entering via convenience code.
4. Select the independent workspace/display block during M0, with its actual
   reference/alias/lifetime/DMA constraints. Implement its model with M1 and
   validate its move through M4. Unknowns must identify the affected block and
   missing evidence; they cannot blanket-defer both region kinds or turn
   image-only qualification into completed first delivery.
5. Runtime allocation and OS-hosted work are authorized continuation, requiring
   concrete owner/fixup and host/lifecycle evidence. Neither is needed to remove today's
   source-patching debt or to deliver the required original, known-image and
   independently moved-block layouts.

M0–M4 now have the scoped functional, source and performance evidence above;
strict original HAND equality remains unfulfilled. Richard has authorized M5–M6
continuation without per-milestone approval. Establish a concrete owner/fixup and
lifecycle contract for each bounded slice; fixed placement is not runtime
allocation, and AllocMem alone is not an OS-hosted game.

### M6 concrete bootstrap/ownership checkpoint (2026-10-24)

The source-owned helper is implemented and adopted by the normal exporter
([adoption receipt](../../runtime/observations/pandora-source-helper-adoption.json)).
It changes only the two declared startup entry operands, retains the 42-byte
helper and prefix initialization, and leaves the original C/vasm rebuild exact.
Cold gameplay qualification is pending in that receipt; it is not a DOS-game claim.
The fixed `$20000` input remains live.

A normal DOS resource probe acquired the current full input `$20000..$7C000`,
full relocated image `$80000..$DC000` and display `$E0000..$ED000` together,
but could not acquire keyboard `$6000..$6080`. It released successful claims,
printed `OOOF`, and returned through a second normal executable to the CLI
([reviewed evidence](../../runtime/observations/pandora-DOS-lease-feasibility.json)).
These are four explicit claims, not the complete ownership set or a stable
OS placement guarantee. The next launch prerequisite is a canonical movable
keyboard owner or refusal on an unavailable fixed claim. Low PRNG/body storage,
remaining producer/backing ownership and hardware/stack/vector restoration
remain separate obligations before genuine Pandora HUNK entry/exit. No demand
for identical pre-entry clocks is added to the OS-hosted acceptance gate.

The source-helper cold run subsequently completed all 576 phases, saved Earth
and escaped with HP49 at frame14351. Both event-loss counters were zero.
Actual helper PC `$20028`, then relocated PCs `$8046A`/`$8048C`, were verified;
the armed old-helper CPU data watch/entry sentinel did not stop this route.
All 509 controller-call records, phase names/statuses/frames and seven captured
PNG hashes equal the previous unheld run. This run captured no PCM; it adds no
audio equivalence or all-frame/DMA claim
([cold qualification](../../runtime/observations/pandora-source-helper-cold-qualification.json)).
It closes this bootstrap-helper slice, not the fixed-input or DOS exit obligations.

The next ownership prerequisite has a bounded implementation:
[seven-field keyboard admission](../../runtime/observations/pandora-keyboard-allocation-admission.json).
Native analysis enumerates five table-base operands plus inventory `+$40` and
pause `+$50`; all seven retain exact opcode/extension identities. The guest
consumer now admits a storage leaf with only these symbolic LONG fields and no
frame contract, children, numeric candidates or other encoding classes. Existing
frame-relative CPU owners still require their immutable guards. Executable
fixtures include both interior aliases, staged-byte refusal and exact failure
unwind; 56 relevant checks pass. This is preparation for normal DOS ownership,
not a claim that the keyboard has already moved in a DOS-launched game.

### M6 bounded owner composition (2026-10-24)

[Native planning checkpoint](../../runtime/observations/pandora-atomic-OS-owner-planning.json):
PRNG is a separate seventeenth owner; native/API/MAL capacity is now bounded at32
instead of conflating unrelated storage to fit16. C/ctypes sizes agree. Original
source was regenerated and C plus independent vasm remain exactly `70480017…`.
The numeric runtime-address contract replaces the old hand-authored PRNG seed
address expression; its symbol and encoded WORD field remain intact. Active
layout exports derive its region-relative address from canonical ownership.

The atomic planner composes explicit allocator returns in one canonical layout,
inherits children, checks rounded eight-byte backing, input/helper/fixed extents,
every signed field reach and cross-owner fixup/guard disjointness. No placement
search or guest mutation occurs. 130 relevant checks pass; separate capacity/
bootstrap checks overlap and are not an additive total. Guest lease acquisition,
full staged-input identity, apply-once patching and complete failure/exit unwind
remain required before DOS game entry.

The first prospective DOS combination was correctly refused: PRNG `$1998`
intersects existing mask bank18. The finite next storage set is:

| Owner | Existing original extent / evidence | Small next action |
| --- | --- | --- |
| Title stars | `$400..$7E8`; two MOVEA.L immediate bases at source `$D56/$D8E` | Separate owner and retain LONG fields; no instruction growth needed. |
| Low masks18/21/30 | `$10F0..$3820`; existing generated-mask write extents | Model the supported group and its constructor/table references, then move it with the other returned owners. Do not remove protection to admit PRNG. |
| High generated masks | `$7D000..$7FEB0`; existing constructor write extents | Acquire its fixed backing before takeover. Write bounds do not alone close DMA lifetime/reads. |

Middle generated masks remain inside the retained `$20000..$7C000` input backing;
no bank45 layout speculation is introduced. PRNG's two retained bytes remain
unknown rather than invented zero seeds. These identified owners, the existing
input/image/display/cursor claims and actual takeover/exit restoration define the
next DOS launch gate; this checkpoint is not an OS-game or all-memory pass.

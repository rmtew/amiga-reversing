# Pandora full source restoration

> Behavioural validation is tracked in [Proposal 045](../proposals/045-behavioural-validation.md).
> Its B01–B10 commitments distinguish framework capability from target coverage;
> its CPU and DMA results have bounded scopes. B07 and generic capability work
> are paused: the current priority is original-layout source restoration and the
> closeout questions below. No commitment closes on documentation alone.

Status: inventory and plan reviewed; startup, world-command, runtime initialization,
input, selected world tiles, scene mask banks, selected title records and audio
input records reviewed. The full restoration and
alternate-layout gates remain open. Initial baseline: merged `22e55bb5`.
This is a work plan and derived evidence index, not another semantic fact store.
Canonical native facts, Manual Action Log and Decision Journal remain authoritative.
The full-game objective is not satisfied by this plan or a few runtime checkpoints.

## Deliverables and separate correctness gates

1. **Original layout:** reproducible generated source for every byte of the
   376,832-byte unpacked payload, with C and independent vasm full-file equality
   to SHA256 `70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
   Unknown material stays explicit raw data until evidence justifies interpretation.
2. **Readable reconstruction:** source-coordinate coverage map with nonoverlapping
   intervals accounting for all payload bytes; subsystem boundaries, entry and
   exit contracts, data layouts/resource extents, meaningful names and comments.
   Each interpretation has source evidence and review status. Counts distinguish
   accepted code, candidate code, structured data and uninterpreted data; inferred
   function ownership and legacy annotations are never silently promoted to proof.
3. **Supported alternate layout:** explicit address-domain model and constraints,
   relocatable internal references including code operands and pointer tables,
   unchanged hardware/OS absolute references, and validated placement of mutable
   state, copied code and chip-visible resources. Build at a second legal base,
   inspect the actual changed relocations, and execute that rebuilt image under
   bounded, identity-checked observations. Successful original self-relocation
   alone does not meet this gate. Arbitrary-address portability is not promised.

Original disk image and loader parity are explicitly out of scope. The existing
packed/unpacked inputs and legal Kickstart can support analysis; no input download
or unrelated tennis changes are required.

## Current closeout scope (2026-10-21, after `e19817e4`)

The original-layout byte reconstruction is done. Readable, reviewed source is
still open; alternate-layout execution and a native C game port are separate
outcomes. The following is the prioritized closeout list, not another fact
store. Its rows must finish with canonical evidence or an explicit, reviewed
limitation; another renamed field alone does not close a row.

| Priority / required original-layout question | Existing evidence and present limit | Acceptance condition | Next bounded action |
| --- | --- | --- | --- |
| 1. Reconcile the remaining byte partition | [Completeness baseline](pandora-completeness-baseline.json), [held-frame restoration](../validation/pandora-player-held-frame.json) and [charge-table restoration](../validation/pandora-combat-charge-plane-layout.json). The baseline's 6,446 unknown bytes predates the held-frame edit; existing weapon-table ownership also needs reconciliation with emitted rows. | Every old unknown interval is reconciled against current canonical ownership; accepted code/data and retained raw exceptions are distinguished, with no inferred padding or duplicate credit. | Compare the baseline interval list with the existing current catalogue and source locators. Recompute accounting with the next necessary source build, not an expensive generation solely for a percentage. |
| 2. Adjudicate the three dominant raw spans | Source `$52..$456` (1,028 bytes), `$B4A8..$C3A8` (3,840), `$39DC8..$3A338` (1,392): 6,260 of the old 6,446 unknown bytes. [Dominant-range evidence](../validation/pandora-dominant-payload-evidence.json) and [access observations](../../runtime/observations/pandora-unknown-span-tracing.json) distinguish touched stack/scratch addresses from original byte purpose. | Positive producer/consumer or allocation evidence supports each interpretation, or a reviewed bounded opaque exception states exactly what remains unknown. No whole-span stack reservation, original scratch-seed meaning, or unused bank suffix is inferred from limited accesses. | Review the existing negative static results and retained consumers for an explicit disposition. Scratch-seed and bank-30 probes are exhausted under current constraints; reopen only on identified new evidence. No new capture is authorized by this list. |
| 3. Resolve or bound control-flow and field ambiguities | [Indirect-dispatch audit](../validation/pandora-indirect-dispatch.json) has 22 reviewed sites, eight initially without known targets; later callback contracts add bounded knowledge, not global target closure. The old baseline lists 32 unresolved field accesses: four known LEA cursor advances, the already-reviewed `$790A` low-byte WORD probe, and 27 dynamic indexed operands. Native unresolved status does not mean these five lack an interpretation. | Each listed site/access has a current interpretation, supported original caller/target or field bounds, or an explicit dynamic limitation. Source/runtime aliases and copied or stack-spliced control flow must not acquire false function boundaries. | Reconcile the eight original sites (`$932`, `$11DE`, `$11F2`, `$6694`, `$7A00`, `$83FE`, `$93F4`, `$4DC2A`) with subsequent canonical summaries; retain the existing five non-dynamic interpretations and select only dynamic consumer bounds still lacking evidence. Preserve mutable-target caveats. |
| 4. Review subsystem source contracts | Existing status sections cover startup/IRQs, world commands/objects and scripts, input/timing, graphics/copper/blitter, UI/inventory/trading/terminal, NPC/combat/endgame, and audio/sequences/samples. Full function, object and resource denominators are unknown; candidate counts are not reviewed counts. | Each of these subsystem groups has an indexed entry/exit, important shared-state and data/resource boundary review, with remaining interpretation questions explicitly listed or accepted. Existing mature work is audited rather than renamed again. | Walk the existing canonical summaries and status by these groups; select only a connected missing contract or layout with concrete producers/consumers. Do not turn generic labels or purpose-byte gaps into a rename quota. |
| 5. Audit source presentation and deliver the original-layout closeout | [Latest source audit and exact receipt](../validation/pandora-audio-control-symbols.json), canonical Manual Action Log and Decision Journal. Byte equality cannot detect lost symbolic meaning or incorrect prose. | Reproducible full C/vasm equality for all 376,832 bytes; labels and evidenced symbolic operands preserved; no unexplained ownership conflicts or possible code/data confusion hidden by raw emission; remaining raw exceptions and semantic limits reviewed and visible. | After substantive edits, review the source diff and final exceptions against rows 1–4, then run one final exact build. Report original-layout acceptance separately from the M4/M5 gates. |

Rows 1–5 bound the closeout questions, not the investigation effort. The complete
semantic denominator and size of unresolved dynamic target sets have not been
established, so neither an overall completion percentage nor an ETA is supported.
A row needing unavailable evidence must retain its precise blocker; it must not
be silently replaced by an endless queue of cosmetic batches.

**Optional polish:** remaining internal branch names and the 47 numeric audio
control positions, formatting preferences, unused EQU/RS emission and font
presentation do not by themselves block original-layout closeout. Fonts and
EQU/RS policy remain outside the current scope. B07 reduction, a broader DMA value
oracle and UI capability work remain paused unless a concrete restoration
question establishes a need. Historical “next B07” recommendations are superseded.

**Separate work:** M4/M5 still require supported address domains, copied and
self-modifying code, chip-visible resource/alias constraints, and an actual
alternate-layout candidate executed at the changed addresses. No alternate-layout
safety is implied by exact original output. A native C game port has no accepted
complete translation or measured implementation denominator; the C disassembler
and generated CPU backend are tools, not a C port of Pandora. Neither that port
nor disk/loader parity is part of the original-layout closeout above.

## Initial inventory (historical baseline)

The initial shared-service snapshot reported 7,087 accepted instructions, 230 function
candidates, 2,096 symbols, 3,925 typed references, 3,364 CFG edges, 411 typed field
uses and 156 analysis review items. Counts are a dated snapshot, not completion
percentages. The complete byte partition is recorded in the status report; semantic resource
boundary reconciliation remains pending.
The 990 existing actions include 989 legacy/unassessed records. Preserve them.

Native startup evidence already distinguishes source location from execution
location: source `0x00..0x27` disables custom interrupts/DMA, discovers its own
load location with PC-relative addresses, copies 42 bytes from `0x28..0x51` to
absolute `0x300`, and jumps there. That helper chooses a forward or backward
byte copy according to source/destination ordering, copying `0x55370` bytes to
fixed `0x10000`, then transfers to `0x1046A`. The direct contract initially loads
at `0x20000`. These facts establish a fixed execution layout and overlapping-copy
requirements, not arbitrary-base support. The relationship between copy length
and the full payload tail must be audited before defining relocated layouts.

## Milestones and acceptance

| Milestone | Work | Acceptance evidence |
| --- | --- | --- |
| M0: complete inventory | Account for every byte; reconcile accepted code runs, data ranges, padding/raw regions, resources and overlaps. Inventory functions, indirect edges, pointer encodings and existing history. | Coverage partitions sum to 376,832 with no gaps/overlap; counts separate semantic certainty from byte coverage; every unresolved interval has a bounded next question. |
| M1: startup and relocation | Recover boot entry, copied helper, fixed execution continuation, stack/application state, interrupt installation, memory clearing/copying and all startup address assumptions. | Reviewed names/comments and register/memory contracts; copy source/destination/size/direction proven; code writes and resource tail classified; full exact rebuild. Runtime probes only for unresolved reachability/state. |
| M2: global program structure | Map startup-to-title-to-gameplay transitions, interrupt/callback ownership, shared application state, dispatch tables and lifecycle transitions. | Entry points and reachable dependencies indexed; each indirect transfer resolved with evidence or retained with a specific unknown; no next-label function-boundary assumptions. |
| M3: dependent subsystems | Restore graphics/copper/blitter, UI/text/inventory, world/map/object logic, input/timing, audio/sequences/samples and resource formats in dependency order. | Reviewed coherent batches with data bounds, call/data consumers, comments explaining behavior/invariants, exact original rebuild and relevant focused tests. Existing mature annotations are audited, not replaced indiscriminately. |
| M4: alternate-layout model | Classify internal relocatable addresses versus hardware/OS/fixed RAM/serialized values; model split regions, signed widths, alignment, relative tables, copied/self-modifying code and DMA restrictions. | Generic framework representation only where an actual recurring capability is missing; target-owned layout constraints; original-layout exactness unchanged; second-base relocation expected-value checks include positive and negative cases. |
| M5: alternate-base execution | Build and run an actually different supported execution layout with canonical source mappings. | Proven relocated code/data/table references and unchanged hardware/OS addresses; identity checks against relocated rebuilt bytes; verify actual PC, data and DMA addresses belong to the alternate layout and startup does not copy back to `0x10000`; attach layout configuration and source mapping to receipts; dependency-led behavior probes beyond original startup; forbidden placements rejected. |
| M6: full-game closeout | Audit remaining raw bytes, anonymous code/data, unresolved edges, comments, resource ownership, conditional paths and reverse-engineering claims. | Every payload region accounted for; remaining semantic uncertainties explicitly adjudicated rather than hidden; subsystem acceptance ledger complete; original exact rebuild reproducible and original-layout closeout questions above adjudicated. Alternate-layout acceptance remains a separate M4/M5 gate; a handful of checkpoints cannot close either scope. |

M4 may proceed alongside later M3 batches once startup/address constraints are
known. Alternate-base binary bytes are expected to differ where relocation is
required; only the original layout must match the original SHA exactly.

## Completion ledger and uncertainty

Maintain a derived per-subsystem/interval ledger referencing canonical actions,
source keys, review decisions and verification receipts. Each row records
unknown/hypothesis/reviewed/verified status, its blocker and next evidence question;
the ledger does not independently grant acceptance. Byte coverage is not semantic
completion. Original-layout closeout may retain explicitly reviewed bounded raw
exceptions as described above; this does not grant them a semantic interpretation.
For alternate-layout acceptance, opaque resources need understood ownership,
extent, consumers and relocation behavior. Unresolved
control-flow targets, conflicting source/runtime identities, unknown pointer
encodings, possible code misclassified as data and unexplained address-dependent
writes block full-game or alternate-layout completion. Report such blockers
explicitly rather than marking the containing subsystem complete.

Plan review approved inventory/startup work. Its requested ledger and actual
alternate-PC/data/DMA checks are incorporated above. Initial audit has also found
legacy handler labels with possible source/runtime coordinate confusion; those
records remain preserved pending dispatch/instruction corroboration.

## Batch protocol and general framework improvements

Use shared revision-bound operations: inspect → evidence-bearing catalog action
→ canonical regeneration → exact verification → question-led probe where needed
→ independent review → durable review decision. Capture old histories and preserve
existing bytes. Undo/redo appends corrections; never hand-edit generated `.s`.
Publish logical reviewed draft PRs; merging requires a new request for this task.

For a framework gap, demonstrate the recurring problem and identify its existing
owner before implementation. Extend native typed facts, shared service or existing
evidence/history models, with generic synthetic and preferably second-target
regressions. Migrate callers and remove superseded code when applicable. Keep
Pandora addresses, names, structures and layout assumptions in target-owned facts
or configuration. Do not add a second analysis pipeline or speculative abstraction.

Observed opportunities to review:

- Coverage queries: existing native region ownership/code runs/data descriptions
  need compact, revision-bound byte-accounting access. Inventory must not scrape
  generated assembly or pretend instruction queries describe all payload bytes.
- Evidence matching: symbols with absent source coordinates currently compare
  equal to legacy actions with absent subject coordinates, falsely attaching
  unrelated evidence. Require concrete identities, retaining valid zero offsets;
  generic null/partial-identity regressions will guard the fix.
- Candidate naming: native function candidates can retain generated aliases even
  when accepted rendered symbol facts have meaningful names. Assess canonical
  identity/provenance before changing projection; names alone cannot measure
  semantic completeness.

Major unresolved ambiguities that change supported layouts or user-facing scope
will be reported with the competing evidence. Missing analysis is analysis work;
it is not automatically a missing framework feature. Keep logs bounded and avoid
full instruction traces. Preserve the resident server between target operations.

Opaque asset packaging/INCBIN export is owned by a separate parallel task. This
work may classify asset boundaries and relocation needs, but will not implement
a competing exporter or edit its assembler/source-packaging path. Adoption will
follow independent review and coordinated integration.

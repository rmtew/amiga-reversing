# Proposal 017: Evidence-Driven Analysis Protocol for Pandora Reversal

Status: active / repurposed for ongoing Pandora analysis-protocol work.
The 017-027 closeout remains the historical gate snapshot for the previous
post-hardening pass: at that point no command-backed, verifier-backed,
exact-round-trip source-converging Pandora mutation remained. The next 017
phase keeps that knowledge but shifts the forward focus to an Evidence-Driven
Analysis Protocol: one shared auto-analysis, evidence, decision, command, and
verifier model for turning report-only reversal facts into verified source
progress.

Proposal 015 is the historical Pandora trial archive. Proposal 016 hardened the
loop surfaces found during that trial. This proposal owns the next focused
Pandora reversing pass using those hardened surfaces.

## Target

- Game target: `targets\amiga_disk_pandora-1988-firebird`
- Sub-target: `amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`
- Rendered source:
  `targets\amiga_disk_pandora-1988-firebird\targets\amiga_raw_pandora_3e1ee0f1_bk_00_000000e8\pandora_3e1ee0f1_bk_00_000000e8.s`

The sub-target is resettable unless a later issue explicitly promotes target
state as canonical. Do not treat timestamp-only `.project.json` changes or
local legacy Manual Action Log churn as meaningful progress.

## Purpose

Build the working specification for evidence-driven auto-analysis and review.
The protocol must let deterministic analysis, a human, an LLM agent, CLI
commands, and a future web UI resolve reversal candidates through the same
model:

1. select one exact use or range;
2. inspect a structured evidence packet;
3. see blockers and conflicts explicitly;
4. accept, defer, or reject a scoped fact;
5. expose mutation only after the accepted fact satisfies verifier gates;
6. prove the rendered source changed only inside the selected scope and still
   round-trips exactly.

Pandora is the proving target. The work is successful only when it moves
Pandora source toward human-quality reconstructed source or removes a measured
blocker needed for that progress.

## Forward Direction

017 now owns the next Pandora progress path instead of creating a new proposal.
The historical 017 pass showed that discovery is no longer the main blocker.
Reports can find useful candidates, but too many candidates stop as
report-only because the system lacks one reusable way to carry evidence into a
scoped, replayable, verifier-backed decision.

The core forward move is the **Evidence-Driven Analysis Protocol**. Evidence
review is the ambiguity-resolution layer of that protocol, not a separate UI or
manual-tooling feature. The five concrete candidate families below are starter
aspects used to prove the protocol against real Pandora work.

## Working Specification

This proposal is the master working specification for this area. New 017 work
must reference it and either implement its current model or update the proposal
when implementation evidence proves the model wrong or incomplete.

Rules:

- no issue defines a private model outside this proposal;
- model changes happen before code, or in the same commit as the code that
  proves the need;
- post-implementation observations update this proposal when they affect the
  protocol;
- old implementation may be non-conforming while a surface is still
  transitioning, but new work must not deepen ad hoc paths;
- legacy state support is temporary transition scaffolding and must be deleted
  when a surface cuts over to v2.

## Evidence-Driven Analysis Loop

The protocol defines the top-level analysis loop:

```text
load target
seed binary, platform, format, and target facts
run deterministic analysis
auto-accept decidable facts
emit review packets for ambiguous facts
actor resolves one or more packets
record scoped decisions in the Decision Journal
replay decisions into the C fact graph
rerun deterministic propagation to fixed point
project render effects and verify
repeat
```

Auto-analysis may accept only protocol-decidable facts. A fact is decidable
when it has stable identity or range, deterministic replayable evidence,
explicit scope, no conflicts, known propagation effect, verifier support,
defined negative-safety cases, and can be reproduced from current inputs.

When any of those pieces is missing, auto-analysis emits a blocked or
reviewable evidence packet instead of guessing. The stop condition is fixed
point under the current binary, target config, platform knowledge, active
decisions, analysis code, and render policy.

## Clean v2 Stack

Implement the protocol as a clean parallel v2 slice beside the current
analysis path, then cut over and delete the replaced surface. Side-by-side
development is scaffolding, not a user-visible compatibility mode.

```text
binary inputs
platform knowledge
target config
Decision Journal
    -> C evidence-driven analysis state
    -> C fact graph
    -> evidence packets
    -> command gates
    -> render effects
    -> verifier results
```

Reuse stable fundamentals: binary loading, M68K decode/spec machinery, target
paths, platform knowledge, round-trip verification, and source-rendering
primitives where they fit. Current reports are discovery aids and regression
references only; they are not protocol schemas or durable truth.

Replace workflow/state semantics: Manual Action Log architecture,
ad hoc accepted/probable statuses, report-specific command gates, scattered
verifier logic, implicit derived-state ownership, and any C/Python boundary
that prevents clean fact graph and replay semantics.

Cutover is per surface. Each surface has exactly one default implementation at
all times. A v2 slice may run internally while old behavior remains default;
once v2 owns a surface, default behavior switches to v2 and old code is
deleted.

The concrete rewrite scope is not fixed yet. The next active step is a
research and architecture inventory issue that maps the current analysis stack
before any v2 implementation slice starts. That research must identify current
behavior, C/Python ownership, platform-specific hooks, fact/state sources,
reports, commands, render/export, verifier flow, hidden coupling, reuse/replace
candidates, and the first safe implementation slice.

017-031 completed that inventory and narrows the first v2 slice. Current target
loading, binary source descriptors, C decode/facts-v2/render primitives,
platform facts, source export, and round-trip reproduction are reuse surfaces.
The rewrite boundary is the workflow/state model: Manual Action Log semantics,
report-private candidate schemas, report/catalog gate duplication,
Python-owned evidence truth, scattered verifier result shapes, and implicit
derived-state ownership must not become the protocol interface.

The next Decision Journal path is intentionally sequential:

1. `017-034` makes `decision_journal.jsonl` durable and append-only, but still
   inactive.
2. `017-035` exposes explicit validation/inspection for humans, LLMs, CLI, and
   API callers through `reversing_loop decision-journal-report`, including an
   in-memory `--dry-run-record` validation path that never appends or replays.
3. `017-036` replays accepted/deferred/rejected/superseded decisions into an
   in-memory projection, surfaced through `decision-journal-report`, without
   mutating C facts or feeding command gates.
4. `017-037` lets the selected RSSET packet/report consult that replayed
   projection as a read-only `journal_decision_evidence` lane, while keeping
   mutation blocked.
5. `017-038` reports the selected RSSET mutation gate/readiness contract while
   keeping mutation disabled.
6. `017-040` records or blocks the real durable Pandora journal accept required
   to make the selected RSSET gate ready.
7. `017-039` enables the selected RSSET mutation only if durable evidence,
   command support, render support, verifier support, and exact round-trip gates
   are all present and `017-038` reports ready after `017-040`.

Later issues in this chain are planned, not frozen. Each completed slice must
refresh the dependent issue checklist if implementation evidence changes the
protocol.

Current ownership is split:

- Python owns project path resolution, source descriptors, orchestration,
  listing cache management, command catalog transport, Manual Action Log
  append/projection, report formatting, planner ranking, and verifier
  composition.
- C owns binary/object decode, facts-v2 propagation, `M68kFactIR`, render
  lookup, source analysis/render planning, emitted listing/source JSON, and
  source profile counters.
- Platform knowledge is split between C platform facts, target metadata, and
  agent-facing Markdown knowledge files.

The first implementation slice should define a shared read-only evidence packet,
selected identity, blockers/conflicts, and decision result schema. Use
Pandora RSSET `rsset-raw-a6:022E` at `s0:000006E4` as the primary packet because
it has high source-quality payoff and remains safely blocked by missing accepted
app-base evidence. Use current A5 and immediate-reference reports as regression
packet shapes: A5 proves accepted/already-recorded and verifier-rich states;
source-offset immediate `s0:000009A6` proves a blocked policy/verifier state.
Do not add mutation until the RSSET packet can prove selected-use path/lifetime
scope, selected A6 base identity, explicit empty conflicts, render effect, and
exact round-trip gates.

Research issues must not start the v2 implementation. They may add narrow
inspection tooling only when needed to answer the research, and must not change
default behavior, refactor opportunistically, or delete old code before a
cutover plan exists.

## Tutorial: One Evidence Review

Start with one exact candidate, not a broad family. For example, Pandora still
has `rsset-raw-a6:022E` blocked at `s0:000006E4`.

The report should not just say "maybe app slot". It should produce a packet
with stable identity, evidence lanes, blockers, and conflicts:

```json
{
  "candidate_id": "rsset-raw-a6:022E",
  "selected_use": {
    "segment": "s0",
    "address": "000006E4",
    "operand_id": "op1",
    "text": "022E(a6)"
  },
  "status": "blocked",
  "blockers": ["missing_accepted_base_evidence"],
  "evidence_lanes": {
    "base_setup": [],
    "path_lifetime": [],
    "same_displacement_context": ["app-slot-like uses exist"],
    "conflicts": "unknown"
  }
}
```

A reviewer, LLM, or CLI command then resolves the missing evidence. If the
scope is proven and conflicts are empty, the decision is recorded as a manual
fact, not as a vague note:

```json
{
  "action": "accept_fact",
  "fact_type": "rsset_app_base",
  "selected_use": "s0:000006E4:op1",
  "base_id": "pandora_app_base_a6",
  "scope": {
    "kind": "selected_use_path_lifetime",
    "setup": "s0:...",
    "use": "s0:000006E4"
  },
  "conflicts": [],
  "evidence": ["rsset-report:rsset-raw-a6:022E"],
  "render_effect": "selected_operand_only"
}
```

Only after that accepted fact exists should the command catalog expose a
mutation:

```json
{
  "command": "rsset.binding.bind",
  "enabled": true,
  "requires": [
    "selected_use_identity",
    "accepted_base_evidence",
    "explicit_empty_conflicts",
    "exact_round_trip"
  ],
  "writes": ["Decision Journal"],
  "renders": ["one selected operand"]
}
```

The verifier then proves the full chain:

```text
decision-journal: accepted fact exists
semantic reload: selected use consumes the fact
rendered source: only expected source line changes
negative checks: same-displacement uses remain blocked
round trip: exact
```

This is the shape every 017 item should converge on. The candidate-specific
parts change, but the selected-use identity, evidence packet, scoped decision,
command gate, verifier, and replay behavior stay common.

## Protocol Primitives

The protocol needs these durable primitives:

- **Selected identity:** exact instruction operand, range, table, string, or
  code island. No "all matching literals" or "all same displacements" without
  an explicit scoped rule.
- **Evidence lanes:** structured facts such as xrefs, CFG path, base setup,
  lifetime, dataflow, target range classification, active decision state, and
  rendered-source effect.
- **Blockers and conflicts:** explicit missing proof, overlap, clobber,
  competing meaning, stale fact, duplicate action, or unsafe render state.
- **Decision actions:** accept scoped fact, defer with reason, or reject
  candidate. Decisions must be replayable from the Decision Journal.
- **Command gate:** mutation commands appear only when accepted evidence and
  action-specific verifier requirements are present.
- **Render effect model:** before/after output is known before writing, and is
  limited to the selected scope.
- **Verifier layers:** Decision Journal state, semantic reload, generated source,
  negative safety checks, and exact round-trip.

## Decision Journal

The clean durable state is a per-target **Decision Journal**, not the current
Manual Action Log as architecture. The current log may be used as temporary
seed evidence while developing v2, but once a surface is processed into v2 the
old storage, adapters, compatibility paths, and legacy semantics must be
removed.

The journal records compact actor decisions and accepted roots. It does not
store every derived analysis fact.

```json
{
  "schema": "evidence-decision/v1",
  "id": "decision-01HX...",
  "prev": "sha256:...",
  "actor": {
    "kind": "human | llm | auto-analysis | tool"
  },
  "action": "accept_fact",
  "candidate_id": "rsset-raw-a6:022E",
  "selected_identity": {
    "target_id": "amiga_raw_pandora_3e1ee0f1_bk_00_000000e8",
    "segment_id": "s0",
    "address": 1764,
    "operand_index": 1
  },
  "fact_type": "rsset_app_base",
  "scope": {"kind": "selected_use_path_lifetime"},
  "evidence_refs": ["packet-rsset-022e-000006e4"],
  "conflicts": [],
  "render_intent": "enables_render"
}
```

Journal rules:

- append-only with explicit supersession, not mutable edits;
- generated ids plus a journal hash chain are enough for v1;
- actor metadata is audit context, not validity proof;
- rationale text is optional and only for judgment not captured structurally;
- decisions carry both candidate id and selected identity, with selected
  identity as the durable anchor;
- evidence packets are regenerated by default; tests and validation artifacts
  may snapshot them;
- invalid replay decisions remain in the journal but are excluded from active
  facts with structured diagnostics;
- stale or invalid decisions surface as reviewable packets when actionable.

## Fact Graph and C Query API

The authoritative fact graph should live inside the C analysis state. Python
owns file IO, orchestration, CLI/API serialization, and presentation, but not
semantic truth.

```text
Python reads Decision Journal
Python validates basic schema/hash chain
Python calls typed C decision APIs
C applies active decisions to analysis state
C reruns propagation to fixed point
Python queries C for packets, gates, render effects, and verification results
```

Conceptual C API:

```c
ArEvidencePacket ar_query_evidence_packet(ArAnalysis *analysis, ArIdentity id);
ArCommandGate ar_query_command_gate(ArAnalysis *analysis, ArIdentity id);
ArReplayResult ar_apply_decision(ArAnalysis *analysis, ArDecision decision);
ArVerifyResult ar_verify_decision(ArAnalysis *analysis, ArDecisionId id);
```

Consumers use typed queries, not raw graph traversal. The graph exposes
semantic fields, stable identities, blockers, conflicts, evidence references,
render effects, and verifier results. UI/CLI formatting, grouping, labels, and
prose explanations stay outside C.

## Candidate States

The protocol states are:

- `accepted`: active fact under current inputs and verifier rules;
- `reviewable`: enough evidence exists for an actor to decide now;
- `blocked`: required evidence, tooling, or protocol support is missing;
- `deferred`: an actor reviewed it and intentionally left it unresolved with a
  recorded reason;
- `rejected`: suppressed as not useful or invalid under the current model;
- `superseded`: replaced by a later decision.

Uncertainty is represented as blockers, conflicts, and defer reasons, not as
fuzzy accepted confidence. Ranking is allowed for work ordering only; it never
proves truth.

State ownership:

- auto-analysis may create blocked, reviewable, rejected, and auto-accepted
  decidable facts;
- humans and LLM reviewers may accept, defer, reject, or supersede through the
  Decision Journal;
- planners execute command gates only and do not change evidence truth;
- verifier failure emits diagnostics and required review/supersession work; it
  does not silently rewrite the journal.

## Render Intent and Policy

Facts declare render intent:

- `renders`: should improve source output when projection support exists;
- `analysis_only`: supports analysis or suppresses work but does not render;
- `enables_render`: feeds later facts that render.

Render-intended facts include operand semantic references, labels, range
classifications, typed data declarations, and structured comments when source
syntax cannot safely express the fact. Analysis-only facts include temporary
CFG/dataflow facts, conflicts, rejected/deferred packets, scores, and stale or
superseded decisions.

Fact types define allowed and unsafe render forms, with platform/target
refinements:

```json
{
  "fact_type": "a5_hardware_ref",
  "render_intent": "renders",
  "allowed_render_forms": ["symbolic_operand", "structured_entry_comment"],
  "unsafe_forms": ["address_mode_changing_operand"]
}
```

Structured comments are first-class render projections when operand syntax is
unsafe, misleading, or assembler-hostile. They are not the default substitute
for symbolic operands. During build-out, an accepted fact may be missing render
projection because implementation is incomplete; that is a transitional
blocker, not a final semantic state for supported render-intended facts.

## Starter Aspects

1. **RSSET/app-base accepted evidence.** Prove one raw A6 use, preferably
   `rsset-raw-a6:022E` at `s0:000006E4`, from blocked report-only candidate to
   accepted `rsset_app_base` fact and one scoped source improvement. The proof
   must include selected-use identity, path/lifetime scope, selected base id,
   explicit `conflicts: []`, semantic reload, no unrelated A6 changes, and
   exact round-trip.

2. **Source-offset immediate provenance.** Prove one source-offset immediate,
   preferably `s0:000009A6` / `addi.w #4224,d1`, by showing operand identity,
   literal width/signedness, possible meanings, landing range, later dataflow,
   conflicts, accepted interpretation, scoped render effect, and exact
   round-trip. Same-literal-only evidence must remain report-only.

3. **A5 path/lifetime evidence.** Prove one A5 hardware/base use from blocked
   candidate to accepted scoped fact. The packet must show base setup, computed
   base expression, custom/app-base delta, CFG reachability, no A5 clobber,
   lifetime end, conflicts, selected render effect, and exact round-trip.
   Linear listing-state evidence alone must never expose mutation.

4. **Decision evidence diff/replay.** Make Decision Journal state auditable as
   protocol data. A reviewer should see each accepted/deferred/rejected fact,
   its evidence inputs, rendered-source effect, verifier layers, stale or
   superseded state, and replay result after semantic reload.

5. **Orphan/code-island acceptance.** Bring code islands, tables, strings, and
   data ranges into the same protocol. Evidence lanes should include xrefs,
   control-flow reachability, overlaps, range classification, and downstream
   render effect. Ambiguous islands become explicit deferred facts, not hidden
   speculative code or raw data.

These aspects are not five unrelated features. They are the first five proof
surfaces for the common protocol.

## Future Human UI

A later proposal can build an Evidence Review Workbench over this protocol. It
should not invent separate evidence rules. It should present the same packet in
one place: selected use, evidence lanes, conflicts, render preview, verifier
state, and scoped accept/defer/reject actions.

The useful UI goal is insight and resolution without forcing the reverser to
open many disconnected reports. The base 017 goal is the protocol that makes
that UI, CLI use, and LLM use consume the same evidence and produce the same
replayable decisions.

## Completion Standard

017 is complete when Pandora demonstrates the protocol across multiple starter
aspects:

- at least one report-only candidate becomes an accepted scoped fact;
- any source mutation is command-backed, verifier-backed, and exact-round-trip;
- the rendered source improves only inside the accepted selected scope;
- unsafe neighboring candidates remain blocked with clear reasons;
- the Decision Journal can be replayed to recover the accepted facts and their
  rendered effects;
- the same evidence packet shape is usable from reports, commands, tests, and
  future UI.

## Issue Protocol

Every future `017-*` issue is a protocol-delta slice against this proposal. It
must not define a private model. Use this structure:

```md
## Proposal Context
- Source proposal: `docs/proposals/017-evidence-driven-analysis-protocol.md`
- Protocol area:
- Current proposal state:
- Desired proposal state after this issue:

## Protocol Delta
- Adds:
- Changes:
- Replaces:
- Deletes:
- Leaves out of scope:

## Default Behavior
- Unchanged, v2 internal only:
- Switched surface to v2:
- Deleted old surface path:
- User-visible behavior:

## Pandora Proof
- Target candidate:
- Evidence packet expected:
- Decision behavior:
- Command gate behavior:
- Render effect:
- Verifier/round-trip:

## Implementation Slice
- C fact graph/query work:
- Python/API/report work:
- Journal/replay work:
- Renderer/verifier work:
- Tests:

## Research Coverage
- [ ] Target load lifecycle traced, or marked out of scope with reason.
- [ ] Post-load auto-analysis hooks traced, or marked out of scope with reason.
- [ ] C analysis ownership mapped, or marked out of scope with reason.
- [ ] Python orchestration ownership mapped, or marked out of scope with reason.
- [ ] Platform-specific extension points mapped, or marked out of scope with reason.
- [ ] Fact/state sources inventoried, or marked out of scope with reason.
- [ ] Derived-state/replay assumptions inventoried, or marked out of scope with reason.
- [ ] Reports/candidate generation traced, or marked out of scope with reason.
- [ ] Command catalog/planner flow traced, or marked out of scope with reason.
- [ ] Legacy Manual Action Log flow traced, or marked out of scope with reason.
- [ ] Render/export flow traced, or marked out of scope with reason.
- [ ] Verifier/round-trip flow traced, or marked out of scope with reason.
- [ ] Pandora RSSET/A5/immediate surfaces mapped, or marked out of scope with reason.
- [ ] Hidden couplings/risks listed, or marked out of scope with reason.
- [ ] Reuse/replace candidates classified, or marked out of scope with reason.
- [ ] First implementation slice recommended, or blocker recorded.

If research discovers another relevant subsystem, add it to this checklist
before continuing. The issue is not complete until the expanded checklist is
signed off or explicitly marked out of scope with reason.

## Research Review
- [ ] Second pass checked file/function coverage.
- [ ] Cross-references searched for missed hooks.
- [ ] Findings were checked against Pandora current surfaces.
- [ ] Proposal updated with model corrections and rewrite-scope findings.
- [ ] Next issue scope follows from the inventory.

## Required Sign-Off
- [ ] Proposal context checked before implementation.
- [ ] Protocol delta implemented as described, or proposal updated.
- [ ] Default behavior impact verified.
- [ ] Old code deleted, or deferred deletion blocker recorded.
- [ ] Evidence packet shape tested.
- [ ] Decision/replay behavior tested where applicable.
- [ ] Command gate refuses unsafe mutation.
- [ ] Render/verifier/round-trip checked where output-affecting.
- [ ] Pandora proof recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
```

Sign-off lives in the issue doc. Bulky command output or target evidence goes
in validation artifacts. Commit messages summarize visible improvement.

Before implementation, update the proposal if the issue changes the model.
After implementation, update the proposal with corrected model details,
unexpected blockers, and out-of-scope follow-ups discovered by the work.

## Post-016 Rules

- Use `docs\agents\reversing-loop.md`.
- Use 016 outputs as guidance:
  `immediate-ref-report`, `a5-hardware-report`, selected-action traceability,
  evidence-led orphan-code scoring, and Review dialog items.
- Treat A5 hardware report output as non-durable linear listing-state
  candidate evidence only. It cannot drive hardware register rendering until a
  real accepted path/lifetime scope exists.
- Exact round-trip remains mandatory for output-affecting actions.
- Prefer structured durable facts over comments: data roles, app/global slot
  names, typed fields, code/data/string/table classification, callback targets,
  interpreted references, and ownership-backed generated descendants.
- Do not perform generic class/address renames such as `string_XXXXXXXX` as
  Pandora progress. If generic styling is desired, log framework policy work.
- Use query/report APIs before full `.s` scans. Full source rendering is for
  broad orientation, final comparison, or fallback when cheaper surfaces cannot
  answer the question.
- Profile slow phases instead of normalizing slow loop progress. Fix only
  measured bottlenecks needed for the active Pandora work.
- Record deferred findings in this proposal as they are encountered, then
  either resolve them or promote them to issues.

## Historical Issues

These issues document the completed post-hardening pass and reopened verifier
hardening. The next active `017-*` issues should be written from the Evidence
Review Protocol order above.

1. `017-001`: post-hardening baseline and candidate queue.
2. `017-002`: immediate runtime-reference triage and promotion path.
3. `017-003`: A5 path/lifetime provenance before hardware rendering.
4. `017-004`: evidence-led Review Item source-quality pass.
5. `017-005`: RSSET/app-slot refinement from accepted evidence.
6. `017-006`: measured loop-performance fixes from Pandora work.
7. `017-007`: operand-level interpreted immediate-reference command and
   verifier.
8. `017-008`: CFG-backed A5 path/lifetime proof report.
9. `017-009`: RSSET candidate discovery for remaining raw A6 operands.
10. `017-010`: planner treatment for low-value representation candidates.
11. `017-011`: A5 accepted-evidence hardware render gate report.
12. `017-012`: immediate-reference report mutation gate.
13. `017-013`: A5 hardware-reference command and verifier.
14. `017-014`: A5 custom-register base-offset report identity.
15. `017-015`: A5 zero-displacement hardware-ref rendering.
16. `017-016`: A5 accepted-provenance verifier status.
17. `017-017`: A5 `intreq(a5)` focused hardware-ref mutation.
18. `017-018`: A5 `bltafwm(a5)` focused hardware-ref mutation.
19. `017-019`: remaining render-safe A5 hardware-ref sweep.
20. `017-020`: immediate-reference report candidate write policy.
21. `017-021`: A5 report suppression for already-recorded hardware refs.
22. `017-022`: current gate closeout.
23. `017-023`: tracked Pandora render evidence for 017 source changes.
24. `017-024`: A5 symbol-delta/address-mode-preserving rendering.
25. `017-025`: accepted RSSET app-base evidence for raw A6 candidates.
26. `017-026`: source-offset immediate-reference policy and verifier path.
27. `017-027`: rerun gate and independent 017 regression review.
28. `017-028`: A5 entry-comment source-output verifier hardening.
29. `017-029`: RSSET accepted-evidence conflict-shape hardening.
30. `017-030`: Pandora exercise pass over the reopened 017 surfaces.

## Historical Gate State

The final 017-027 rerun after `017-028`, `017-029`, and `017-030` recorded
this Pandora surface:

```text
immediate-ref-report:
  safe_to_mutate=false
  candidate_count=9
  command_candidate_count=0
  report_only_candidate_count=9
  remaining source family: source_offset

a5-hardware-report:
  safe_to_mutate=false
  accepted_path_lifetime_evidence_count=20
  existing_manual_state_uses=20
  command_candidate_count=0
  entry_comment_uses=1

rsset-candidate-report:
  safe_to_mutate=false
  candidate_count=125
  use_count=994
  status_counts:
    blocked=124
    already_recorded=1
  top_active_candidate=rsset-raw-a6:022E
  top_active_missing_gates: missing_accepted_base_evidence
  top_active_accepted_base_evidence_count=0
  top_active_catalog_state=report_only_same_displacement_app_slot_not_base_evidence

inspect:
  candidate_work_count=0
  round_trip_status=exact

run-one dry run:
  action=null
  planner_status=no_candidate
  planner_message=no supported source-converging command candidate
  ranked_candidates=225
  remaining candidates are 221 generic class/address data-symbol names and
  4 low-value literal representation candidates
```

Final verification:

```text
focused A5 entry-comment tests: 3 passed
focused RSSET candidate-report tests: 10 passed
cmd /c src\precommit.bat: passed
round_trip_status: exact
```

This is the final 017 gate snapshot after the reopened work:

- `017-024`: implemented exact address-mode-preserving A5 rendering for the
  existing zero-displacement accepted ref by projecting a generated entry
  comment instead of changing operand syntax.
- `017-025`: removed the command catalog fallback that treated selected
  app-slot context as synthetic RSSET base evidence. Same-displacement/generic
  app-slot context remains report-only until real selected-use
  `rsset_app_base` provenance exists.
- `017-027`: reran the current gates after the reopened 017-025 fix; no
  command-backed, verifier-backed source-converging mutation remains.

Review reopened the track before final closeout:

- `017-028`: the A5 entry-comment verifier must prove the generated source text
  contains the generated comment, not pass from listing/UI comment state.
- `017-029`: accepted RSSET base evidence must require an explicit empty
  `conflicts` sequence; missing or malformed conflict state is not accepted
  evidence.
- `017-030`: after those fixes, do a demonstrable Pandora editing pass over the
  related source-converging surfaces, not just the new verifier changes. It
  should use the real target to exercise review/action discovery, candidate
  reports, command catalog entries, accepted/edit-blocked paths, verification,
  and source evidence capture before rerunning `017-027`.

The reopened track is now complete. `017-027` reran the gate set after
`017-028`, `017-029`, and `017-030`; no source-converging mutation remains
available without new evidence or new policy/tooling.

The deferred `017-006` performance issue remains conditional; use it only when
a measured slow phase crosses its investigation threshold during active 017
work.

## Recommended Order

Begin with `017-031`: a research and architecture inventory issue. It must map
the current analysis stack, double-check coverage, update this proposal with
rewrite-scope findings, and recommend the first implementation slice. Default
behavior must remain unchanged.

After that research issue, turn the five starter aspects into the next
`docs/issues/017-*` sequence, with the Evidence-Driven Analysis Protocol as
the shared implementation target. Each issue should name the protocol primitive
it advances and the Pandora demonstration it will use.

Use this order unless implementation evidence forces a better one:

1. complete the research inventory and proposal correction pass;
2. define the shared evidence packet, selected identity, blockers/conflicts,
   and decision result schema;
3. wire one read-only Pandora report through that packet shape;
4. add accepted/deferred/rejected Decision Journal records for that packet;
5. gate one mutation command from accepted protocol evidence;
6. add verifier layers for Decision Journal replay, semantic reload, rendered-source
   effect, negative safety, and exact round-trip;
7. repeat the same protocol shape across the remaining starter aspects.

The current parallel queue after the RSSET/app-base slice is:

- `017-041`: source-offset immediate provenance packet;
- `017-042`: A5 path/lifetime protocol packet refresh;
- `017-043`: Decision evidence diff/replay audit;
- `017-044`: orphan/code-island evidence packet;
- `017-045`: protocol issue sign-off enforcement.

Prefer the first starter aspect that can demonstrate the whole chain with the
least speculative policy. If no mutation is safe, complete the read-only
packet, blocker, and defer/reject path, then move to the next starter aspect.
Use `017-006` only when a measured slow phase blocks normal protocol work.

## Acceptance Criteria

Each protocol issue must include:

- a concrete Pandora candidate or candidate family;
- a structured evidence packet with stable selected identity;
- explicit blockers and conflicts;
- scoped accept/defer/reject behavior recorded in Decision Journal state where
  applicable;
- command gating that refuses mutation without accepted evidence;
- verifier coverage for Decision Journal replay, semantic reload, rendered output,
  negative safety, and exact round-trip when output-affecting;
- a visible source-quality improvement, or a documented blocker that the
  protocol exposes cleanly and safely.

Support-code fixes are accepted only when tied to a concrete protocol blocker,
verifier gap, command/catalog identity issue, or measured slow span. They need
focused tests and a rerun of the original Pandora report or action that exposed
the issue.

## Living Notes

Add meaningful observations here while working. Keep entries short and promote
repeatable work to `docs\issues\017-*`.

- 016 A5 output is useful for choosing candidate families, but it is explicitly
  not durable accepted hardware-base evidence.
- 017-001 baseline: hygiene and inspect are clean for
  `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`;
  Review Items are clear, round-trip status is exact, and no baseline candidate
  mutation was performed.
- The selected next family is `017-002` immediate runtime-reference triage.
  `immediate-ref-report` found concrete report-only candidates, including
  runtime/source-offset immediates, but planner writes remain blocked until
  verifier-backed immediate-reference interpretation exists.
- `a5-hardware-report` is deferred to `017-003`: it found many probable A5
  custom-register candidates, but all observed entries remain non-durable
  listing-state evidence with no accepted path/lifetime scope. Hardware register
  rendering remains blocked.
- The selected-action dry run currently prefers a mechanical printable byte
  immediate rendering action. That command is available, but it is lower value
  than reference/path provenance work and is not selected as 017 progress.
- 017-002 triage attempted the strongest immediate-reference family. The report
  found 10 accepted, conflict-free candidates; the best visible source-quality
  candidate is `s0:00006138` (`addi.l #458752,d0`) because it computes
  `app_text_cursor_ptr` from a runtime-address base. Promotion is blocked:
  there is no operand-level command to record a verified interpreted immediate
  reference, and no projection/semantic reload verifier for that rendered
  immediate-reference target. The report now exposes those gates structurally
  and keeps `symbolic_reference_allowed=false` and `rendering_allowed=false`.
- 017-003 checked the A5 hardware family without rendering. The concrete
  selected use was `s0:000004A6` (`move.w d0,dmacon(a5)`), reached from the
  linear A5 definition at `s0:00000498`. The report now gives this a concrete
  `linear_listing_between_a5_writes` scope, but its path/lifetime verdict is
  still `unknown` because no control-flow proof shows A5 remains `_custom` on
  every path to the use. Hardware register rendering remains blocked.
- 017-004 found no current Review Items or candidate work from the Review
  dialog source for the Pandora sub-target, so there is no durable Review Item
  to resolve. Review-count reduction is not treated as progress.
- 017-005 found no accepted RSSET/app-slot candidate in the current Pandora
  planner surface. A dry run selected `representation.character` after inspect
  returned no candidate work; no `target.rsset_region.*` or
  `rsset.binding.*` candidate was available. RSSET command/verifier plumbing
  exists, but this target currently lacks accepted source evidence for a new
  binding or field refinement.
- 017-006 did not identify a performance blocker. The active Pandora report and
  dry-run commands observed during this pass completed in roughly 8-9 seconds,
  below the issue's 30 second investigation threshold, so no speculative
  performance refactor was started.
- Follow-up unblockers were promoted from the blocked 017 pass:
  `017-007` for immediate-reference mutation/verifier support, `017-008` for
  CFG-backed A5 path/lifetime proof, `017-009` for RSSET candidate discovery,
  and `017-010` for planner handling of low-value representation candidates.
- 017-007 added the durable operand-level `immediate_ref.interpret` path for
  accepted interpreted immediate references. The report now exposes command and
  verifier support only when the candidate is accepted, conflict-free,
  runtime-address backed, and fits the selected operand width. Plain
  source-offset matches and the byte-sized `$523C` candidate remain report-only
  because address-shaped constants can also be masks or counts.
- 017-007 promoted Pandora `s0:00006138` (`addi.l #458752,d0`) after the
  command/verifier gates were present. The source export now renders
  `addi.l #imm_ref_h0_00050000_rt_00070000,d0`, with an xref to source offset
  `$50000` / runtime `$70000`, and the next instruction stores the result to
  `app_text_cursor_ptr(a6)`. The Manual Action Log advanced from 37 to 38 at
  head hash
  `924b8bd47d84ad8aabb01484808bf54f2e3434540480dd1b6fd1583f3cf5fa60`.
- 017-007 verification initially exposed a cache-ordering gotcha: command
  execution invalidates the listing cache, so render/xref verification must
  reopen the listing before checking projected operands. After reopening, the
  manual-log, semantic reload, rendered-source, xref-projection, and round-trip
  layers all passed; round-trip remained exact. Persisting a refreshed tracked
  `.s` export is separate from local Manual Action Log state.
- 017-010 changes the autonomous planner, not the manual command catalog:
  printable-byte `literal_representation` candidates from listing syntax are
  still reported but are now marked low value and skipped as autonomous
  progress unless accepted semantic evidence is attached. A Pandora dry-run
  now returns no action instead of selecting `representation.character`; the
  planner output keeps those skipped representation candidates and the existing
  generic class/address data-symbol blockers visible.
- 017-009 added a read-only `rsset-candidate-report`. Pandora reports 125
  grouped A6 displacement candidates from 994 uses; the top group is
  `rsset-raw-a6:022E`, but it is blocked by `missing_accepted_base_evidence`.
  The report exposes `rsset.binding.report` and catalog-visible
  `rsset.binding.bind` context while keeping `safe_to_mutate=false`; no target
  mutation was performed.
- 017-008 extends `a5-hardware-report` with a conservative straight-line CFG
  path/lifetime report. Pandora now classifies the selected `s0:000004A6`
  A5 use as `accepted_custom_base` with source evidence
  `a5-custom-cfg:h0:00000498->000004A6:op1:d0096`, but hardware register
  rendering remains blocked because verifier consumption/render support is
  still separate work.
- 017-011 makes that A5 rendering blocker explicit in report output:
  `cfg_path_lifetime_report` remains `safe_to_mutate=false` and
  `rendering_allowed=false` even when accepted path/lifetime evidence exists,
  and now names the missing `a5_hardware_ref.interpret` command and
  `a5_hardware_ref_state` verifier gates. Exact round-trip remains required
  for any future output-affecting hardware-register render mutation.
- 017-012 fixes a report-safety issue found during post-commit review:
  after the Pandora runtime-address immediate was promoted, the remaining
  `immediate-ref-report` candidates were accepted source-offset matches without
  command payloads. The report now exposes a `mutation_gate` and keeps
  top-level `safe_to_mutate=false` unless at least one command-backed
  `immediate_ref.interpret` candidate remains.
- 017-013 adds the durable A5 hardware-reference command/verifier path. Accepted
  CFG A5 uses now advertise `a5_hardware_ref.interpret` only when they carry
  accepted path/lifetime evidence, and the verifier requires Manual Action Log
  state in `a5_hardware_refs`, rendered symbolic operand state, and exact
  round-trip. Linear listing-state A5 candidates remain non-durable report
  evidence.
- After 017-013 support was present, Pandora `s0:000004A6`
  (`move.w d0,dmacon(a5)`) was recorded as durable A5 hardware-ref state from
  accepted evidence `a5-custom-cfg:h0:00000498->000004A6:op1:d0096`. The
  verifier passed manual-log, semantic reload, rendered-source, and exact
  round-trip layers. This did not require a broad Pandora mutation run.
- 017-013 post-commit review exposed a report correctness blocker:
  `lea _custom+dmaconr,a5` was being treated as exact `_custom`, so `(a5)` was
  misidentified as `bltddat` instead of effective offset `$0002` / `dmaconr`.
  017-014 now carries `custom_base_offset` through A5 evidence and command
  payloads, accepts signed displacements only through valid effective offsets,
  blocks out-of-range effective offsets, and keeps zero-offset evidence ids
  stable.
- The first post-017-014 mutation, Pandora `s0:0000045C`, recorded durable
  `dmaconr` A5 hardware-ref state and passed manual-log and semantic-reload,
  but failed rendered-source projection. A forced `dmaconr(a5)` render changes
  the address mode because A5 already points at `_custom+dmaconr`, so 017-015
  keeps zero-displacement/non-zero-custom-base A5 refs semantic-only until
  exact symbol-delta rendering exists. Focused Pandora validation now blocks
  `s0:0000045C` with that reason while leaving `s0:000004A6` command-backed.
- The next safe A5 mutation selected Pandora `s0:000004AA` and rendered
  `intena(a5)` exactly, but the generic provenance wrapper rejected
  `source_evidence_status=accepted` even though the A5 action-specific verifier
  passed. 017-016 adds `accepted` to the generic accepted-provenance statuses;
  revalidation of action `manual-5f2c6ead224244dabec3cadaff7d2d98` now passes
  manual-log, provenance, semantic-reload, rendered-source, and exact round-trip
  layers.
- 017-017 continued the focused A5 path with the next unrecorded command-backed
  Pandora candidate, `s0:000004AE`, from evidence
  `a5-custom-cfg:h0:00000498->000004AE:op1:d009C`. Action
  `manual-c2202ab8723a407eb25ebccbfdf48476` renders `move.w d0,intreq(a5)`
  and passes manual-log, provenance, semantic-reload, rendered-source, and exact
  round-trip layers.
- 017-018 recorded the next render-safe A5 candidate, `s0:000004C0`, from
  evidence `a5-custom-cfg:h0:00000498->000004C0:op1:d0044`. Action
  `manual-fa2c2e177ce645968850a0e8c3779158` renders
  `move.w d0,bltafwm(a5)` and passes manual-log, provenance, semantic-reload,
  rendered-source, and exact round-trip layers.
- 017-019 exhausted the remaining render-safe, command-backed A5 candidates in
  the same accepted-evidence family. Fifteen additional A5 refs passed
  manual-log, provenance, semantic-reload, rendered-source, and exact round-trip
  verification; `a5-hardware-report` now has zero remaining unrecorded
  command-backed A5 candidates after existing manual refs are excluded. Blocked
  zero-displacement/non-zero-custom-base A5 refs remain semantic-only pending
  exact symbol-delta rendering support.
- 017-020 fixes the remaining immediate-reference report inconsistency found
  after the A5 sweep: top-level `mutation_gate.safe_to_mutate=false` was correct,
  but source-offset report-only candidates still advertised supported
  candidate-level write policy. Candidate policy now stays report-only unless an
  actual `immediate_ref.interpret` command payload is present.
- 017-021 fixes the analogous A5 post-sweep report state: accepted path/lifetime
  evidence remains visible, but A5 uses already present in
  `manual_state.a5_hardware_refs` no longer count as fresh command candidates.
  Pandora now reports the render-safe A5 queue as exhausted instead of inviting
  duplicate mutations.
- 017-022 records the current end state of the focused Pandora pass. The
  immediate-reference, A5, RSSET, and planner gates now all agree that no safe
  source-converging mutation remains without new evidence or tooling; remaining
  generic class/address data-symbol styling and low-value literal
  representation candidates are not accepted as 017 progress.
- Post-closeout review found follow-up rerun work that should remain in 017
  instead of being lost: 017 source-quality improvements are documented through
  local target/manual state but not a tracked rendered-source evidence artifact;
  zero-displacement or non-zero custom-base-offset A5 refs still need exact
  address-mode-preserving symbol-delta rendering; RSSET has 125 report-only A6
  candidates blocked by missing accepted app-base evidence; and remaining
  immediate source-offset candidates need a deliberate policy/verifier path
  before any mutation. These were promoted to `017-023` through `017-027`.
- 017-023 added `docs/validation/pandora-017-rerun-2026-05-21.md` as the
  tracked evidence boundary. No refreshed `.s` render was committed in this
  closeout; full 017 local/manual reproduction requires Manual Action Log count
  58 with head hash
  `3cbe93c200fd62d091b67c5b096c7b2221e3b57bf30f222272633a4342deed35`.
- 017-024 implemented the address-mode-preserving annotation/render path for
  accepted A5 refs that cannot safely become symbolic operands. Pandora
  `s0:0000045C` now renders an entry comment naming `dmaconr` while preserving
  `move.w (a5),d0`; the verifier checks that no unsafe `dmaconr(a5)` operand is
  emitted.
- 017-025 added selected-use, app-slot-context, and Manual Action Log evidence
  search to `rsset-candidate-report`. Pandora now reports 124 blocked RSSET
  groups plus one already-recorded `$01AD` group; the top active group
  `rsset-raw-a6:022E` still lacks accepted `rsset_app_base` evidence,
  selected-use path/lifetime scope, empty conflicts, and a selected A6 base id.
- Post-review 017-025 hardening made that blocker stricter: accepted RSSET
  base evidence must carry selected-use identity and a `selected_use`
  path/lifetime scope covering the exact A6 use. Sparse or broader evidence is
  rejected as report evidence, not consumed as durable mutation proof.
- 017-026 closes the immediate source-offset policy for Pandora: the 9 remaining
  source-offset candidates stay report-only until accepted runtime-address
  provenance exists.
- 017-027 reran the report surfaces and dry-run planner after `017-024` and
  `017-025`. Immediate refs remain 9 report-only source-offset candidates; A5
  has 20 accepted entries already in manual state, no fresh command candidates,
  and 1 address-mode-preserving entry-comment render; RSSET has 124 blocked
  groups plus one already-recorded `$01AD` group, with `rsset-raw-a6:022E` as
  the top active missing-evidence group. `inspect` reports no candidate work
  and exact round-trip, and `run-one --dry-run` returns no action.
- After post-review 017-025 hardening, the 017-027 gate was rerun again with
  the same mutation result: RSSET `rsset-raw-a6:022E` still has
  `accepted_base_evidence_count=0`, and stricter selected-use matching did not
  expose any command-backed Pandora mutation.
- Reopened 017-025 review found a catalog/report mismatch: the report rejected
  same-displacement app-slot context as non-durable evidence, but the command
  catalog still allowed selected app-slot context to synthesize
  `selected-app-slot:*` base evidence. App-slot context now remains report-only
  for `rsset.binding.bind`; focused Pandora rerun keeps `rsset-raw-a6:022E`
  blocked with `accepted_base_evidence_count=0`.
- Reopened 017-027 rerun after the 017-025 catalog hardening found no supported
  Pandora mutation: immediate refs are 9 report-only source-offset candidates,
  A5 has 20 accepted manual-state refs and 1 entry-comment render with no fresh
  command candidate, RSSET still has 125 candidates with top
  `rsset-raw-a6:022E` blocked by missing accepted base evidence, inspect is
  clear/exact, and dry run reports `no_candidate`.
- 017-028 hardened the A5 address-mode-preserving entry-comment verifier: it
  now requires generated source rendering to succeed and requires the generated
  source text to contain the expected entry comment. Listing/UI
  `comment_text` alone no longer satisfies the verifier, while unsafe symbolic
  operand text such as `dmaconr(a5)` remains rejected.
- 017-029 hardened RSSET accepted-evidence classification: `conflicts` must be
  explicit, sequence-shaped, and empty. Missing or malformed conflict state now
  remains rejected evidence, and the focused Pandora RSSET report still leaves
  `rsset-raw-a6:022E` blocked with `accepted_base_evidence_count=0`.
- 017-030 tracked a real Pandora exercise pass in
  `docs/validation/pandora-017-exercise-2026-05-22.md`: the
  `s0:0000045C` A5 entry-comment action passes the hardened generated-source
  verifier and exact round-trip, RSSET `s0:000006E4` / `$022E` remains blocked
  by missing accepted app-base evidence, and immediate `s0:000009A6` remains
  report-only source-offset evidence. No new safe mutation was available.
- Final 017-027 rerun after the reopened work matched the exercise pass:
  immediate refs, A5 refs, RSSET, inspect, dry-run planner, focused tests, and
  precommit all agree that no command-backed Pandora mutation remains.
- 017-032 added the first internal read-only v2 packet projection for
  `rsset-raw-a6:022E` at `s0:000006E4`. The packet is a Python adapter over the
  existing C-backed listing/RSSET report facts, not a new authoritative C fact
  graph API yet. It carries stable selected-use identity, evidence lanes,
  expanded v2 blockers, explicit conflict state, render intent, and a blocked
  `rsset.binding.bind` gate while leaving default reports, planner behavior,
  Decision Journal writes, rendering, and mutation unchanged.
- 017-033 added an inactive Decision Journal schema skeleton in Python:
  `evidence-decision/v1` records for `accept_fact`, `defer_fact`,
  `reject_fact`, and `supersede_decision`; packet references from the 017-032
  RSSET shape; append-only `prev` hash validation; actor, selected identity,
  evidence-ref, conflict, and supersession diagnostics. It intentionally does
  not read/write target journal files, replay decisions into C facts, replace
  the Manual Action Log, expose `rsset.binding.bind`, render source, or change
  planner/default report behavior.
- 017-034 added explicit per-target `decision_journal.jsonl` read/append IO for
  that schema. Reads report malformed JSONL and whole-chain diagnostics; appends
  are accepted only after existing records and the appended chain validate.
  `decision_journal.jsonl` is target-local manual/journal state for hygiene and
  clean-run classification, but no default report, planner, command, render,
  verifier, C fact replay, or Manual Action Log path consumes it.
- 017-035 exposed that state through explicit
  `python -m amiga_reversing.reversing_loop decision-journal-report --target`
  JSON output, with optional `--dry-run-record` in-memory validation. The
  surface reports existence, validity, diagnostics, active/superseded decision
  ids, and `next_prev` without appending, replaying, rendering, enabling
  `rsset.binding.bind`, or changing default inspect/planner behavior.
- 017-036 added deterministic in-memory replay projection for valid Decision
  Journal records. `decision-journal-report` now includes active
  accepted/deferred/rejected buckets, superseded ids, active ids, and grouping
  by candidate and selected identity. Invalid or malformed journals produce no
  active facts, replacement ids remain informational, and no C facts, Manual
  Action Log paths, command gates, rendering, or default planner behavior
  consume the projection yet.
- 017-037 connected RSSET candidate reports and selected evidence packets to
  that replay projection through a read-only `journal_decision_evidence` lane.
  Matching `rsset_app_base` accepts, defers, rejects, and mismatches are visible
  with exact selected-use checks and reason codes, but legacy
  accepted-base-evidence counts, `rsset.binding.bind`, render/verifier gates,
  mutation, and planner behavior remain unchanged.
- 017-038 and 017-039 split the risky mutation step. 017-038 owns gate and
  verifier readiness reporting with `mutation_enabled=false`; 017-039 owns any
  actual selected RSSET source mutation and must stop if 017-038 is not ready.
- 017-038 is implemented as a read-only `journal_mutation_gate` on RSSET
  candidate reports and selected evidence packets. It reports ordered
  evidence/render/verifier/round-trip gates, the selected `app_022E(a6)` render
  intent, generated-source verifier support, and exact round-trip availability
  while keeping `rsset.binding.bind` blocked and `mutation_enabled=false`.
- 017-040 recorded the real durable Pandora `accept_fact` for
  `rsset-raw-a6:022E` at `s0:000006E4:op1`, with selected-use scope and
  `conflicts: []`; the 017-038 gate then reported ready.
- 017-039 consumed that accepted journal fact through a selected-only
  `rsset.binding.bind` candidate. The command copied journal provenance into the
  catalog context, appended one scoped `rsset_use_site_binding`, verified the
  selected rendered source and exact round-trip, and left the selected report as
  `already_recorded`/`already_satisfied` with no duplicate mutation authority.
- 017-041 added a read-only source-offset immediate evidence packet over the
  existing immediate-reference report. Pandora `s0:000009A6:op0`
  (`addi.w #4224,d1`) now reports selected identity, literal width/syntax,
  possible source-offset interpretation, landing/dataflow lanes, explicit
  blockers, and a disabled `immediate_ref.interpret` gate. Same-literal
  evidence remains report-only and no mutation path was exposed.
- 017-042 added a read-only A5 path/lifetime evidence packet over the existing
  A5 CFG lifetime report. Pandora `s0:0000045C:op0` shows accepted existing
  Manual Action Log state and `s0:000004E6:op1` shows listing-state blockage
  from a possible A5 clobber before use; neither packet exposes fresh mutation.
- 017-043 added a Decision Journal audit result to
  `decision-journal-report`. The real Pandora
  `decision-rsset-022e-accept-017-040` audit is active and source-effective
  after replay, with evidence-ref identity matching, rendered-source effect,
  verifier layers, and no blockers, while fixture coverage proves superseded,
  deferred, rejected, and malformed classifications.
- 017-044 added a read-only orphan/code-island/data-range packet surface over
  manual review and listing-backed data-symbol candidates. The selected Pandora
  proof used real string data-range candidate `s0:000010F3-$00001113`; it is
  explicit packet evidence with blocked `data_symbol.rename` next action, not
  hidden auto-classification.
- 017-045 added `amiga_reversing.tools.validate_017_issues` as a local
  protocol sign-off validator for `017-*` Markdown. It validates status,
  proposal reference, required sections, completed checkboxes, completion
  evidence, and superseded replacement/reason without rewriting files; 017-039
  and 017-040 are passing examples.
- Post-commit review reopened `017-041` through `017-044` for completion
  corrections. Read-only packets must not expose nested command gates that can
  be mistaken for mutation authority; packet access must be tested at the
  supported CLI/API/report boundary or explicitly justified as private helper
  scope; Decision Journal audit source-effect and verifier layers must come from
  real replay/current semantic state or report explicit blockers, not fact-type
  inference.
- The reopened corrections are implemented. `source-offset-immediate-packet`,
  `a5-path-lifetime-packet`, and `orphan-code-island-packet` are supported CLI
  packet surfaces with tests. Read-only packet `command_gate.enabled` and
  `command_gate.safe_to_mutate` are always false; lower-level command support is
  informational only. The base Decision Journal audit is conservative
  (`projected_unverified`) until `reversing_loop.inspect_decision_journal`
  verifies source effect from current target reports; Pandora RSSET audit now
  reports source-effective only after matching the current RSSET report and
  existing manual binding state. Generated-source and exact-round-trip audit
  layers remain `not_checked` with explicit blockers unless current verifier
  results are read or rerun.
- 017-046 added a Decision Journal lane to the source-offset immediate packet
  and recorded Pandora `s0:000009A6:op0` as durable `defer_fact`
  `decision-source-offset-immediate-000009a6-defer-017-046`. Same-literal
  source-offset evidence remains non-accepting and non-mutating.
- 017-047 added a Decision Journal lane to the A5 path/lifetime packet and
  recorded Pandora `s0:0000045C:op0` as durable `defer_fact`
  `decision-a5-path-lifetime-0000045c-defer-017-047`. Existing manual A5 state
  is reported, but no fresh mutation is authorized.
- 017-048 added a Decision Journal lane to orphan/code-island and ambiguous
  data-range packets and recorded Pandora string range `s0:000010F3-$00001113`
  as durable `defer_fact`
  `decision-orphan-code-island-000010f3-defer-017-048`.
- 017-049 added read-only Decision Journal verifier artifact ingestion from
  `decision_verifier_artifacts.json`. Generated-source, negative-safety, and
  exact-round-trip layers can be marked `passed` only when artifact decision id,
  candidate id, selected identity, and freshness match. Missing/stale/mismatched
  artifacts remain explicit blockers; the real Pandora RSSET audit currently
  keeps those verifier layers `not_checked` because no current artifact exists.
- 017-050 is the next active step: produce the current verifier artifact for the
  already accepted and already mutated Pandora RSSET decision. It must keep
  artifact production explicit and non-mutating, then prove that
  `decision-journal-report` can consume the artifact and report
  generated-source, negative-safety, and exact-round-trip layers as `passed`
  only for the selected `s0:000006E4:op1` decision.

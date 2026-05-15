# Amiga Game Disassembly Project

This context describes the project language around reverse engineering Amiga and related 68000 binaries into reproducible, editable source.

## Language

**Reproduction Comparison**:
The check that decides whether rebuilt bytes preserve the original target at the selected exactness level, possibly producing adjusted rebuilt bytes when container shape can be preserved without changing semantics.
_Avoid_: Diff, verification

**Source Rendering**:
The production of assembler source text from analysed target facts.
_Avoid_: Disassembly when specifically referring to emitted source text

**Assembly**:
The production of rebuilt bytes from rendered source.
_Avoid_: Rebuild when specifically referring to the assembler step

**Assembler Policy**:
The policy values that control how assembly emits target bytes, including container encoding choices such as relocation record type and optional symbols.
_Avoid_: Assembler options when referring to the normalized policy model

**Assembler Profile**:
The assembler syntax and compatibility metadata that source rendering must honor.
_Avoid_: Renderer hardcoding

**Project Rebuild**:
The production of rebuilt target bytes for a project using original target metadata and preserving recognized original container shape by default.
_Avoid_: Assembly when specifically referring to project-aware reproduction output

**Round-Trip Verification**:
The workflow that renders source, assembles rebuilt bytes, runs reproduction comparison, and records the result.
_Avoid_: Reproduction comparison

**Container Shape**:
Bytes and records that affect the file container representation but not the program payload semantics at the selected exactness level.
_Avoid_: File shape when specifically referring to non-semantic container representation

**Original File Structure**:
User-facing wording for non-content parts of the original target file that may need to be preserved or explained.
_Avoid_: Container record

**Container Layout**:
C-emitted byte ranges that classify original or rebuilt bytes by container role, such as header, section payload, relocation records, symbols, debug, or section end.
_Avoid_: File layout when specifically referring to binary container ranges

**Container Encoding**:
The concrete container record choices used to represent content, such as relocation record type, ordering, grouping, header flags, and terminators.
_Avoid_: Container layout when referring to record representation choices

**Reproduction Comparison Context**:
The C-owned state used to compare original bytes and rebuilt bytes under a selected backend and reproduction policy.
_Avoid_: HUNK-specific fixer context

**Workflow Context**:
Top-level C workflow state passed through a repository-owned operation; it may carry arenas and later workflow-local services, but it is not a generic allocator bag.
_Avoid_: Allocator context, hidden global state

**Workflow Arena**:
C-owned temporary memory for one top-level C workflow call, destroyed before the call returns and never used for returned artifacts.
_Avoid_: Global scratch arena, process scratch arena, returned artifact arena

**Scratch Mark**:
A saved position in a **Workflow Arena** that is rewound before leaving a local analysis or rendering pass.
_Avoid_: Free list, object destructor, result owner

**Result Arena**:
C-owned memory that lives exactly as long as a C result object and is destroyed by that object's destroy function.
_Avoid_: Workflow scratch, caller-freed output buffer

**Arena Builder**:
A growable C collection or output accumulator that allocates from an explicit arena and finalizes into arena-owned storage without later per-buffer free calls.
_Avoid_: realloc-owned vector, hidden heap list

**Caller-Freed Output Buffer**:
A plain text or byte buffer returned through a public C API and released by the caller with the matching free function.
_Avoid_: Result arena pointer, workflow arena pointer

**Local C API**:
A C interface consumed only by this repository and changeable when a cleaner ownership model requires it.
_Avoid_: External ABI contract, compatibility boundary

**Compatibility Shim**:
Legacy adapter code that preserves an older internal API shape after repository-owned callers have moved to a cleaner interface.
_Avoid_: Migration helper, local API cleanup

**Reproduction Exactness**:
The level at which rebuilt bytes preserve the original target, ranging from full-file equality through content equality to mismatch.
_Avoid_: Pass/fail when the distinction matters

**Full-File Exactness**:
The condition where rebuilt bytes are byte-for-byte identical to the original target, including payload, container layout, and container encoding.
_Avoid_: Container exactness

**Content Exactness**:
The condition where rebuilt bytes preserve the target's meaningful payload or content even when the surrounding container representation is not full-file exact.
_Avoid_: Exact reproduction when full-file bytes differ

**Relocation Fixup Set**:
The resolved set of relocation fixups a container applies to payload bytes, independent of how those fixups are encoded in container records.
_Avoid_: Relocation order when referring to payload relocation meaning

**Policy Divergence**:
The condition where the selected assembler policy emits a different container shape than the recognized original container shape.
_Avoid_: Unsupported shape

**Unsupported Container Shape**:
Original container shape that is observed but not understood well enough to preserve or fully check.
_Avoid_: Policy divergence

**Manual Review Item**:
A user-facing unit of post-analysis work that needs human judgment or action before the target can be considered fully understood.
_Avoid_: Issue

**Review State**:
The target-level summary of whether manual review is clear, pending, or blocked by a live contradiction.
_Avoid_: Issues status

**Reconciled Range**:
A byte range explained by entrypoint-rooted analysis or accepted seeds.
_Avoid_: Understood range

**Unreconciled Range**:
A byte range not yet explained by entrypoint-rooted analysis or accepted seeds.
_Avoid_: Unknown range

**Manual Seed**:
A persisted user-authored analysis seed that records explicit intent such as treating a range as code, data, or a typed value.
_Avoid_: Metadata seed, policy seed

**Manual Label**:
A user-authored symbol name attached to a target address or range start.
_Avoid_: Entity name

**Label Scope**:
The namespace relationship that determines whether a label name must be globally unique or may be local to an owning label.
_Avoid_: Manual label uniqueness

**Manual Comment**:
A user-authored note attached to a target address or range.
_Avoid_: Entity comment

**Manual Representation**:
A user-authored rendering preference for a value or literal that does not by itself classify bytes as code or data.
_Avoid_: Manual seed, data type

**Manual Seed Mode**:
The strength of a **Manual Seed** as either a required analysis input or an exploratory suggestion.
_Avoid_: Seed confidence

**Manual Resolution**:
A persisted user-authored decision that closes or annotates a **Manual Review Item** without necessarily changing analysis facts.
_Avoid_: Manual seed

**Manual Action Log**:
The ordered per-target record of user-authored review and analysis actions from which current manual state is projected.
_Avoid_: Separate manual seed and resolution files

**Target Identity**:
The content and address-defining target inputs that manual actions are bound to.
_Avoid_: Display metadata

**Legacy Entity State**:
The retired `entities.jsonl` and `overrides.json` model that mixed generated range inventory with user annotation state.
_Avoid_: Current target state

**Evidence Fingerprint**:
A compact identity for the analysis evidence supporting a generated **Manual Review Item**.
_Avoid_: Item ID

**Review Confidence**:
An ordinal confidence level for a **Manual Review Item** or candidate classification.
_Avoid_: Probability score

**Suggested Review Action**:
A structured next action offered for a **Manual Review Item** that can append a domain action to the **Manual Action Log**.
_Avoid_: Help text

**Manual Action Catalog**:
The canonical set of currently valid manual analysis actions exposed to UI, keyboard, command palette, CLI, and API callers.
_Avoid_: Separate UI action list, Review dialog buttons

**Listing Selection**:
The active target of a user or tool action in the rendered analysis listing, consisting of a selected row and optionally a selected element inside that row.
_Avoid_: Temporary row highlight

**Listing Element**:
A selectable semantic part of a rendered listing row, such as a label, operand, immediate value, equate, comment, or data literal.
_Avoid_: Text span

## Relationships

- **Round-Trip Verification** includes **Source Rendering**, **Project Rebuild**, and **Reproduction Comparison**.
- **Project Rebuild** supplies an **Assembler Policy** to **Assembly**.
- **Source Rendering** consumes an **Assembler Profile** for syntax features such as local labels.
- Standalone **Assembly** uses an ideal/default **Assembler Policy** unless the caller overrides selected policy values.
- **Reproduction Comparison** consumes original bytes and rebuilt bytes.
- **Reproduction Comparison** runs inside a **Reproduction Comparison Context**.
- A **Workflow Context** carries explicit workflow-owned state through a top-level C operation.
- A **Workflow Context** does not own returned persistent data; persistent results live in a **Result Arena**, caller-provided arena, or model-owned arena chosen by the API contract.
- A **Workflow Context** is introduced only where a top-level workflow needs multiple workflow-owned concerns; existing **Workflow Arena** parameters remain valid when they express the full contract.
- A **Workflow Arena** supplies temporary C memory within one top-level workflow call.
- A **Scratch Mark** creates a nested temporary lifetime inside a **Workflow Arena**.
- Scratch allocation uses **Scratch Marks** on the current **Workflow Arena** unless a measured workflow needs a separate arena form.
- A **Result Arena** owns internal pointers inside one C result object.
- Repository-owned C APIs prefer explicit **Workflow Context**, **Workflow Arena**, or **Result Arena** parameters over generic allocator parameters.
- Production C code does not add generic heap-backed allocator facade usage; allocation cleanup replaces it with explicit lifetime ownership rather than accepting it as transition debt.
- Existing heap-backed allocator facade call sites are removed in focused ownership clusters, and each cluster must move to an explicit **Workflow Arena**, **Result Arena**, model-owned arena, or **Caller-Freed Output Buffer** contract.
- **Caller-Freed Output Buffers** remain valid at Python, CLI, or public C API edges, but repository-owned internals do not introduce new caller-freed buffers.
- For internal persistent returned data, the caller chooses the destination arena or passes an object/model that owns the destination arena.
- An **Arena Builder** is a reusable building block for append-style collections in either a **Workflow Arena** or **Result Arena**.
- A **Caller-Freed Output Buffer** must not point into a **Workflow Arena** or **Result Arena**.
- C modules that allocate internal pointers choose a **Workflow Arena** or **Result Arena** explicitly at their interface.
- C allocation cleanup starts by classifying every allocation site by lifetime; only workflow and result ownership sites are converted first.
- Internal C ownership migrations replace old ownership paths instead of keeping compatibility or fallback paths.
- A **Local C API** may change when arena ownership makes a cleaner interface.
- A **Compatibility Shim** is avoided for repository-owned code because this project has no external compatibility contract.
- **Project Rebuild** preserves recognized original **Container Shape** by default.
- **Original File Structure** is the user-facing way to describe **Container Shape** differences.
- **Container Shape** can differ while **Reproduction Comparison** still reports **Content Exactness**.
- **Container Layout** gives Python the byte ranges it needs for report and row issue mapping.
- **Container Encoding** is used to derive the **Assembler Policy** for **Project Rebuild**.
- **Reproduction Exactness** is reported by **Reproduction Comparison**.
- **Full-File Exactness** is the strongest kind of **Reproduction Exactness**.
- **Content Exactness** is a kind of **Reproduction Exactness**.
- A changed **Relocation Fixup Set** prevents **Content Exactness**.
- A preserved **Relocation Fixup Set** with different record ordering or grouping is a **Container Shape** difference.
- **Policy Divergence** means the original **Container Shape** was recognized but not selected by **Assembler Policy**.
- **Unsupported Container Shape** means the original **Container Shape** was not understood well enough to derive a preserving **Assembler Policy**.
- A target has manual work remaining when it has one or more **Manual Review Items**.
- A **Manual Review Item** is range-bound when analysis can identify affected bytes, and target-level or section-level only when no exact byte range exists.
- A **Review State** is `clear` when no **Manual Review Items** remain open, `needs_review` when normal review work remains, and `blocked` when a live hard conflict or required seed refusal remains.
- A `clear` **Review State** means no known actionable manual work remains under current analysis rules, not that the target is fully understood.
- A `blocked` **Review State** prevents a target from being rated `clear` but does not by itself prevent viewing, analysis, rendering, or export.
- Resolved **Manual Review Items** do not affect **Review State** unless their current **Evidence Fingerprint** differs from the recorded **Manual Resolution**.
- A **Manual Review Item** can be generated from an **Unreconciled Range**.
- A **Reconciled Range** is explained by entrypoint-rooted analysis or an accepted seed, not by plausibility alone.
- A **Manual Seed** can make an **Unreconciled Range** eligible for analysis and later reconciliation.
- A **Manual Seed** keeps manual provenance distinct from metadata, policy, and tool-inferred evidence.
- A **Manual Resolution** can close a **Manual Review Item** without turning its range into a **Reconciled Range**.
- A **Manual Seed** requests reanalysis, while a **Manual Resolution** records a decision about review work.
- **Manual Review Items** are regenerated from current analysis facts; **Manual Seeds** and **Manual Resolutions** are projected from the **Manual Action Log**.
- The **Manual Action Log** is per target and ordered so user actions can be replayed.
- The first **Manual Action Log** record is a header containing log version and **Target Identity**.
- A missing **Manual Action Log** means no manual actions have been recorded yet.
- A header-only **Manual Action Log** is valid empty manual state with pinned **Target Identity**.
- Undo and redo append compensating entries to the **Manual Action Log** rather than deleting prior entries.
- The **Manual Action Log** records domain actions, not UI gestures.
- **Manual Action Log** replay follows file order, while each entry also records action id, sequence, timestamp, and optional undo relationship metadata.
- Broken **Manual Action Log** sequence metadata creates a manual action log inconsistency **Manual Review Item**; replay still follows file order unless parsing or projection fails.
- **Manual Action Log** parsing or projection failure sets **Review State** to `blocked` because current user intent cannot be computed.
- **Target Identity** includes original byte hash, target format or platform, section or hunk layout, runtime or load address metadata, and extracted child source identity.
- **Target Identity** excludes display names, notes, UI labels, and generated analysis outputs.
- **Target Identity** excludes **Assembler Profile** unless the profile changes address interpretation.
- Analysis regressions or improvements do not change **Target Identity**; they change generated facts, **Evidence Fingerprints**, or **Manual Review Items**.
- **Manual Action Log** target identity mismatch is fatal for the project target; the log is not applied and the target remains `blocked` until restored or reimported.
- **Legacy Entity State** is not preserved; any useful role it served is replaced by C analysis facts, **Manual Review Items**, and **Manual Action Log** projections.
- New target state must not depend on `entities.jsonl`, `overrides.json`, entity overrides, or entity verification status.
- A **Manual Label** replaces the old entity name override and is stored through **Manual Action Log** actions.
- A **Manual Label** affects rendering and UI naming; it does not prove code or data unless paired with a **Manual Seed**.
- A **Manual Label** on an unreconciled range creates a **Manual Review Item** unless classification evidence or a **Manual Seed** explains the range.
- **Label Scope** applies to auto-generated labels, metadata or policy labels, and **Manual Labels**.
- A global **Label Scope** requires uniqueness in emitted source scope; a local **Label Scope** may repeat only under an owning global label or scope anchor.
- Local **Label Scope** ownership is explicit in analysis facts and manual actions; nearest-previous-label behavior is only an assembler emission constraint.
- The assembler profile must prove local-label syntax support before source rendering emits local labels.
- Local-label syntax, owner rule, reserved names, and required mode flags are **Assembler Profile** metadata.
- Manual label UI defaults to global **Label Scope** until local-label emission is proven for the active assembler profile.
- Auto-analysis emits globally unique generated labels until local-label emission is proven.
- Label namespace problems create label scope conflict **Manual Review Items**.
- A label scope conflict blocks review only when emitted source correctness or assembly is at risk.
- A **Manual Comment** replaces the old entity comment override and is stored through **Manual Action Log** actions.
- A **Manual Comment** on an unreconciled range creates a **Manual Review Item** unless classification evidence or a **Manual Seed** explains the range.
- A **Manual Representation** affects source rendering and listing display but does not prove classification or reconcile a range.
- A **Manual Representation** is stored through **Manual Action Log** actions rather than as a **Manual Seed**.
- A review-resolution action records the review item id, **Evidence Fingerprint**, range and kind snapshot, and resolution reason.
- A **Manual Seed** has a stable seed id and is updated through new **Manual Action Log** entries, not mutation in place.
- A **Manual Seed Mode** is `required` when analysis must honor the seed or report a conflict, and `suggested` when analysis may reject it.
- A data **Manual Seed** uses data role, unit, and encoding fields rather than separate seed kinds for each data conversion.
- A **Manual Seed** may target a subrange inside an existing generated block; analysis normalizes the range and splits rendered blocks as needed.
- A **Manual Review Item** may include **Suggested Review Actions** for creating seeds, resolving review work, or opening related evidence.
- Navigational **Suggested Review Actions** are transient UI actions and are not appended to the **Manual Action Log**.
- The **Manual Action Catalog** supplies **Suggested Review Actions** and contextual manual-editing commands for all caller surfaces.
- Review dialog buttons, command palette entries, hotkeys, context menus, CLI commands, and API clients invoke **Manual Action Catalog** entries rather than defining separate behavior.
- The **Manual Action Catalog** is backend-owned; UI surfaces render catalog entries instead of hardcoding manual action eligibility.
- Navigation commands that operate on **Listing Selection** are visible in the same command palette catalog and can show assigned key-binding badges even when they do not append to the **Manual Action Log**.
- A **Listing Selection** identifies the current **Manual Action Catalog** context.
- A **Listing Selection** always has a row target and may have a **Listing Element** target when an action needs operand-level, symbol-level, or literal-level precision.
- Manual review UI is checklist-first, with facets for kind, confidence, state, section, source, or range as secondary filtering.
- Entrypoint seeds remain primary analysis evidence; **Manual Seeds** augment the same analysis run with lower provenance priority.
- Seed provenance priority is entrypoint, metadata or policy, required **Manual Seed**, then suggested **Manual Seed**.
- A required **Manual Seed** cannot override entrypoint-proven facts; conflicts are surfaced as manual seed conflict **Manual Review Items**.
- A **Manual Resolution** closes the matching **Evidence Fingerprint** by default; changed evidence reopens the **Manual Review Item** as changed since resolution.
- A hard conflict **Manual Review Item** can be acknowledged but not closed while the conflict remains true.
- Acknowledged hard conflict **Manual Review Items** keep **Review State** at `blocked`.
- User block conversion creates or updates a **Manual Seed**; source is rerendered from analysis facts rather than edited directly.
- A code **Manual Seed** runs the normal fixed-point analysis for its target or runtime view and may cascade through discovered control-flow, table, and data evidence.
- A code **Manual Seed** must not cause unrelated whole-file speculative scanning.
- Initial **Manual Review Item** kinds are reproduction mismatch, unsupported container shape, orphan code candidate, unreconciled data range, suspicious instruction decode, manual seed conflict, manual label unreconciled, manual comment unreconciled, label scope conflict, manual action log inconsistency, and manual action log target mismatch.
- A reproduction mismatch blocks review only when **Content Exactness** fails or cannot be checked; container-only differences are normal **Manual Review Items**.
- An unreconciled data range lacks accepted classification evidence; absence of references from accepted code is not sufficient by itself.
- A suspicious instruction decode **Manual Review Item** is emitted only for accepted or candidate code with actionable misclassification evidence grounded in established reverse-engineering tool practice.
- **Review Confidence** uses `low`, `medium`, or `high` and must be supported by explicit evidence reasons rather than raw probability.
- A required **Manual Seed** that conflicts with stronger facts creates a manual seed conflict **Manual Review Item**.

## Example Dialogue

> **Dev:** "Did round-trip verification fail in source rendering, assembly, or reproduction comparison?"
> **Domain expert:** "Assembly succeeded; reproduction comparison found only a reloc record ordering difference that can be preserved without changing semantics."

## Flagged Ambiguities

- "reproduction" was used for both the whole verification workflow and the byte comparison step; resolved: **Round-Trip Verification** is the workflow, **Reproduction Comparison** is the byte comparison step.
- "issue" was used for user-facing post-analysis work; resolved: use **Manual Review Item** to avoid confusion with bug-tracker issues and reproduction failures.
- "no issues" and "issues" were used for target-level review status; resolved: use **Review State** values `clear`, `needs_review`, and `blocked`.
- "understood" was used as a loose target state; resolved: use **Reconciled Range** and **Unreconciled Range** for byte-range explanation.
- "entity" was used for generated ranges and user annotation state in `entities.jsonl`; resolved: treat that as **Legacy Entity State** and replace it with C analysis facts plus manual review concepts.
- "Review buttons", "hotkeys", and "LLM/API actions" were used as separate surfaces; resolved: use **Manual Action Catalog** for the canonical callable action set.
- "selected row" and "temporary highlight" were used loosely; resolved: use **Listing Selection** for durable action focus and **Listing Element** for intra-row targets.
- "change representation" was mixed with data typing; resolved: **Manual Representation** controls display syntax, while **Manual Seed** controls analysis classification.

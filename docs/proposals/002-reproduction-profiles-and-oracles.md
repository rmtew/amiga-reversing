# Proposal 002: Reproduction Profiles and Oracle Assemblers

Status: Closed as implemented; remaining state cleanup belongs to Proposal 007.
Status changed: 2026-05-17.

The original PRD split for this proposal has been deleted from `docs/prd/`.
That is expected: PRDs are temporary planning artifacts. Durable behavior and
follow-up notes now live here, in `docs/reproduction.md`, and in the current
`docs/issues/028-*` state-correctness work.

## Checkpoint Index

- [ ] Why This Exists
- [ ] Mental Model
- [ ] Current State Read
- [ ] Integration Findings
  - [ ] 1. Exactness Gate Is Strict
  - [ ] 2. Profiles Are Implemented
  - [ ] 3. Oracle Compatibility Is Scoped
  - [ ] 4. Tool Availability Is Project-Level
  - [ ] 5. Source Export Is Non-Verification
  - [ ] 6. Legacy Target UI Edits Are Out Of Scope Here
- [ ] Forward Model
- [ ] Artifact Ownership
- [ ] Non-Goals
- [ ] Implemented Work
- [ ] Remaining Work
- [ ] Acceptance Criteria
- [ ] Verification
- [ ] Follow-Up Review: 2026-05-17

## Why This Exists

Reproduction has two different jobs:

1. Prove the project can rebuild a target with the project-owned exactness gate.
2. Ask external assemblers whether exported source is compatible with their
   syntax and output behavior.

Those jobs must stay separate. External assemblers are useful oracles, but they
do not define whether a target is reproduced. The project exactness gate remains
the direct framework rebuild plus comparison against the original target.

## Mental Model

```text
target metadata / active profile
  -> concrete reproduction options
  -> reproduction policy
  -> framework exactness gate
  -> optional oracle compatibility reports
  -> optional source export
```

Profiles are convenience presets over concrete policy. Reports should always
show both the active gate policy and any requested oracle results, with oracle
statuses using `oracle.*` levels rather than bare reproduction statuses.

## Current State Read

The implementation now covers the core proposal:

- `amiga_reversing/disasm/reproduction.py` defines concrete reproduction
  options, policies, built-in profiles, input stamps, and report writing.
- Built-in profiles are `exact-framework`, `source-vasm`, `source-devpac`, and
  `content-semantic`.
- `REPRODUCTION_ASSEMBLERS` is still `{"our"}`. `vasm` and `devpac` are oracle
  modes, not exactness assemblers.
- `amiga_reversing/disasm/tool_registry.py` owns project-level discovery for
  `vasm`, `genam`, and `vamos`, including configured paths, bundled paths, PATH
  lookup, status, cheap version, and executable stamp.
- `amiga_reversing/disasm/oracle_compatibility.py` runs scoped vasm and
  GenAm-through-vamos compatibility checks and returns `oracle.*` levels.
- `amiga_reversing/disasm/source_export.py` renders vasm/DevPac source exports
  with metadata and target identity stamps and marks export as non-verification.
- `amiga_reversing/disasm/server.py` exposes profile, policy, tool registry,
  tool availability, source export, and reproduction routes.
- `amiga_reversing/tools/reproduction_profiles.py` provides list/show/set CLI
  coverage for profiles.
- Tests exist for profile expansion, invalid option rejection, server routes,
  tool registry discovery, oracle report levels, source export, reproduction
  sweep records, web source hooks, and profile CLI behavior.
- `docs/validation/reproduction-sweep-2026-05-16.md` records the GenAm and
  Bloodwych sweep. Both targets remain exact at the framework gate; oracle
  attempts are recorded separately as `oracle.not_run` because the external
  assemblers rejected the rendered source in those cases.

## Integration Findings

### 1. Exactness Gate Is Strict

The exactness gate is still the project-owned rebuild path. This matches
`docs/reproduction.md` and ADR 0001: C owns reproduction comparison, and source
assembly is debug/oracle surface rather than the steady-state correctness gate.

### 2. Profiles Are Implemented

The profile catalog exists in `reproduction.py`, is surfaced through server
routes, is visible to the web app, and has a CLI wrapper. Profiles expand to
typed options before they affect reproduction.

### 3. Oracle Compatibility Is Scoped

Oracle reports use `oracle.full_file_match`, `oracle.content_match`,
`oracle.mismatch`, `oracle.not_comparable`, `oracle.missing`, and
`oracle.not_run`. This avoids the old ambiguity where an oracle could appear to
make a target `exact`.

### 4. Tool Availability Is Project-Level

Tool paths are project/workspace configuration under `.amiga_reversing`, not
manual review facts. Availability is stamped only when a requested oracle needs
the tool chain.

### 5. Source Export Is Non-Verification

Source export is a user workflow for getting vasm/DevPac-shaped text. It carries
metadata hashes and target identity, but it does not prove reproduction. The
export header says to run reproduction or oracle checks separately.

### 6. Legacy Target UI Edits Are Out Of Scope Here

Profile selection currently persists through `target_ui_edits.json` via
`reproduction_options` edits. That is legacy state plumbing, not a reproduction
architecture requirement.

Proposal 007 and issue `docs/issues/028-006-delete-target-ui-edits-and-unify-mutation-execution.md`
own removal of `target_ui_edits.py` and replacement with the future mutation
path. Proposal 002 should not introduce a second cleanup plan for the same
state model.

## Forward Model

Keep the implemented split:

```text
framework exactness gate
  owns target reproduced / not reproduced

oracle compatibility
  owns external assembler accepts source / output comparison level

source export
  owns downloadable source text and provenance stamps

tool registry
  owns external tool path discovery and availability
```

The profile UI and CLI should continue to write concrete reproduction options,
not arbitrary profile-specific state.

## Artifact Ownership

- Reproduction options: target configuration, currently read by
  `reproduction_options_for_target`.
- Reproduction reports: `targets/<name>/reproduction.json`.
- External tool paths: `.amiga_reversing/tool_registry.json`.
- Source exports: generated response payloads, not durable verification state.
- Validation sweep notes: `docs/validation/`.
- Target UI edit deletion: Proposal 007 issue `028-006`.

## Non-Goals

- Do not make `vasm`, DevPac, GenAm, or `vamos` the exactness gate.
- Do not preserve old `target_ui_edits.json` compatibility.
- Do not add user-authored custom profile schemas until built-in profile state is
  moved through the Proposal 007 mutation model.
- Do not treat source export as evidence of reproduction correctness.

## Implemented Work

The old PRD 018-022 scope is effectively complete:

- profile catalog and policy summary
- profile get/set API and CLI
- tool registry and availability records
- oracle compatibility reports
- source export workflow
- GenAm/Bloodwych validation sweep note

## Remaining Work

No new Proposal 002 issue set is needed. Current remaining work is either:

- Proposal 007 state cleanup: remove `target_ui_edits` as a durable mutation
  source, including reproduction profile persistence.
- Normal oracle renderer improvement: make vasm/DevPac source accepted by more
  external assemblers without weakening the framework gate.

## Acceptance Criteria

Proposal 002 is complete when:

- exact reproduction still depends only on the project framework gate
- profile selection expands to validated concrete options
- requested oracle tools are discovered and stamped
- oracle reports use scoped `oracle.*` levels
- source export remains explicitly non-verification
- validation sweeps record gate status separately from oracle status
- stale PRD references are removed from durable docs

## Verification

Existing focused coverage:

- `tests/test_reproduction.py`
- `tests/test_tool_registry.py`
- `tests/test_oracle_compatibility.py`
- `tests/test_reproduction_sweep.py`
- `tests/test_disasm_server.py`
- `tests/test_reproduction_profiles_cli.py`
- `tests/test_web_app_source.py`

Integration evidence:

- `docs/validation/reproduction-sweep-2026-05-16.md`

## Follow-Up Review: 2026-05-17

Reviewed against current code, `docs/reproduction.md`, `CONTEXT.md`,
`TODO.md`, Proposal 007, and the active `docs/issues/028-*` issue set.

Conclusion: Proposal 002 should be closed as implemented. The only architecture
smell found during this review is the legacy `target_ui_edits` persistence path,
and that is already assigned to Proposal 007. Keeping it out of Proposal 002
prevents duplicate state cleanup plans.

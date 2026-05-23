# 018-014: Mac OS Non-CODE Resource Metadata Inventory

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS resource-fork metadata outside executable CODE
  segments
- Blocked by: `018-001`
- Independent of: `018-010`
- Current proposal state: Mac target output lists non-CODE resource types as
  placeholders. Their relationship to executable analysis is not yet captured
  as structured inventory.
- Desired proposal state after this issue: non-CODE resources in the MPW Asm
  fixture and local Mac docs are inventoried as metadata, support, deferred, or
  unsupported records without changing CODE rendering/navigation.

## Knowledge Delta

- Adds: Mac non-CODE resource inventory and source policy notes.
- Changes: non-CODE placeholders become structured evidence/debt rather than
  anonymous omissions.
- Replaces: vague "structured placeholder" comments where source-backed
  classification is possible.
- Deletes: none.
- Leaves out of scope: CODE resource rendering, resource editing, full Rez
  decompilation, UI navigation, and accepted executable code semantics.

## Default Behavior

- No parser behavior changes unless limited to metadata-only inventory output.
- No Mac CODE rendering/navigation files should be changed.
- Non-CODE resources must not be treated as executable code unless cited facts
  prove executable semantics.

## Evidence Standard

- Resource types must be classified as accepted metadata, candidate metadata,
  deferred, unsupported, or conflict evidence.
- Accepted classifications require citations or parser assertions.
- Project-observed fixture inventory may support candidate records.
- The inventory must preserve resource type, count, ids/names where available,
  payload size/hash where already exposed, and analysis relevance.

## Implementation Slice

- Inventory MPW Asm non-CODE resource types currently visible in the target:
  `acur`, `CURS`, `cmdo`, `vers`, and any others present.
- Search local Mac markdown/docs for resource type semantics relevant to MPW
  tools or applications.
- Update `docs/platform-executable-formats.md` and/or KB records with
  classification and deferred/unsupported reasons.
- Add tests for inventory/classification if parser output changes.
- Do not modify multi-CODE rendering/navigation behavior.

## Research Completion Standard

Record trace blocks for:

- observed resource type/id/name/count inventory;
- local documentation citations found or missing;
- classification decision for each resource type;
- why non-CODE resources are not executable CODE evidence;
- parser-output changes, if any.

## Research Coverage

- [x] MPW Asm non-CODE resource inventory sampled.
- [x] Local Mac docs searched for each observed resource type.
- [x] Resource classifications assigned.
- [x] Deferred/unsupported reasons recorded.
- [x] CODE rendering/navigation touch points avoided.

## Research Review

- [x] Second pass checked every accepted classification against citations.
- [x] Project-observed-only classifications remain candidate.
- [x] Non-CODE resources are not presented as executable CODE.
- [x] No 018-010 output paths are modified.
- [x] Tests added if output changes.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Non-CODE resource inventory recorded.
- [x] Classification/status/source policy recorded for each resource type.
- [x] Deferred/unsupported reasons recorded.
- [x] No CODE rendering/navigation behavior changed.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes if KB
  changes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.


## Completion Evidence

- Recorded candidate-only non-CODE resource metadata inventory and confirmed no CODE rendering/navigation behavior changed.
- Validation commands listed in the required sign-off were run after implementation before commit.
- No Mac multi-CODE rendering/navigation files for 018-010 were modified.

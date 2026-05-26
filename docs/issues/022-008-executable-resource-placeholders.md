# 022-008: Executable Resource Placeholders

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Add typed placeholders for executable-relevant Mac resources and custom
extensions referenced by CODE source. Do not broadly decode unrelated non-CODE
resources.

Use existing non-CODE inventory and CODE reference context as input. This issue
is about stable source placeholders, not broad Mac resource parsing.

## Acceptance criteria

- [ ] Placeholder records include resource type/id/name when known.
- [ ] Placeholder records include byte size, hash or stable identity,
      provenance, status, and reason.
- [ ] Placeholder records include reference sites from CODE source when known.
- [ ] Placeholder identities are stable enough for later UI navigation:
      resource type/id/name plus source reference site where available.
- [ ] Custom or unsupported extension material is source-visible as a
      placeholder, not a silent gap.
- [ ] Broad non-CODE resource decoding is avoided unless directly required for
      executable source comprehension.
- [ ] Web/API payloads expose placeholders in a stable form.
- [ ] Proposal 022 records any future resource UI/navigation work.

## Verification

Run at minimum:

```powershell
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

## Blocked by

- `docs/issues/022-007-macos-code-ownership-and-relocation-integration.md`

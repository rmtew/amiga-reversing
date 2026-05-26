# 022-003: Source Coverage Verifier

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Add the C-owned source coverage verifier for restored source ownership ranges.
The verifier must reject silent gaps, overlapping ownership, and invalid
role/status rendering claims.

Python may expose report/test wrappers, but the checks must live in C.

The verifier must validate rendered source ownership, not just parser summary
shape. It should be usable from listing artifact/report paths after C computes
the result.

## Acceptance criteria

- [ ] Verifier detects gaps in covered executable source bytes.
- [ ] Verifier detects overlapping ownership ranges.
- [ ] Verifier rejects accepted instruction rendering from data, BSS, metadata,
      relocation/fixup, placeholder, or unknown ranges.
- [ ] Verifier allows explicit unknown only with span, status, reason, and
      provenance.
- [ ] Amiga/Atari verifier path is compatible with exact rebuild gates.
- [ ] Mac verifier covers selected CODE resource bytes without claiming
      round-trip.
- [ ] Verifier results can be exposed through `CListingArtifact` or equivalent
      artifact API.
- [ ] Tests cover passing and failing ownership reports.
- [ ] Proposal 022 records verifier limits and follow-up findings.

## Verification

Run at minimum:

```powershell
cmd /c src\build.bat
uv run python -m amiga_reversing.tools.platform_executable_formats validate
git diff --check
```

## Blocked by

- `docs/issues/022-002-shared-source-ownership-model.md`

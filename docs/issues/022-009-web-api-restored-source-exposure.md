# 022-009: Web/API Restored Source Exposure

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Expose restored source ownership, source references, verifier results, and
placeholders through existing web/API surfaces. Do not redesign the UI.

Document obvious UI shortcomings as future work.

Treat the current Mac CODE web panel and listing artifact API as consumers to
migrate. Do not hide restored source evidence behind docs-only reports.

## Acceptance criteria

- [ ] Web/API payloads expose restored source ownership ranges.
- [ ] Web/API payloads expose source reference records.
- [ ] Web/API payloads expose verifier status/results.
- [ ] Web/API payloads expose executable-relevant placeholders.
- [ ] Existing views can inspect required evidence without relying only on
      legacy Mac-only fields.
- [ ] Existing listing/navigation/window APIs remain usable for Amiga, Atari,
      and Mac.
- [ ] UI gaps are documented in Proposal 022 as future work, including
      ownership navigation, relocation/reference context, resource placeholder
      navigation, or side-by-side code/data/source views where relevant.
- [ ] No UI redesign is implemented unless required evidence is otherwise not
      visible.

## Verification

Run at minimum:

```powershell
uv run python -m pytest tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

## Blocked by

- `docs/issues/022-007-macos-code-ownership-and-relocation-integration.md`
- `docs/issues/022-008-executable-resource-placeholders.md`

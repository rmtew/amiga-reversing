Status: implemented
Source proposal: docs/proposals/016-pandora-reversing-loop-hardening.md
Moved from: docs/proposals/015-agent-reversing-pandora-target.md D011

Scope:
Clean up duplicate manual-seed verifier reporting.

Problem:
Some command execution results expose the same manual seed through both
`action` and `actions`. The verifier reads both and reports duplicate
`expected_manual_seeds` and `matching_manual_seeds`. Verification still passes,
but review output is noisier than necessary.

Required work:
- Deduplicate manual seed identities before verifier comparison/reporting.
- Preserve detection of real missing, extra, or mismatched seeds.
- Add tests where `action` duplicates the first `actions` entry and where two
  genuinely distinct seeds are present.

Acceptance:
- Verifier output lists each expected/matching manual seed once.
- Existing manual-seed verification behavior is unchanged for real mismatches.

Implementation:
- Manual seed creation payloads are deduped by exact payload identity before
  verifier comparison/reporting.
- Manual seed removal ids are deduped before absence checks.
- Focused tests cover `action` duplicating the first `actions` entry and two
  genuinely distinct seed payloads.

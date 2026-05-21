Status: active
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: review request after 017-024/017-025 closeout

Scope:
Use the real Pandora sub-target for a demonstrable editing pass over the
related source-converging surfaces after the 017 verifier hardening, not only
unit tests and compact gate summaries.

Problem:
017-024 and 017-025 changed important source-converging surfaces, then 017 was
closed from report summaries. Before final closeout, the agent should exercise
the related Pandora editing workflow enough to prove the loop helps or
correctly blocks real target work. This is broader than testing only the new
verifier changes.

Required work:
- Reproduce the current Pandora target state without committing timestamp-only
  `.project.json` churn.
- Exercise the related editing features used by this proposal on the real
  target: review/action discovery, immediate-reference report policy, A5
  hardware-ref editing/projection, RSSET report/bind blocking, command catalog
  availability, already-satisfied detection, verifier layers, and source
  evidence capture.
- Exercise the A5 entry-comment path as one case, recording the exact source
  location, generated-source evidence, and round-trip result.
- Exercise RSSET evidence search as one case, starting with
  `rsset-raw-a6:022E`; inspect flow/xrefs/source context enough to either find
  accepted base evidence or document the exact missing proof.
- Pick at least one additional concrete Pandora candidate or editing surface
  from inspect/reports/review context, even if the result is a justified block,
  so the pass is not limited to the two review findings.
- Use query/report APIs first. Render or inspect the full `.s` only where it
  answers a concrete evidence question or provides final review evidence.
- If a command-backed, verifier-backed, exact-round-trip mutation appears,
  execute it and verify it. If not, record why each inspected family remains
  blocked.
- Update proposal 017 and validation evidence with the inspected locations,
  report counts, timings if slow, and visible source/result summary.

Acceptance:
- The pass includes concrete Pandora locations inspected, not only aggregate
  counts.
- A5 entry-comment generated-source behavior is proven on Pandora after
  `017-028`.
- RSSET top active group evidence search is demonstrated beyond report-only
  summary after `017-029`.
- At least one other related editing surface is exercised and recorded with a
  concrete Pandora location/result.
- Any output-affecting change has exact round-trip verification.
- Final 017 closeout is deferred to `017-027` after this issue is complete.

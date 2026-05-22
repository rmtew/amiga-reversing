Status: implemented
Type: AFK
Source proposal: docs/proposals/017-evidence-driven-analysis-protocol.md
Promoted from: 017-008 follow-up

Scope:
Make `a5-hardware-report` distinguish accepted path/lifetime evidence from a
safe hardware-register render mutation path.

Problem:
017-008 can classify straight-line `_custom` A5 uses as
`accepted_custom_base`, but rendering remains blocked. Without explicit
command/verifier gate fields, consumers can over-read accepted evidence as
permission to render hardware register names.

Required work:
- Keep the report read-only and non-mutating.
- Expose whether accepted path/lifetime evidence exists.
- Expose missing command support and missing verifier support as concrete
  gates.
- Keep exact round-trip marked as required for any future output-affecting
  mutation.

Acceptance:
- `accepted_custom_base` A5 uses still have `safe_to_mutate=false` and
  `rendering_allowed=false`.
- The report names the missing command and verifier gates.
- Tests prove accepted evidence does not imply render permission.

Result:
- `cfg_path_lifetime_report` now includes `safe_to_mutate=false`,
  `mutation_policy=report_only_requires_render_command_and_verifier`, and a
  `rendering_gate` payload.
- The gate reports accepted evidence count, missing
  `a5_hardware_ref.interpret` command support, missing
  `a5_hardware_ref_state` verifier support, and exact round-trip as a future
  output-affecting requirement.
- Pandora A5 hardware rendering remains blocked until a later issue adds the
  command, projection, verifier, and exact round-trip mutation path.

Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Make immediate and data-literal representation changes genuinely
source-converging.

Current evidence:
- `ManualRepresentationMetadata` and `create_manual_representation` exist.
- Command catalog exposes representation commands on immediate and data literal
  elements.
- Existing focused tests prove data-literal append/projection, but not durable
  instruction-immediate rendering or an action-specific loop verifier.

Acceptance criteria:
- Operand identity is durable across listing rebuilds.
- Instruction immediates and data literals both render with the selected style.
- The loop verifier checks Manual Action Log, semantic reload, projected
  representation, rendered text, and round-trip exactness where output-affecting.

Required tests:
Operand identity tests, instruction-immediate rendering tests, data literal
regression tests, and loop verifier tests.

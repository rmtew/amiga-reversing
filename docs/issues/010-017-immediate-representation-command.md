Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

Scope:
Add command/manual-action support for changing immediate value representations
in rendered source, including decimal/hex/binary/character/symbolic-equate forms
where the assembler can preserve exact output.

Problem:
A human reverser often improves source by rendering immediates in the domain
form that communicates intent. The agent currently lacks a supported path for
those non-label, non-slot source improvements.

Out of scope:
Do not change instruction semantics, immediate values, or binary output. Do not
use representation changes as makework; require evidence that the new
representation improves source readability or domain meaning.

Files likely touched:
- `amiga_reversing/disasm/manual_actions.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/target_metadata.py`
- source rendering/projection code
- `amiga_reversing/reversing_loop.py`
- focused tests

Acceptance criteria:
- Command catalog exposes immediate representation choices for locator-backed
  operands or elements with durable operand identity.
- Manual Action Log records the representation override durably.
- Projection/rendered source shows the requested representation at the target
  operand only, unless a structured broader action is explicitly selected.
- Verifier confirms rendered text changed as intended and round-trip remains
  exact.
- Loop can select this only when evidence explains why the representation
  improves source convergence.

Required tests:
- catalog exposes representation choices for immediate operands;
- command execution appends Manual Action Log entry;
- projection/rendered source updates the immediate representation;
- output equivalence/round-trip remains exact;
- loop refuses representation-only makework without evidence.

Cleanup / deletion:
Delete after implementation, verification, and proposal notes are complete.

Notes for agents:
Prefer equates for repeated or named constants. Immediate representation changes
are best for local display intent, such as ASCII characters, bit masks, or
domain-significant decimal counts.

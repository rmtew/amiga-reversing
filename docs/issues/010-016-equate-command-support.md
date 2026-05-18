Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

Scope:
Add supported Manual Action Log commands for equate creation, editing, and
renaming, then expose them to the reversing loop as source-converging actions.

Problem:
Human-quality reconstructed source needs named constants for magic numbers,
flags, structure sizes, command ids, menu ids, hardware masks, and similar
immediate/domain values. Agents should not encode these by comments or direct
source edits; they need durable equate commands with verification.

Out of scope:
Do not infer broad constant taxonomies without local evidence. Do not add
assembler-source-only rewrites that bypass target metadata/manual actions.

Files likely touched:
- `amiga_reversing/disasm/manual_actions.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/target_metadata.py`
- `amiga_reversing/disasm/server.py`
- `amiga_reversing/reversing_loop.py`
- focused source rendering and command tests

Acceptance criteria:
- Command catalog exposes equate add/edit/rename actions for durable constant
  identities or selected immediate values.
- Manual Action Log stores enough identity to replay the equate without relying
  on row index or text.
- Rendered source includes the equate definition and uses it at verified
  reference sites where the representation is accepted.
- Loop reports evidence, expected rendered-source improvement, command id,
  verifier, and mutation result.
- Round-trip remains exact.

Required tests:
- equate add/edit/rename command catalog and execution tests;
- projection/rendering test proving definition and references update;
- reversing-loop smoke selecting one equate action from analysis evidence;
- round-trip/reproduction check for output equivalence.

Cleanup / deletion:
Delete after support, tests, verification, and proposal notes are complete.

Notes for agents:
Good equate candidates should come from repeated immediates, API/hardware
semantics, enum-like comparisons, or documented game/platform constants.

Status: Open
Source proposal: docs/proposals/010-agentic-reversing-loop.md

Scope:
Add first-class Manual Action Log support for adding, editing, and renaming
app/base-relative slots rendered as `app_XXXX` style RS/app storage names, then
expose it through the normal command catalog and reversing loop.

Problem:
GenAm source-convergence work quickly reaches app-slot names such as
`app_0234(a6)`. These are not source labels and should not be renamed through
`label.rename`. Today an agent can observe them in rendered source and analysis
facts, but cannot apply the same kind of structured durable edit a user needs.

Out of scope:
Do not add one-off scripts, direct target metadata writes, or compatibility
paths around the Manual Action Log. Do not infer app-slot names without
evidence from xrefs, API semantics, or surrounding behavior.

Files likely touched:
- `amiga_reversing/disasm/manual_actions.py`
- `amiga_reversing/disasm/manual_action_catalog.py`
- `amiga_reversing/disasm/server.py`
- `amiga_reversing/disasm/target_metadata.py`
- `amiga_reversing/reversing_loop.py`
- focused workflow/server/reversing-loop tests

Acceptance criteria:
- Command catalog exposes app-slot add/edit/rename actions for a durable
  app/base-relative slot locator or equivalent structured target identity.
- Command execution appends a Manual Action Log action that overrides the app
  slot name without mutating retired state models.
- Projection/rendering uses the accepted app-slot name at the RSSET definition
  and all matching base-relative references.
- Reversing loop can execute the command through `/commands/execute` in the
  same process, record evidence/rationale, and verify the projected name.
- Round-trip remains exact for output-affecting rendered source changes.

Required tests:
- catalog availability for an app slot with a full durable identity;
- command execution appends the expected Manual Action Log entry;
- semantic reload projects the new slot name at definition and references;
- reversing-loop focused test for a GenAm-style app-slot rename candidate;
- round-trip or reproduction verification for the affected target shape.

Cleanup / deletion:
Delete this issue after the command, loop access, tests, verification, and
durable proposal notes are complete.

Notes for agents:
Prefer existing app-slot/base-slot facts from C analysis. If the data model
cannot identify a slot durably enough for command execution, stop and add that
identity contract before adding a UI/loop shortcut.

---
name: target-reversing-workflow
description: Restore an Amiga reversing target through durable framework analysis facts and actions. Use when selecting and reversing the next target subsystem, classifying code or data, recovering tables or record layouts, improving the analysis command surface, regenerating target source, or verifying exact reassembly.
---

# Target Reversing Workflow

Reconstruct the original absolute-address source image. The target is complete
when code and data are accounted for by durable analysis facts, the rendered
source is human-readable where evidence permits, and it reassembles to the
original binary exactly. Relocatable or re-entrant output is a later pass.

## Start and preserve state

1. Read `AGENTS.md`, `docs/agents/reversing-loop.md`, and the relevant parts
   of `docs/proposals/010-agentic-reversing-loop.md`.
2. Treat C analysis facts and the target Manual Action Log as the source of
   truth. Never edit generated target `.s` files directly.
3. Open the listing/analysis server once and keep it running for a reversing
   swath. Reopen or refresh the target projection after a target action; only
   rebuild/restart the server when its implementation or loaded C backend has
   changed.
4. Preserve unrelated worktree changes. Do not commit timestamp-only target
   `.project.json` changes.

## Select useful work

Choose a connected, evidence-backed swath rather than isolated labels:

- a routine with its direct helpers, tables, and call/data consumers;
- a game subsystem and its shared state/record fields;
- a data family with its bounds, element roles, and all known consumers.

Prioritize unresolved control flow, unclassified data, repeated anonymous
field accesses, indirect dispatch/table bounds, and high-xref anonymous
objects. Inspect xrefs before naming or classifying anything.

## Apply facts through commands

Use the normal listing command surface to create durable facts: labels and
function names; code/data/range classification and table bounds; data-block
layouts, elements, fields, types, and interpreted references; and app/RSSET
slots plus callback/indirect-call evidence.

Name fields only when repeated uses establish their meaning. Preserve unknown
bytes as explicit raw, padding, or review state; do not invent structure solely
to eliminate `dc.b` output. Recover one shared layout where evidence proves
one, rather than independently naming equivalent offsets.

For a missing capability, implement the smallest general command-path feature,
give it a durable Manual Action representation and focused regression test,
then resume the same swath. Do not use a framework gap as a reason to defer
otherwise supported reversing work or to hand-edit output.

## Verify and commit every slice

After every output-affecting slice, regenerate and require full exactness:

```powershell
$env:UV_CACHE_DIR='C:\Data\R\git\claude-repos\amiga-reversing2\.uv-cache'
uv run python -m amiga_reversing.tools.rendered_source_roundtrip_report `
  --target <target-id> --update-rendered-source --no-write-report --json
```

Require `rendered_source_full_file_exact: 1`. Run focused tests for framework
changes; run the appropriate broader suite when the change crosses renderer,
analysis, or command-server boundaries. Commit the changed framework code and
tests together with the target's `manual_actions.jsonl` and regenerated `.s`.

## Use runtime evidence narrowly

Use `$headless-amiga-runtime` only to resolve a concrete static ambiguity:
reachability, an unpacked payload mapping, dynamic state, or a disputed field.
Keep WinUAE strictly headless. Convert useful observations into normal static
facts and still pass exact round-trip verification.

## Report progress

State the subsystem completed, durable facts added, framework gaps fixed,
verification result, and the next connected unresolved swath. Distinguish
evidence from remaining hypotheses.

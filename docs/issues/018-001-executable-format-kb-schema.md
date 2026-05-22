Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Define the shared schema for platform executable/container format knowledge.

Acceptance criteria:
- The schema is one shared top-down model with platform extension blocks, not
  unrelated per-platform schemas.
- Records can describe platform, format id, archetype id, producer/variant,
  signatures, containers, regions, relocations, symbols, BSS, typed
  entrypoints, loader model, runtime model, analysis model, renderer
  expectations, citations, and parser assertions.
- Unknowns, conflicts, deferred areas, and unsupported areas are first-class
  records with parser behavior rules.
- Fact states include `validated`, `parser_asserted`, `candidate`,
  `deferred`, and `unsupported`; accepted parser behavior can consume only
  `validated` and visible `parser_asserted` facts.
- Source policy records `old_out_of_print`, `modern_compatible`,
  `project_observed`, and `parser_asserted` source types.
- Schema supports Amiga, Atari ST, and Mac OS without platform-specific hacks.
- Parser assertions require reason, citation context, and standard
  interpretation.
- Tests validate representative records and a thin Mac CODE/resource proof
  record.
- Canonical files are planned as `docs/platform-executable-formats.md`,
  `knowledge/platform_executable_formats.schema.json`, and
  `knowledge/platform_executable_formats.json`.

Blocked by:
None.

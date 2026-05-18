Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Turn API, LVO, register-base, and struct-pointer semantic discoveries into
consumed source-converging actions.

Current evidence:
- `entry_register_seeds` are consumed by rendering and support `library_base`
  and `struct_ptr`.
- Command catalog exposes `semantic.library_base.<library>` helpers for A6 LVO
  contexts, using row API metadata when present and NDK library/function lookup
  otherwise.
- Command catalog exposes `semantic.register.struct_ptr` on register elements;
  execution writes a `struct_ptr` register seed with an explicit struct name.
- `semantic.lvo.*` commands append semantic hints; LVO hints for immediate
  operands now project to `_LVO*` symbol representations and render with NDK
  includes.
- `semantic.struct_offset.*` commands append semantic hints; struct-offset
  hints for immediate operands now project to NDK field symbol representations
  and render with includes.

Progress:
- Known LVO immediate constants are source-converging: Manual Action Log hint ->
  effective metadata -> rendered `_LVO*` symbol -> exact direct rebuild.
- Known struct-offset immediate constants are source-converging: Manual Action
  Log hint -> effective metadata -> rendered field symbol -> exact direct
  rebuild.
- A6 LVO library-base seeds are no longer exec-only; command execution records
  the selected library and named base struct when the NDK payload provides it.
- Register-selected struct-pointer seeds now use the existing Manual Action Log
  projection path and no longer default to `exec.library`.
- API call semantics, evidence-scoped register lifetimes, typed field access
  semantics, and higher-confidence struct-pointer candidate generation remain
  open.

Acceptance criteria:
- Register/base identities cover entry-scoped and evidence-scoped lifetimes.
- LVO/API/struct-offset semantic choices project into effective metadata.
- Commands are available for supported libraries, registers, and struct pointer
  cases without hard-coded exec-only behavior.
- Verifiers prove rendered-source propagation through calls, arguments, return
  values, or stored state as applicable.

Required tests:
Register seed projection/render tests, semantic hint consumption tests, command
catalog tests, and loop verifier tests.

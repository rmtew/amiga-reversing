Status: Open
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Turn API, LVO, register-base, and struct-pointer semantic discoveries into
consumed source-converging actions.

Current evidence:
- `entry_register_seeds` are consumed by rendering and support `library_base`
  and `struct_ptr`.
- Command catalog only exposes a narrow `semantic.library_base.exec` helper for
  A6 LVO contexts.
- `semantic.lvo.*` and `semantic.struct_offset.*` commands append semantic
  hints, but semantic hints are not consumed by effective metadata/rendering.

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

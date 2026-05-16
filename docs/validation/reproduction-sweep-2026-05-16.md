# Reproduction Validation Sweep - 2026-05-16

## Scope

- Targets: `amiga_hunk_genam`, `amiga_hunk_bloodwych`
- Gate profile: active exactness gate from target reproduction options
- Oracle checks recorded separately with PRD 020 `oracle.*` comparison levels
- Report paths:
  - `targets/amiga_hunk_genam/reproduction.json`
  - `targets/amiga_hunk_bloodwych/reproduction.json`

## Classifications

| Target | Gate status | Gate comparison | Oracle | Oracle level | Tool availability | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `amiga_hunk_genam` | `exact` | `exact_file` | `genam-devpac` | `oracle.not_run` | `genam`: available bundled; `vamos`: available on PATH | GenAm rejected rendered DevPac source: absolute indexed PC syntax at line 1923. Gate remains exact. |
| `amiga_hunk_bloodwych` | `exact` | `exact_file` | `vasm` | `oracle.not_run` | `vasm`: available bundled | vasm rejected rendered source for selected `-m68000`: `movec` instructions require a higher CPU. Gate remains exact. |

## Repeat

1. Run `run_reproduction("amiga_hunk_genam")` and `run_reproduction("amiga_hunk_bloodwych")`.
2. Record gate `status` plus `comparison.status` from each reproduction report.
3. Run oracle compatibility with `{"oracle_modes": ["devpac"]}` for GenAm and `{"oracle_modes": ["vasm"]}` for Bloodwych.
4. Record only scoped oracle levels such as `oracle.not_run`, never bare `exact`.

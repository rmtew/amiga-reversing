# 0001-003 Manual Seeds In Analysis

## Parent

PRD 0001: Manual Review Workflow

## What to build

Make projected Manual Seeds participate in analysis. Entrypoint evidence remains primary, then metadata or policy, then required Manual Seeds, then suggested Manual Seeds. Code Manual Seeds run the normal analysis discovery loop for the target or runtime view and may cascade through real control-flow, table, and data evidence. Data Manual Seeds classify ranges using role, unit, and encoding fields.

## Acceptance criteria

- [ ] Required code Manual Seeds can seed code analysis without unrelated whole-file speculative scanning.
- [ ] Required data Manual Seeds can classify range data role, unit, and encoding.
- [ ] Suggested Manual Seeds may be rejected when stronger evidence contradicts them.
- [ ] Required Manual Seeds that conflict with entrypoint-proven or stronger facts produce manual seed conflict review work rather than overriding those facts.
- [ ] Manual Seeds may target subranges and cause normalized block splitting where valid.
- [ ] Analysis output preserves manual provenance distinctly from metadata, policy, and tool-inferred evidence.
- [ ] CDP tests pass.
- [ ] `cmd /c src\precommit.bat` passes.

## Blocked by

- 0001-001 Manual Action Log Projection

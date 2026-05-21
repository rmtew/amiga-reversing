# Pandora 017 Exercise Pass - 2026-05-22

Target:
`amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`

Scope:
Reopened 017 exercise pass after `017-028` and `017-029`. This is a tracked
evidence boundary only; no refreshed `.s` export is committed here.

## State Reproduction

- `inspect_target`: `candidate_work_count=0`; verification paths for semantic
  reload, projection check, and round trip are available.
- Round trip: `status=exact`.
- `run_one_iteration(..., dry_run=True)`: `planner.status=no_candidate`,
  `action=null`, message `no supported source-converging command candidate`.
- Dry-run ranked candidates: 225 total, with 221 `data_symbol_name` candidates
  stopped as class/address styling and 4 `literal_representation` candidates
  stopped as syntax-only low semantic value.
- Existing target-local `.project.json` churn is not meaningful evidence and is
  not staged.

## A5 Entry-Comment Case

Concrete location:

- Definition: `s0:00000456`, `lea.l _custom+dmaconr.l,a5`.
- Use: `s0:0000045C`, `move.w (a5),d0`.
- Manual action: `manual-964aee63919e438880d1f5e7670ef95d`.
- Evidence id: `a5-custom-cfg:h0:00000456->0000045C:op0:b0002+d0000`.
- Render mode: `entry_comment`.

Generated source evidence:

```asm
abs_0_00010456:
	lea.l _custom+dmaconr.l,a5
    ; A5 hardware ref: dmaconr at _custom+$0002; operand kept as (a5)
abs_0_0001045C:
	move.w (a5),d0
```

Hardened verifier result:

- Overall status: `passed`.
- Layers passed: manual action log, semantic reload, rendered source, round
  trip.
- Rendered-source layer: `source_contains_expected_comment=true`,
  `actual_comment_text` matches expected, and
  `matched_unsafe_symbol_operand_text=false`.

Current A5 report:

- `accepted_custom_base` evidence count: 20.
- Fresh command candidates: 0.
- Rendering gate is blocked by `command_candidate`; accepted manual-state refs
  are already recorded.

## RSSET Top Active Group

Concrete location:

- Candidate: `rsset-raw-a6:022E`.
- Selected use: `s0:000006E4`, `bclr.b #1,app_022E(a6)`.
- Displacement: `$022E`, width 1, memory write.
- Same-displacement use count: 66.

Source context:

```asm
abs_0_000106D8:
	bset.b #5,app_033C(a6)
	bne.b abs_0_0001074C
	bsr.w abs_0_00017B6E
	bclr.b #1,app_022E(a6)
	beq.b abs_0_00010724
	lea.l abs_0_0005C940.l,a0
```

Evidence search result:

- `accepted_base_evidence_count=0`.
- Searched selected-use source evidence, same-displacement app-slot context,
  and manual `rsset_use_site_bindings`.
- Manual accepted RSSET bindings currently cover displacement `$01AD` only;
  none cover `$022E`.
- Same-displacement app-slot context is rejected as report-only, not durable
  accepted base/path evidence.
- `rsset.binding.report` is available, but `rsset.binding.bind` is blocked by
  `missing_accepted_base_evidence`.

Current RSSET report:

- `candidate_count=125`, `use_count=994`.
- Status counts: `blocked=124`, `already_recorded=1`.
- Top active group remains `rsset-raw-a6:022E`.

## Immediate Reference Surface

Concrete location:

- Candidate: `s0:000009A6`, `addi.w #4224,d1`.
- Family: `source_offset`.
- Target source offset: `$1080`.
- Conflicts: empty.

Policy result:

- `safe_to_mutate=false`.
- `command_candidate_count=0`, `report_only_candidate_count=9`.
- Candidate write policy is `report_only`; `immediate_ref.interpret` command
  support and verifier support are unavailable for source-offset matches until
  accepted runtime-address provenance exists.

## Outcome

No command-backed, verifier-backed, exact-round-trip Pandora mutation was
available. The issue result is a validated block, not a source edit. Final 017
closeout remains deferred to `017-027`.

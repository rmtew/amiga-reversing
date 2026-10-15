# Bounded backend fixture cleanup

The eight failures audited before the fresh Pandora reading are addressed only
in `tests/test_c_backend.py`. No production behavior or target facts change.
Two expectations follow the current native contract (runtime-range provenance
and use mask, and stable instruction identity without a display ordinal).
Three copied-view fixtures now exercise both data-only and independently
established execution contexts. The positive contained-view case uses JSR so the
second transfer is actually reachable; its former independent code seed is
removed. The data-copy case checks absence of runtime-control evidence, while
the executing case requires the exact source site, destination and evidence kind.
Both raw fixtures reassemble with C and independent vasm, using the configured
host vasm capability rather than a Linux-only executable path.

The Epic, ICE and Magicland tests skip only when their specific original input
is absent. Once present, decoding, analysis and assertions still fail normally;
no replacement game bytes or broad exception catches are introduced.

Validation (2026-10-15, Linux cloud):

```sh
.venv/bin/python -m pytest -q -rs -o addopts='' tests/test_c_backend.py \
  -k 'runtime_copy_storage_alias or contained_runtime_view or runtime_absolute_raw_binary_materializes or runtime_observation_view_maps_pc or epic_runtime_absolute or ice_bootloader_stage or runtime_ref_to_copied_range_start or magicland_org_bootstrap or runtime_data_range_shadows'
# 9 passed, 3 skipped, 223 deselected
.venv/bin/python -m pytest -q tests/test_native_entry_lineage.py tests/test_tool_graph.py
# 16 passed
```

A broader `-k 'runtime or copied or bootstrap or contained'` check gives
19 passed, 7 skipped and three failures. All three reproduce using the untouched
HEAD version of the test file against the same backend: Tetragon copied-stub
recognition, copied-image bootstrap view reason, and GenAm's missing original
input. These additional failures are retained, not weakened or folded into this
checkpoint. The earlier complete isolated native baseline already established
that the original eight failures predated the fresh restoration work; see
`docs/validation/pandora-eight-backend-baseline.json` if present and the recorded
eight-failure audit in the target status. This checkpoint is a focused repair,
not a claim that the entire backend integration suite passes.

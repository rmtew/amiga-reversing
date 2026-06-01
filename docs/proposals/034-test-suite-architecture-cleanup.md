# Proposal 034: Test Suite Architecture Cleanup

Status: proposed.

The test suite has accumulated coverage by adding tests at whatever seam was
most convenient at the time. That preserved behavior, but it also let
integration work leak into the normal developer loop and made later profiling
look like a cache or parallelism problem.

The rule is:

```text
unit tests prove one decision cheaply
contract tests prove one boundary explicitly
integration tests prove wiring across real tools and real targets
corpus tests prove selected real-world regressions
drift tests prove generated artifacts are current
```

The solution is not to hide slow tests, add gratuitous caches, or rely on
parallel execution. The solution is to make the suite structure match the
system structure, then reduce each layer by fixing repeated broad test seams.

## Tutorial: The Problem

The historical expectation was that non-CDP tests ran in under two minutes.
Recent full serial runs exceeded four minutes, and even after trimming obvious
duplicate work they remained around two and a half minutes:

```text
full pytest before cleanup:
  > 4 minutes

after obvious duplicate fixture cleanup:
  1575 passed, 73 skipped in 156.64s

fast default after layer taxonomy:
  1188 passed, 57 skipped, 403 deselected in 17.94s
```

The 17.94s result proves that a fast developer loop is possible, but it does
not prove the old base set was made efficient. It was achieved by making
integration tests opt-in:

```text
pytest tests
  -> unit/default developer loop

pytest tests -m integration
  -> wider integration layer
```

That is useful as a workflow correction, but it is not the end state. The
integration layer still contains the test design debt.

Measured opt-in layer profile:

```text
integration          387 passed, 16 skipped, 2:22
c_backend            208 passed, 15 skipped, 1:20
route_integration    133 passed, 24s
codegen_drift         24 passed, 9.8s
macos_real_fixture    11 passed, 7.8s
```

The slow tests are not one bad file. They are repeated broad seams.

## Tutorial: What The Pre-Research Shows

The integration profile points at a small number of repeated shapes:

```text
Damocles Tetragon native unpacking       14.16s
Macos committed project payload          10.56s
Bloodwych runtime/table analysis          6.79s
Pandora BK wrapper                        6.41s
Pandora table descriptors                 5.45s
data class listing/navigation/candidates  4.59s
string text examples                      4.45s
m68k diagnostic inventory                 3.48s
GenAm real LVO/RSSET tests                3.26s / 2.87s
Bloodwych generated source exact          3.10s
Magicland loader/self-decrunch            2.70s / 2.64s
MonAm callback/indexed pointer tests      2.52s / 2.01s
```

The C backend seam map makes the problem clearer:

```text
205 C backend tests

render_source       54
assemble            53
analyze_project     50
listing_source      45
direct_rebuild      35
listing_rows        25
analyze_binary      10
disk_backend         8
materialize          4
catalog_backend      3
```

The most common combinations are:

```text
pure/python                                         29
analyze_project only                               24
listing_source only                                21
listing_rows only                                  15
assemble + direct_rebuild + render_source          15
render_source only                                 13
assemble + render_source                           11
analyze_project + assemble                         10
direct_rebuild only                                 8
analyze_project + listing_source                    6
```

That means the cleanup should not chase individual slow tests one at a time.
It should split the test harness by actual seam:

```text
analysis facts
listing rows
source rendering
assembly/rebuild
disk import
runtime materialization
route dispatch
generated artifact drift
```

The route layer shows the same pattern. Most route tests seed listing rows,
mock project resolution, call `route_request`, and then assert command catalog
or manual-action behavior. That is command logic wrapped in a route envelope.
The route smoke should remain, but the command matrix should move to a direct
command harness.

The drift layer also mixes jobs. `test_m68k_coverage.py` repeatedly builds
current generated inventories while also testing inventory algorithms.
`test_macos_runtime_generation.py` repeatedly extracts baseline metadata while
also checking parser behavior. These should become small synthetic parser tests
plus one real drift test per generator.

The Mac real fixture layer repeatedly imports the same MPW image for different
views of the same payload. One test should prove real image import. Projection
tests should consume a durable imported packet fixture.

## Tutorial: The Current Shape

The current taxonomy is explicit:

```python
# tests/conftest.py
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item_is_c_backend(item):
            item.add_marker(pytest.mark.c_backend)
            item.add_marker(pytest.mark.integration)
        if item_is_route_integration(item):
            item.add_marker(pytest.mark.route_integration)
            item.add_marker(pytest.mark.integration)
        if item_is_codegen_drift(item):
            item.add_marker(pytest.mark.codegen_drift)
            item.add_marker(pytest.mark.integration)
```

The default loop excludes integration:

```toml
[tool.pytest.ini_options]
addopts = ["-m", "not integration and not real_integration and not web_e2e"]
```

This is a routing table for test work, not a claim that the integration layer
is efficient.

```text
default unit loop
  fast enough for local edit feedback

integration loop
  non-real integration contracts and tool-bound checks

real integration loop
  real corpus sentinels and historical regressions

web e2e loop
  Brave/CDP browser checks
```

The next step is to reduce integration cost by correcting test seams.

## Tutorial: Anti-Pattern 1 - Real Corpus Tests Prove Too Much

Some tests use a real target because the bug was found in a real target, then
keep adding assertions for every related fact.

Example shape:

```python
analysis = analyze_binary_source_with_c_backend(
    PROJECT_ROOT / "tests" / "fixtures" / "hunk" / "damocles_tetragon_53b24620.bin",
    project_root=PROJECT_ROOT,
)

tetragon_events = [
    event for event in analysis["decompression_events"]
    if event.get("codec_id") == "tetragon"
]

assert len(tetragon_events) == 2
assert tetragon_events[1]["entry_validation_valid"] is True
assert tetragon_events[1]["entry_validation_accepted_instructions"] == 25003
assert tetragon_events[1]["decompressed_sha256"] == "3438..."
```

That test is doing several jobs:

```text
real fixture import
  -> native unpacker detection
  -> native unpack execution
  -> entry validation
  -> payload role classification
  -> exact regression hashes
```

The corrected structure is:

```text
synthetic codec contract
  proves Tetragon marker and event metadata

synthetic entry-validation contract
  proves valid code-bearing payload acceptance

native decompressor contract
  proves materialized bytes for a small fixture

real Damocles corpus smoke
  proves the real target still exposes the two expected events
```

The real target should be the smoke test, not the only place where all behavior
is specified.

## Tutorial: Anti-Pattern 2 - Crossing the C Boundary For Every Assertion

`tests/test_c_backend.py` repeatedly crosses expensive seams:

```text
render_source       54 tests
assemble            53 tests
analyze_project     50 tests
listing_source      45 tests
direct_rebuild      35 tests
```

That usually means tests are using a broad "render and rebuild everything" seam
when they only need one contract.

Bad shape:

```text
test wants to prove:
  "indexed pointer table comparator stays clean"

test does:
  build full listing artifact
  render full source text
  assemble source
  compare rebuilt bytes
  inspect profile
```

Preferred shape:

```text
analysis-only contract
  input: synthetic hunk or small target fixture
  output: table descriptor facts

render-only contract
  input: small analysis/render IR fixture
  output: source line text

rebuild contract
  input: one representative source output
  output: exact binary bytes

real corpus smoke
  input: one real target
  output: no source refusal and expected sentinel fact
```

Code should make this easy:

```python
def analyze_fixture(source: BinarySource) -> AnalysisFacts:
    ...

def render_fixture(facts: AnalysisFacts) -> str:
    ...

def rebuild_fixture(source_text: str) -> bytes:
    ...
```

The key is that a test should choose one helper because it needs that layer,
not because that helper returns many convenient fields.

## Tutorial: Anti-Pattern 3 - Route Tests Are Command Unit Tests In Disguise

`route_integration` takes about 24s. Most of that is not true route coverage.
Many tests seed a fake listing artifact, call `route_request`, then assert that
the command catalog or manual action payload is correct.

Current shape:

```python
_seed_c_listing_artifact(monkeypatch, "bloodwych", _RowsCListingArtifact(rows))
monkeypatch.setattr(disasm_server, "get_project", ...)
monkeypatch.setattr(disasm_server, "resolve_project_paths", ...)
monkeypatch.setattr(disasm_server, "append_manual_action", append_action)

payload = disasm_server.route_request(
    "POST",
    "/api/projects/bloodwych/commands/execute",
    {},
    {
        "command_id": "comment.edit",
        "context": _row_command_context(rows[0]),
        "parameters": {"text": "review"},
    },
)

assert payload["data"]["action"]["kind"] == "comment.edit"
```

That test is mostly command execution logic. The route adds setup and response
wrapping noise.

Preferred shape:

```text
command catalog unit test
  rows + context -> command list

command execution unit test
  command_id + context + parameters -> manual action + local effects

route smoke test
  HTTP-ish request -> correct dispatch and response envelope
```

A direct harness would look like:

```python
def execute_command_fixture(
    *,
    rows: list[ListingRow],
    command_id: str,
    context: dict[str, object],
    parameters: dict[str, object],
) -> CommandExecutionResult:
    catalog = build_command_catalog(rows=rows, context=context)
    return execute_catalog_command(catalog, command_id, parameters)
```

Then only a small number of tests need `route_request`.

## Tutorial: Route Command Split Map

The route-marked tests in `tests/test_disasm_server.py` currently split like
this:

```text
113 route-marked tests

commands/execute      39
commands catalog      15
listing routes        26
project routes        20
reproduction routes    4
project create/import  2
tool routes            1
other                  6
```

The command-heavy part is the clearest cleanup target:

```text
54 command catalog/execute tests
  many seed a listing artifact
  many monkeypatch get_project / resolve_project_paths / append_manual_action
  many call route_request
  most assert command payloads, manual action payloads, local effects, or locator behavior
```

The implementation already has useful internal seams:

```python
def _command_catalog_payload(project_name: str, query: dict[str, list[str]]) -> dict[str, object]:
    context, rows = _command_context_from_query(project_name, query)
    ...

def _execute_command(project_name: str, body: Mapping[str, object] | None) -> dict[str, object]:
    command_context, rows = _command_context_from_body(project_name, context)
    catalog = _command_catalog_payload(project_name, _query_from_command_context(command_context))
    ...

def _execute_manual_action_command(
    project_name: str,
    action_id: str,
    context: Mapping[str, object],
    rows: list[dict[str, object]],
    parameters: dict[str, object] | None,
    *,
    workflow_profile: WorkflowProfile | None = None,
) -> dict[str, object]:
    ...
```

The problem is not that these seams are absent. The problem is that tests reach
them through `route_request`, so each command rule pays route parsing,
projection service setup, locator lookup, durable project patching, append
mocking, invalidation, and response wrapping.

### Command Catalog Tests

Current shape:

```text
test_route_manual_action_catalog_returns_review_item_actions
test_route_manual_action_catalog_returns_target_commands
test_route_manual_action_catalog_returns_row_and_element_actions
test_route_manual_action_catalog_returns_range_actions_with_mixed_eligibility
...

route_request(GET /api/projects/bloodwych/commands)
  -> _command_catalog_payload
  -> context resolution
  -> action catalog
  -> command entry/web envelope
```

Split:

```text
catalog contract tests
  direct action catalog functions:
    target_action_catalog
    review_item_action_catalog
    listing_row_action_catalog
    listing_element_action_catalog
    listing_range_action_catalog

command-entry contract tests
  action + context -> command_id, effect, target_context, required_parameters, typed_error

route smoke tests
  GET /commands target context
  GET /commands row locator context
  malformed locator -> CommandContractError code
```

The target-command catalog test is especially broad. It currently checks
navigation, source export, reproduction profile, target equates, execution
views, RSSET regions, and history commands in one route body. That should become
catalog unit tests plus one route envelope smoke.

### Command Execute Tests

Current shape:

```text
test_route_manual_action_catalog_execute_appends_target_equate_action
test_route_manual_action_catalog_execute_returns_custom_struct_local_effect
test_route_manual_action_catalog_execute_returns_typed_field_local_effect
test_route_manual_action_catalog_execute_appends_comment_action
test_route_manual_action_catalog_execute_range_uses_explicit_applicable_subranges
...

route_request(POST /api/projects/bloodwych/commands/execute)
  -> _execute_command
  -> _command_context_from_body
  -> _command_catalog_payload
  -> _execute_manual_action_command
  -> append_manual_action
  -> _manual_action_application_payload
  -> invalidation
  -> mutation/workflow profile response
```

Split:

```text
manual payload contract
  action_id + context + parameters -> manual action kind/payload

local effect contract
  manual action kind/payload + context -> application local effects

invalidation contract
  manual action kind -> listing cache clear or presentation dirty

execute envelope smoke
  POST /commands/execute comment.edit returns:
    command_id
    effect
    context
    mutation
    workflow_profile
```

A direct test harness should make the durable boundary explicit:

```python
def execute_manual_command_fixture(
    *,
    project_id: str = "bloodwych",
    command_id: str,
    context: dict[str, object],
    rows: list[dict[str, object]] = [],
    parameters: dict[str, object] | None = None,
) -> dict[str, object]:
    append_log: list[dict[str, object]] = []
    result = _execute_manual_action_command(
        project_id,
        command_id,
        context,
        rows,
        parameters,
        workflow_profile=WorkflowProfile("manual_command_execution", target_id=project_id),
    )
    return {"result": result, "appended_actions": append_log}
```

That harness should still mock durable append, but it should not route through
HTTP-ish dispatch for every command.

### Slice 2 Implementation Checkpoint - Target Command Execution

The first route cleanup pass moved target-level manual command execution tests
off `route_request()` and onto `_execute_manual_action_command()` directly.

Before, these tests paid the route and command-availability path even though
they asserted only manual action payloads and local effects:

```text
POST /api/projects/bloodwych/commands/execute
  -> _execute_command
  -> _command_context_from_body
  -> _command_catalog_payload
  -> _execute_manual_action_command
  -> manual action append
  -> local application payload
```

The direct helper now states the seam explicitly:

```python
payload, appended_actions = _execute_manual_command_fixture(
    monkeypatch,
    tmp_path,
    command_id="target.execution_view.add",
    context={"kind": "target"},
    parameters={
        "source_start": 0x20,
        "source_end": 0x80,
        "base_addr": 0x4000,
        "name": "stage_code",
    },
)
```

Coverage moved:

```text
target.execution_view.add
target.execution_view.edit
target.execution_view.remove
target.rsset_region.add
target.rsset_region.edit
target.rsset_region.remove
app_slot.rename
app_slot.remove
target.equate.add/edit/represent/rename/remove
target.custom_struct add/edit/remove/rename
target.custom_struct_field add/edit/remove/rename
typed_gap.field.add
typed_access.field.rename
typed_gap.field.add with selected evidence context
review_note.add/edit/clear
label.rename create/rename/absolute-domain cases
row.seed.data.palette
row.seed.data.named
review.seed.data copper_list/named
review.seed.remove
review.label.rename
representation.character
element.seed.data.named
```

Measured result for the converted cases:

```text
pytest tests\test_disasm_server.py -k "test_command_manual_action_execute" -q
  35 passed, 147 deselected in 0.74s

pytest tests\test_disasm_server.py --collect-only -q
  89 selected, 93 deselected

pytest tests\test_disasm_server.py -m route_integration -q
  93 passed, 89 deselected in 13.53s

pytest tests -q
  1241 passed, 57 skipped, 350 deselected in 16.40s
```

Element command tests exposed an important boundary: public element contexts are
not enough for direct manual payload checks. They need the resolved element
context that route/body handling normally supplies:

```python
context = disasm_server._selected_command_element_context(row_payload, element_id)
context["target"] = "bloodwych"
context["locator"] = _row_locator(row)
context["projection_hash"] = "cache"
```

That is a useful distinction for the rest of the route split:

```text
public locator context
  belongs in route/locator tests

resolved command context
  belongs in direct command payload tests
```

The review-note conversion exposed the same principle for row payloads:
route-resolved listing rows carry `row_index`, and direct command fixtures must
include that field when the command payload depends on row identity.

A follow-up default profile showed that the suite still has headroom, and the
slowest default tests are not the converted command tests:

```text
pytest tests -q --durations=30
  1241 passed, 57 skipped, 350 deselected in 16.40s

slowest default calls:
  test_active_runtime_imports_are_current_package_or_standard_library  0.70s
  test_agent_listing_backed_comment_smoke_uses_harness_path            0.49s
  reversing-loop decision journal / planner CLI tests                  0.18s-0.39s
  import_adf help/materialization tests                                0.14s-0.22s
```

The next route pass should therefore batch row/element command moves and keep a
route-envelope smoke for command execution, rather than moving one test at a
time and remeasuring noise.

### Locator And Projection Tests

Some command tests are genuinely about locator behavior:

```text
row command resolves without all rows materialization
element command resolves without all rows materialization
same-address comment ids stay distinct
same-address label ids stay distinct
stale/malformed locator returns a command contract error
```

These should not become pure catalog tests. They should target locator
resolution directly:

```text
_command_context_from_query
_command_context_from_body
_resolve_command_locator
_resolve_command_range_locator
```

Keep one route smoke for each public error code:

```text
missing_locator
stale_locator
ambiguous_locator
non_mutable_command
invalid_command_context
```

### Listing Routes

The 26 listing route tests are more plausibly route-level, but many still test
artifact behavior through the route:

```text
index window
anchor window
address window
source offset window
navigation payload
API call annotation
projection dirty reads
cache reuse
disk project rejection
listing job open/status
```

Split:

```text
listing artifact contract
  window selection, anchor selection, source offset lookup, navigation payload

listing annotation contract
  rows + platform call metadata -> api_call fields

projection service contract
  locator normalization, projection hash, dirty presentation reads

route smoke
  GET /listing returns normalized payload
  GET /listing/navigation returns overlaid navigation
  POST /listing/open and GET /listing/status dispatch to job layer
```

### Workflow Harness Tests

`tests/test_api_workflow_harness.py` is correctly route-oriented. It proves a
durable workflow across listing fetch, command execution, project reload, stale
locator recovery, and browser-refresh-equivalent snapshots:

```text
GET /listing
POST /commands/execute
GET /project
GET /listing after mutation
assert durability matrix
```

These should remain integration tests. They are the higher-level sentinels that
allow many individual command route tests to move downward.

## Tutorial: Anti-Pattern 4 - Generated Drift Tests Rebuild Whole Worlds

`codegen_drift` is small in count but expensive relative to purpose:

```text
test_m68k_coverage.py
  build_diagnostic_inventory()
  build_canonical_inventory()
  CLI report/check calls

test_macos_runtime_generation.py
  load generator
  extract baseline metadata
  render header/source/json
```

Some of these tests verify algorithms. Others verify committed generated files
are current.

They should be separate:

```text
algorithm tests
  small synthetic metadata
  default or cheap opt-in

drift tests
  one real extraction
  one render comparison
  opt-in codegen_drift
```

Current repeated shape:

```python
generator = _load_generator()
metadata = generator.extract_baseline_metadata()

assert _record_by_name(metadata, "Rect")["size"] == 8
```

Preferred shape:

```python
def test_record_extraction_from_small_fixture() -> None:
    metadata = extract_metadata_from_text(SMALL_MAC_TYPES_FIXTURE)
    assert metadata["records"][0]["name"] == "Rect"

def test_generated_mac_os_runtime_metadata_is_current() -> None:
    metadata = extract_baseline_metadata()
    assert generated_files_equal(render_all(metadata))
```

The first test proves parser behavior. The second proves repository drift.

## Tutorial: Generated And Drift Split Map

The codegen layer is not large by count, but it repeats full generated-world
work in tests that are partly algorithm checks.

### M68K Coverage

Current shape:

```text
test_diagnostic_inventory_loads_current_generated_form_tables
  build_diagnostic_inventory() with current generated tables

test_canonical_inventory_summarizes_current_generated_data
  build_canonical_inventory() with current generated tables

test_diagnostic_report_command_prints_counts
  m68k_coverage.main(["report", "--phase", "diagnostic"])

test_canonical_report_command_prints_summaries
  m68k_coverage.main(["report", "--phase", "canonical"])

test_diagnostic_check_command_succeeds_with_current_classified_data
  m68k_coverage.main(["check", "--phase", "diagnostic"])

test_canonical_check_command_prints_canonical_summaries
  m68k_coverage.main(["check", "--phase", "canonical"])
```

The same file also has good cheap tests that already use `FakeForm`:

```python
inventory = m68k_coverage.build_diagnostic_inventory(
    assembler_forms=[matched_asm, asm_only],
    disassembler_forms=[matched_disasm, disasm_only],
)
```

Split:

```text
default/synthetic
  unmatched form accounting
  missing sample strategy classification
  unsupported family stale/active logic
  strict coverage failure classification
  report text formatting with injected inventory

codegen_drift
  one diagnostic inventory smoke over current generated data
  one canonical inventory smoke over current generated data
  one CLI check smoke for report/check dispatch
```

The CLI tests should not each rebuild the current inventory if the thing under
test is output formatting. Prefer injectable inventory builders:

```python
def test_diagnostic_report_formats_counts(capsys) -> None:
    inventory = diagnostic_inventory_fixture()
    assert m68k_coverage.report_inventory(inventory) == 0
```

Then retain one real command smoke:

```text
m68k_coverage check --phase canonical
  proves current generated artifacts still satisfy the full check path
```

### Mac OS Runtime Generation

Current shape:

```text
test_record_extraction_covers_baseline_structs_with_source_evidence
  load generator
  extract_baseline_metadata()
  assert Rect, EventRecord, HVolumeParam

test_trap_extraction_covers_baseline_calls_with_register_protocol
  load generator
  extract_baseline_metadata()
  assert _GetResource, _WaitNextEvent, _UnloadSeg, _LoadSeg, _GetFNum, ...

test_num_to_string_is_package_macro_not_opword_alias
  load generator
  extract_baseline_metadata()
  assert package macro classification

test_generated_mac_os_runtime_metadata_is_current
  load generator
  extract_baseline_metadata()
  render header/source/json and compare committed files
```

This repeats full baseline extraction for parser-rule checks.

Split:

```text
default/synthetic
  record parser from small AIncludes text fixture
  trap parser from small trap/opword fixture
  package macro parser for _NumToString-style case
  C prototype/register protocol extraction from small fixture

codegen_drift
  one full extract_baseline_metadata()
  compare mac_os_runtime.h
  compare mac_os_runtime.c
  compare mac_os_runtime.json
```

The parser tests should exercise the same parser functions that baseline
extraction uses, but against small text:

```python
def test_record_parser_extracts_offsets_from_small_fixture() -> None:
    metadata = extract_metadata_from_text({
        "Interfaces/AIncludes/MacTypes.a": RECT_FIXTURE,
    })
    rect = record_by_name(metadata, "Rect")
    assert field_by_name(rect, "right")["offset"] == 6
```

If the generator cannot currently parse from injected text, that is the seam to
add. Do not preserve repeated full baseline extraction just because it is the
only convenient API.

## Tutorial: Anti-Pattern 5 - Real Mac Fixture Tests Repeat The Import

The Mac real fixture layer repeatedly opens the MPW image and rebuilds related
views:

```python
def _imported() -> dict[str, Any]:
    _requires_real_fixture()
    return import_mpw_asm_container(IMAGE_PATH)
```

Then several tests assert different projections of the same imported payload:

```text
HFS item recognized
CODE inventory matches committed metadata
CODE 1 preview exists
CODE 1 can be sent through listing backend
web payload exposes source and binary pivots
```

The useful split is:

```text
one real fixture import contract
  IMAGE_PATH -> durable imported container packet

many projection unit tests
  imported packet fixture -> web/source/listing views
```

Textual flow:

```text
MPW-GM.img.bin
  -> real importer contract
  -> committed/imported packet shape
      -> source view tests
      -> web view tests
      -> listing source tests
```

Most tests do not need to open the image. They need a representative packet.

## Tutorial: Mac Real Fixture Split Map

The Mac fixture tests repeat the same expensive real-world input:

```text
resources/platform_macos/MPW-GM.img.bin
  -> ndif2raw / HFS read
  -> MPW/Tools/Asm file
  -> resource fork
  -> CODE 0..27
  -> selected CODE 1 Main
  -> listing/project/web views
```

Current repeated real fixture shapes:

```text
test_macos_asm_container.py
  _imported() calls import_mpw_asm_container(IMAGE_PATH) in multiple tests
  extract_mpw_asm_code_bytes(IMAGE_PATH, resource_id=1)
  build listing artifact from CODE 1 bytes

test_macos_web_view.py
  _payload() imports the real container for several web projection tests

test_macos_container_payload.py
  build container payload from real MPW image
  import resource CODE file and write child target descriptor

test_macos_target_artifact.py
  committed target/project descriptor checks
  real listing source from MPW image
  committed asm artifact compared with real C summary
  full Mac listing artifact analysis/summary/navigation/source/window

test_macos_project_payload.py
  broad synthetic/faked C summary test
  real committed MPW fixture smoke
```

Split:

```text
real image import sentinel
  MPW-GM.img.bin -> imported container packet
  assert HFS file identity, fork roles, resource type counts, selected CODE 1 identity

committed artifact sentinel
  real C summary + committed asm artifact
  assert every CODE resource has a source block
  assert selected CODE 1 entry/source shape remains present

packet projection tests
  imported container packet fixture -> web payload
  imported container packet fixture -> source/binary boundary
  imported container packet fixture -> restored source failure modes

listing projection tests
  small CODE byte fixture -> MacosCodeListingArtifact source/window behavior
  synthetic project descriptor -> native Mac source descriptor behavior

project payload tests
  faked C summary + source fixture metadata -> binary_container_view/source_quality/navigation
```

The packet fixture should be explicit, not an implicit cache:

```json
{
  "fixture": "mpw_tools_asm_import_packet_v1",
  "source_image": "resources/platform_macos/MPW-GM.img.bin",
  "hfs_path": "MPW-GM/MPW/Tools/Asm",
  "file": {"type": "MPST", "creator": "MPS ", "cnid": 2310},
  "code_resources": [
    {"id": 0, "role": "jump_table_segment"},
    {"id": 1, "role": "code_segment", "name": "Main", "code_entry_offset": 40}
  ]
}
```

Tests using this packet are not pretending to test image import. They test
projection behavior from a known imported shape.

Real fixture tests that should remain:

```text
MPW image import smoke
  proves image/provider/HFS/resource parsing still works

MPW CODE resource extraction smoke
  proves CODE 1 bytes can still be extracted and decoded by the listing backend

committed Mac target smoke
  proves tracked project/asm artifacts still match the real image summary
```

Everything else should prefer small packet or summary fixtures.

## Proposed Cleanup Slices

### Slice 1 - Introduce Layer-Specific Test Helpers

Create helpers that make the chosen seam explicit:

```python
def assert_analysis_facts(source: BinarySource) -> dict[str, object]:
    ...

def assert_listing_rows(source: BinarySource) -> list[dict[str, object]]:
    ...

def assert_rendered_source(source: BinarySource) -> str:
    ...

def assert_rebuild_exact(source_text: str, original: bytes) -> None:
    ...
```

The important rule is that helpers must not silently do more than their name
promises. If a test needs rendering, it asks for rendering. If it needs rebuild,
it asks for rebuild.

Initial targets:

```text
assemble + direct_rebuild + render_source
  split into render contract and rebuild contract

analyze_project + assemble
  split into analysis fact contract and one rebuild sentinel

listing_source-only tests
  check whether listing rows or renderer output is the actual subject
```

### Slice 2 - Extract Command Catalog And Execution Harnesses

Move route-heavy command tests behind direct command functions:

```text
route_request()
  parse request
  resolve project/artifact
  call command catalog or executor
  wrap response
```

Tests should target:

```text
command catalog behavior      many tests
command execution behavior    many tests
route envelope behavior       few tests
```

This should reduce `route_integration` from many medium route tests to a small
route smoke layer plus fast command unit tests.

### Slice 3 - Replace Broad Real Corpus Assertions With Synthetic Contracts

For each slow real target test, ask:

```text
Which invariant is this proving?
Can the invariant be proven with a minimal hunk/raw fixture?
What real target sentinel remains necessary?
```

Example:

```text
Damocles Tetragon
  keep: real target exposes two Tetragon events with expected load/entry ranges
  move: entry validation behavior to synthetic code-bearing payload fixture
  move: copied-stub metadata to synthetic native unpacker fixture
  move: exact decompressed hash to materialization contract fixture
```

The real corpus smoke remains valuable. It should not be the only test for the
underlying rules.

Initial real-corpus split matrix:

```text
Damocles Tetragon
  keep: two real events with expected load/entry ranges
  move: entry validation, copied-stub metadata, materialized hash

Pandora BK wrapper
  keep: real wrapper provider and payload identity smoke
  move: provider metadata and payload role classification

Bloodwych runtime/table analysis
  keep: one target-level source/listing sentinel
  move: runtime copy, jump table, scalar table, pointer table, row class rules

Magicland/Conqueror/Voodoo native unpacking
  keep: one real boot/decrunch path per family
  move: small native decompressor and materialization contracts

GenAm/MonAm symbol and table cases
  keep: one real target smoke per program family
  move: LVO, RSSET, callback, indexed pointer, and data symbol rules
```

## Tutorial: C Backend Split Map

The first cleanup pass should be planned as a coverage-preserving split, not a
deletion pass.

### Current C Backend Profile

After the generated/drift and route-command cleanup passes, the C backend layer
is still dominated by broad real-corpus tests:

```text
pytest tests -m c_backend -q --durations=30
  208 passed, 15 skipped, 1425 deselected in 79.96s

slowest:
  Damocles Tetragon native unpacking                         13.58s
  Bloodwych runtime copy and table rows                       6.78s
  Pandora BK wrapper                                          6.20s
  table descriptors use evidence bounds not caps              5.13s
  data classes reach rows/navigation/candidates               4.35s
  string text examples render from evidence                   3.67s
  Bloodwych generated source assembles exact                  2.90s
  Magicland loader file transfers                             2.60s
  Magicland self-decrunch materialization                     2.44s
  MonAm callback field targets                                2.37s
```

The next C backend cleanup should split these by seam. The most valuable first
target remains Damocles Tetragon because it combines real corpus detection,
native execution, materialization hashes, payload role classification, entry
validation, and copied-stub metadata in one test.

The broader marker split shows that real corpus sentinels now run as their own
layer rather than being silently folded into every integration run:

```text
pytest tests -q
  1241 passed, 407 deselected in 18.26s

pytest tests -m integration -q --durations=10
  204 passed, 1444 deselected in 39.69s

pytest tests -m real_integration -q --durations=10
  130 passed, 16 skipped, 1502 deselected in 103.64s

pytest tests -m "c_backend and not real_integration" -q --durations=15
  92 passed, 1556 deselected in 11.21s
```

This does not mean real corpus tests should be hidden or weakened. It means the
suite should name the cost honestly:

```text
contract/backend integration
  synthetic and small-fixture C boundary checks

real corpus integration
  selected real targets and historical regressions
```

That marker cleanup is now implemented. The remaining C backend work is to make
the real corpus layer itself cheaper by splitting broad tests such as Damocles,
Bloodwych, and Pandora into smaller contract tests plus retained corpus
sentinels.

### Damocles Tetragon

Current test:

```text
test_real_dll_damocles_tetragon_native_unpacking_candidates
  analyze full Damocles fixture
  find two Tetragon events
  assert section offsets and compressed ranges
  assert postpass metadata
  assert output sizes and hashes
  assert entrypoint/load ranges
  assert payload role and validation counters
  assert copied stub storage/runtime/transfer offsets
```

Split:

```text
real corpus smoke
  assert two Tetragon events
  assert section 1 load/entry $40000
  assert section 2 load $1000 entry $59484
  assert both are materializable primary programs

native Tetragon contract
  small fixture -> compressed range, postpass range, escape byte, consumed offsets

entry validation contract
  known code-bearing payload -> valid, accepted instruction count, no required failures
  known corrupt payload -> invalid or below threshold

copied stub contract
  copied stub pattern -> storage offset, runtime address, transfer offset

materialization contract
  event id -> output size and sha256
```

The real Damocles fixture remains, but it stops carrying every rule.

#### Damocles Pre-Research

Focused timings show that the cost is not the Python assertion count:

```text
pytest tests\test_c_backend.py -m real_integration \
  -k "damocles or voodoo or magicland or conqueror" -q --durations=20

  Damocles Tetragon native unpacking        13.97s
  Magicland self-decrunch materialization    2.65s
  Magicland loader transfers                 2.14s
  Voodoo Tetragon comparator                 1.03s
  Conqueror native decrunch materialization  0.33s
```

Direct backend timing confirms the expensive seam:

```text
analyze_binary_source_with_c_backend(damocles_tetragon_53b24620.bin)
  14.028s

materialize_recognized_unpacker_event_with_c_backend(section 2 event)
  11.850s
```

The C implementation already has useful internal pieces:

```c
recognized_tetragon_try_unpack_event_local(...)
  -> pure Tetragon LZ stage
  -> postpass
  -> decompressed hash
  -> entry validation

recognized_unpacker_attach_copied_stub_local(...)
  -> copied runtime view metadata
  -> copied-stub transfer metadata

recognized_unpacker_try_native_copied_stub_local(...)
  -> build concrete memory image
  -> execute copied target-owned unpacker
  -> validate output span and entrypoint
```

But the exposed Python test API only reaches those pieces through full source
analysis:

```python
analysis = analyze_binary_source_with_c_backend(fixture)
result = materialize_recognized_unpacker_event_with_c_backend(
    "amiga-hunk",
    fixture,
    event_id,
    output_path,
)
```

That means a better assertion split is necessary but not sufficient. To reduce
runtime, the backend needs either small fixture coverage that avoids the
Damocles-sized native execution path, or a narrow C test seam for recognized
unpacker contracts.

The profile output currently hides this cost. For the 14s Damocles analysis,
`profile["facts_v2"]` reports normal analysis work in milliseconds because
`append_object_decompression_analysis_json()` runs the decompression probes
after the main facts profile has already been built. Add explicit timing fields
for:

```text
decompression_candidate_scan_seconds
decompression_provider_probe_seconds
decompression_self_decrunch_seconds
decompression_recognized_unpacker_seconds
decompression_event_json_seconds
```

Without those timings, test cleanup work will keep chasing the wrong layer.

#### Decompression Timing Checkpoint

The backend now exposes decompression probe timings in the analysis profile:

```json
{
  "profile": {
    "decompression": {
      "decompression_candidate_scan_seconds": 1.121,
      "decompression_provider_probe_seconds": 0.088,
      "decompression_self_decrunch_seconds": 1.296,
      "decompression_recognized_unpacker_seconds": 12.553,
      "decompression_event_json_seconds": 0.0
    }
  }
}
```

The focused Tetragon test pass now proves two things:

```text
synthetic Tetragon marker test
  profile exposes all decompression timing keys

real Damocles Tetragon sentinel
  recognized-unpacker timing is nonzero
  copied-stub native execution exposes step count
```

Verification:

```text
cmd /c src\build.bat
  passed

src\build\m68k_c_unit_tests.exe
  passed

pytest tests\test_c_backend.py -m c_backend -k "tetragon" -q --durations=20
  3 passed, 220 deselected in 18.72s

pytest tests\test_c_backend.py -m "c_backend and not real_integration" -q --durations=15
  92 passed, 131 deselected in 11.73s

uv run ruff check tests\test_c_backend.py tests\conftest.py pyproject.toml
  passed

uv run mypy
  passed
```

This does not reduce Damocles yet. It makes the real cost measurable and shows
the next fix belongs inside the recognized-unpacker/native copied-stub path.

Measured Damocles after instrumentation:

```text
profile.decompression:
  decompression_candidate_scan_seconds       1.116
  decompression_provider_probe_seconds       0.089
  decompression_self_decrunch_seconds        1.358
  decompression_recognized_unpacker_seconds 11.589
  decompression_event_json_seconds           0.000

section 2 copied-stub native execution:
  native_execution_step_count 15537114
  native_execution_stop_reason pc_range
```

This means the next viable cleanup is not another marker split. It is a
contract/runtime split for the copied-stub native executor:

```text
small copied-stub contract
  proves runtime-view/stub metadata and simulator stop behavior in thousands of
  steps, not millions

real Damocles sentinel
  proves the real target still reaches materializable status and expected
  load/entry identity
```

Existing synthetic copied-runtime tests prove runtime views and materialized
runtime code, but they do not exercise recognized Tetragon copied-stub native
execution. Damocles is still the only current fixture for this exact path.

#### Slice 6 Implementation Checkpoint - Tetragon Copied-Stub Contract

The copied-stub metadata has been moved to a small synthetic hunk contract:

```text
test_listing_analysis_identifies_tetragon_copied_stub_transfer_without_real_payload
  synthetic Tetragon marker
  synthetic copy loop from storage bytes to runtime $100
  traced indirect jump into copied stub
  asserts copied_stub_storage_offset/runtime_address/transfer_offset/site_offset
  asserts native execution is not attempted because no real packed payload exists
```

Measured focused result:

```text
pytest tests\test_c_backend.py -m c_backend -k "tetragon" -q --durations=20
  4 passed, 220 deselected in 15.17s

slowest:
  real Damocles native unpacking sentinel    13.16s
  Voodoo Tetragon comparator                 0.89s
  synthetic marker contract                  0.13s
  synthetic copied-stub contract             0.05s
```

The real Damocles test is now a sentinel:

```text
real Damocles sentinel
  two Tetragon events
  no false self-decrunch event
  both payloads materializable
  expected load/entry identity
  section 2 native copied-stub path ran
```

This confirms that assertion cleanup alone cannot remove the remaining cost.
The 13s wall time is real native decompressor execution:

```text
recognized-unpacker phase
  simulates the copied target unpacker
  writes and validates a $779C9-byte output
  validates the code-bearing entrypoint
```

The next production seam is one of:

```text
analysis summary mode
  detect and describe copied-stub Tetragon without executing full native output

materialization-only validation
  keep expensive native execution in materialize_recognized_unpacker_event
  make ordinary analysis report a pending/materializable-by-native descriptor

small valid copied-stub compressed fixture
  same native path, intentionally tiny output
```

The first two affect import behavior and UI semantics, so they need design work
before implementation. The third needs a known valid small Tetragon payload or a
test-only fixture generator; it should not be faked by asserting less on
Damocles.

#### Slice 6B Implementation Checkpoint - Real Damocles Assertions Narrowed

The real Damocles Tetragon test no longer asserts exact decompressed output
sizes and hashes. Those are materialization details, not the purpose of the real
corpus sentinel. The test now checks:

```text
two Tetragon events
no false self-decrunch event
recognized-unpacker timing is visible
both events are materializable primary programs
both entrypoints validate as code-bearing payloads
section 1 load/entry identity is $40000/$40000
section 2 load/entry identity is $1000/$59484
section 2 native copied-stub execution ran
```

Focused timing confirms the remaining cost is native execution, not assertion
breadth:

```text
pytest tests\test_c_backend.py -m c_backend -k "tetragon" -q --durations=20
  4 passed, 220 deselected in 15.41s

slowest:
  real Damocles native unpacking sentinel    13.46s
  Voodoo Tetragon comparator                 0.88s
  synthetic marker contract                  0.15s
  synthetic copied-stub contract             0.05s
```

The next implementation opportunity is a backend seam that can prove native
copied-stub/Tetragon materialization on a small extracted stream or direct C
unit fixture without simulating the full Damocles section 2 payload on every
real-integration run.

#### Slice 6C Implementation Checkpoint - Damocles Native Execution Deferred

The backend seam is now explicit. Ordinary recognized-unpacker analysis no
longer runs the native copied-stub simulator for a copied-stub Tetragon event.
It records a materializable deferred event:

```json
{
  "status": "materializable",
  "reason": "native_tetragon_unpack_deferred",
  "payload_role": "primary_program",
  "payload_role_confidence": "signature_only",
  "native_execution_deferred": true,
  "target_start_address": 4096,
  "entrypoint": 365700
}
```

The expensive native executor now belongs to the materialization boundary:

```text
analysis request
  -> detect marker
  -> detect copied-stub storage/runtime copy
  -> infer output span and entrypoint
  -> report native_execution_deferred

materialize recognized unpacker event
  -> rebuild analysis context
  -> run native copied-stub simulator
  -> validate entrypoint
  -> write output bytes
  -> return verified size/hash/role metadata
```

Import had to move with the seam. Deferred events may not have a verified
`decompressed_sha256` in analysis. The disk importer now accepts such events
only when they are materializable recognized unpacker events, then fills the
child origin and decompression record from the materialization result.

The real Damocles test is now a candidate-analysis sentinel:

```text
two Tetragon events exist
no false self-decrunch event
section 1 remains natively validated in analysis
section 2 is materializable but native_execution_deferred
section 2 copied-stub metadata/load/entry survives
```

The focused profile shows the original overreach has been removed from the
candidate-analysis test:

```text
pytest tests\test_c_backend.py -m c_backend -k "tetragon" -q --durations=20
  4 passed, 220 deselected in 4.07s

slowest:
  real Damocles deferred-analysis sentinel     2.77s
  Voodoo Tetragon comparator                   0.93s
  synthetic marker contract                    0.14s
  synthetic copied-stub contract               0.05s
```

One explicit materialization probe was run against the real Damocles section 2
event after the seam change:

```text
materialize_recognized_unpacker_event(section 2)
  status: ok
  size: 489929
  sha256: 34389204110c8bc4972eb3f0a7f8d1b73779fde10f1a5e48eb36b7c8068ea65a
```

That probe proves the product path still works. The remaining cleanup opportunity
is to replace this real-sized materialization proof with a small valid copied-
stub fixture or a direct C unit seam, so copied-stub native materialization can
be regression-tested without paying the full Damocles output size.

### Pandora BK Wrapper

Current test:

```text
test_real_dll_pandora_bk_provider_wrapper_promotes_absolute_payload
  analyze 189000-byte packed fixture
  assert provider, codec, source offsets
  assert decompressed size and sha256
  assert derived target suggestion
  assert load address, entrypoint, parent activity, payload role
```

Split:

```text
real corpus smoke
  assert one BK payload from ancient-cli at section 0 offset $E8
  assert suggestion is materializable at load/entry $20000

provider wrapper contract
  provider output packet -> provider_id, codec_id, packed/decompressed sizes

payload role contract
  initial control target in absolute payload -> primary_program

suggestion contract
  materializable event -> derived target suggestion fields

hash/materialization contract
  one fixture -> decompressed sha256
```

#### Slice 7 Implementation Checkpoint - Pandora Real Smoke Narrowed

The real Pandora BK wrapper test no longer asserts exact packed size,
decompressed size, or decompressed hash. A fast section-range decompression
contract now owns provider/codec/materialized-byte assertions:

```text
test_decompression_c_backend_pandora_bk_section_range_contract
  decompress section 0 offset $E8 size 189000
  provider_id ancient-cli
  codec_id bk
  decompressed size matches output file
  decompressed sha256 matches the known BK payload
```

The real wrapper test now keeps only the real corpus promotion proof:

```text
one derived target suggestion exists
one decompression event exists
one scanned packed payload exists
payload is provider-scanned ancient-cli/bk at section 0 offset $E8
payload reports decompressed_size from scan-json but no decompressed_sha256
suggestion/event are materializable
reason is provider_wrapper_validation_deferred
payload role is primary_program
parent target does not remain active
load/entry identity is $20000/$20000
```

Downstream materialized-child metadata is already covered by fake analysis and
fake decompressor import tests in `tests/test_import_adf.py`, where provider
identity, hashes, payload role, confidence, parent activity, and child origin
are asserted without the real Pandora packed fixture.

The missing lower seam is still the provider-wrapper C contract itself:

```text
provider output packet + absolute transfer proof
  -> provider_wrapper_validation_deferred during analysis
  -> parent_remains_active=false
  -> primary_program load/entry identity
```

The product path now avoids decompression during analysis for provider wrapper
cases where Ancient scan metadata plus static wrapper transfer gives enough
metadata to materialize a child target. Decompressed bytes and hashes are still
proved by the explicit section-range materialization contract and by import-time
materialization.

Ancient cannot be removed yet. Current imported targets and real tests still use
it for codecs that native Tetragon and simulated self-decrunch support do not
cover:

```text
targets/amiga_disk_pandora-1988-firebird/.../decompression.json
  method ancient-cli, codec bk

targets/amiga_disk_midwinter-ii---flames-of-freedom-.../.../decompression.json
  method ancient-cli, codec bk

test_real_dll_carrier_decompression_suggestions_require_runtime_metadata
  ancient-cli rnc1-old

test_real_dll_voodoo_trainer_decompression_comparator
  ancient-cli rnc1
```

Removing Ancient requires native or replacement support for at least `bk`,
`rnc1`, and `rnc1-old`, followed by target reimport/regeneration.

Focused verification:

```text
pytest tests\test_c_backend.py -m c_backend -k "pandora_bk" -q --durations=20
  2 passed, 222 deselected in 1.99s
  real wrapper promotion  1.03s
  section-range contract  0.16s

pytest tests\test_c_backend.py -m c_backend -k "pandora_bk or carrier_decompression_suggestions or voodoo_trainer_decompression_comparator" -q --durations=20
  3 passed, 1 skipped, 220 deselected in 2.38s
```

### Voodoo, Magicland, Conqueror Decrunchers

Current shape:

```text
analyze real fixture or disk-extracted file
find decrunch event
materialize event
assert event metadata
assert output size and sha256
```

Split:

```text
family smoke
  one real target per decrunch family proves the path is still detected

analysis contract
  small hunk/raw fixture -> event kind, load address, entrypoint, transfer offset

executor/materializer contract
  event id + fixture -> output bytes/hash

disk import contract
  Conqueror ADF -> CONQUEROR entry extraction
```

Conqueror is especially broad because it starts by extracting from disk, then
analyzes, then materializes. Those are three seams.

The focused decompressor profile shows that not every real decompressor test is
equally expensive:

```text
Voodoo Tetragon comparator                 1.03s
Conqueror native decrunch materialization  0.33s
```

Those are acceptable as retained family sentinels if their assertions stay
focused. Damocles is the one that needs a structural test seam because the
native copied-stub path is both expensive and currently unprofiled.

Later cleanup removed
`test_real_dll_magicland_self_decrunch_materialization`. Its large-output
materialization path duplicated the compact self-decrunch materializer contract
plus the cheaper Conqueror real simulator sentinel. The project-wide round-trip
report continues to cover the imported Magicland self-decrunched child as an
exact rendered target.

#### Magicland Loader Transfer Checkpoint

`test_real_dll_magicland_records_loader_file_transfers_without_unproven_asset_materialization`
was doing two analyses of the same Magicland target:

```text
analyze_project_source_with_c_backend(...)
_facts_v2_listing_analysis_for_project(...)
```

Both exposed the same recovered target-loader file-transfer facts. The test now
uses the combined listing analysis only:

```text
combined analysis
  -> no loader-owned decompression events
  -> no target-loader decompression events
  -> 14 recovered target_loader_file media transfers
  -> TUNE00 and MAP destination/offset sentinels
```

Measured result:

```text
pytest tests\test_c_backend.py -m real_integration -k "magicland_records_loader_file_transfers" -q --durations=10
  1 passed, 223 deselected in 2.46s
  slowest call: 1.57s
```

### Bloodwych Runtime And Tables

Current test:

```text
test_real_dll_bloodwych_detects_runtime_copy_loader_and_table_rows
  analyze project and build listing rows
  assert decode health counters
  assert runtime copied stage is code at $400
  assert bitmap pointer runtime refs
  assert indirect sites become jump tables
  assert code start refs
  assert scalar table descriptor and entries
  assert pointer table descriptor, entries, references
  assert rendered row text, byte spans, offsets
```

Split:

```text
real Bloodwych smoke
  no source refusal
  no required instruction failures
  copied stage at $400 has label + instruction row

runtime-copy analysis contract
  synthetic copy loop -> execution view/code range fact

bitmap reference contract
  synthetic copper list -> four bitmap runtime refs and data_class bitmap

jump table contract
  synthetic indexed branch -> recovered_indirect_site + code_start_refs

scalar table contract
  indexed local scalar read -> accepted descriptor, entry count proof, numeric entries

pointer table contract
  pointer entries -> accepted target entries and data references

listing row contract
  table facts + bytes -> row text, start/end offsets, original bytes
```

This keeps Bloodwych as the real sentinel while moving each analyzer rule to a
small fixture.

#### Bloodwych Pre-Research

The current Bloodwych test is a representative broad real-corpus test. One call
to `_facts_v2_listing_analysis_for_project("amiga_hunk_bloodwych")` is used to
prove all of these unrelated rules:

```text
analysis health counters
runtime-copied code promotion
bitmap runtime references
indirect jump-table recovery
code-start refs from jump tables
scalar table structural bounds
pointer table entry and reference recovery
listing row text, byte spans, and original bytes
```

That is exactly the shape the cleanup should eliminate. The retained Bloodwych
target proof should not be a second full-listing checklist. The exact source
round-trip sentinel already renders Bloodwych, proves the copied stage at
`$400`, checks representative table/source snippets, assembles the result, and
compares rebuilt hunk bytes. The broad listing checklist can therefore be
removed rather than narrowed into another duplicate real-target pass.

```text
facts_v2 source is not refused
required instruction failures stay at zero
copied stage at $400 renders as code
full source assembles and section bytes match
```

The detailed rules are covered by small or lower-level fixtures where they
already exist, and missing seams should be added there rather than recreated in
the real Bloodwych test. That gives failures a clear owner:

```text
synthetic indexed branch fixture fails
  -> jump-table recovery is broken

synthetic scalar table fixture fails
  -> table bound proof is broken

project-wide rendered source report fails on Bloodwych
  -> target-specific round-trip integration regressed
```

Implementation checkpoint:

```text
removed:
  test_real_dll_bloodwych_detects_runtime_copy_loader_and_table_rows

retained Bloodwych proof:
  project-wide rendered source round-trip report

existing compact coverage:
  runtime ORG/storage alias tests
  copied runtime stub tracing tests
  indexed dispatch/pointer-table round-trip tests
  copper list and bitmap runtime-ref row projection tests
```

### Data Class Navigation And Candidate Generation

Current test:

```text
test_real_dll_render_plan_data_classes_reach_listing_rows_navigation_and_candidates
  loop Bloodwych, GenAm, MonAm
  build listing rows for each
  assert data class row validity
  assert minimum class counts
  assert navigation typed-data entries
  build GenAm rows with locators
  call reversing_loop._listing_data_symbol_candidates
  assert candidate action/verifier shape
```

Split:

```text
real data-class smoke
  one assert per target that expected data classes survive into listing rows

listing row invariant contract
  rows with data_class -> kind=data, no label-only data rows

navigation contract
  rows -> typed-data group entries, no duplicate keys

candidate generation contract
  small rows with locators -> data_symbol.rename candidates and verifier shape
```

The candidate-generation portion does not need three real project analyses.

The same problem appears in the string/table evidence tests. For example,
`test_real_dll_025_string_text_examples_render_from_evidence` rendered
Starglider, Pandora, MonAm, Magicland, and Conqueror in one test. That was five
real source renders to prove selected string rendering examples.

Split it into:

```text
renderer contract
  bytes + evidence facts -> dc.b string text and terminator handling

classification contract
  real or synthetic facts -> only evidence-backed spans become strings

real corpus sentinels
  one short example per target family, each with a clear test name
```

Implementation checkpoint:

```text
test_real_dll_025_string_text_examples_render_from_evidence
  removed from the real integration suite
  no longer pays full Starglider source rendering for source-quality text checks

removed from this Python real corpus test:
  Starglider rank strings and false-positive exclusions
  Pandora credits examples
  MonAm diagnostic strings
  Magicland title/copyright examples
  Conqueror cracktro strings
```

The Starglider checks were not round-trip duplicates. Rendering bytes as
`dc.b $41,$43,...` and rendering them as `dc.b "ACE PILOT",$00` both assemble
to the same payload, so a project round-trip report cannot catch that
source-quality regression. The replacement therefore moved the exact examples
to compact C fixtures:

```text
facts_v2_rank_string_sequence_renders_starglider_examples
  small data section renders "ACE PILOT" and "COMMANDER" from string-sequence evidence

facts_v2_unlabeled_code_section_orphan_shape_does_not_auto_classify_string
  small code-shaped byte run rejects the Starglider "NuNu" and "NuD0" false positives
```

The remaining real Starglider tests now guard target-specific control-flow,
slot-width, and linkage behavior. Generic text classification belongs at the C
analysis/rendering seam where the rule is cheap and explicit.

`test_real_dll_026_table_descriptors_use_evidence_bounds_not_caps` has the same
shape for runtime views, table descriptors, table entries, source rendering,
and false-positive exclusions. It should be split by rule before trying to
optimise the implementation.

Implementation checkpoint:

```text
test_real_dll_026_table_descriptors_use_evidence_bounds_not_caps
  removed from the real integration suite
  no longer pays full Pandora child analysis for duplicated table mechanics

remaining work:
  keep Pandora child source exactness in rendered-source roundtrip
  keep provider/materialization coverage in the Pandora BK wrapper tests
  keep table entry/reference export details in C/source-analysis contract tests
```

The behavior is already covered at smaller seams:

```text
src/test_m68k_ir.c
  facts_v2_pc_word_dispatch_descriptor_promotes_targets_beyond_inline_set
    auto table descriptor end offset follows structural evidence, not a cap

  facts_v2_address_indexed_word_load_uses_signed_table_displacement
    indexed word dispatch promotes bounded relative targets

  facts_v2_word_offset_table_targets_promote_strings
    word-offset string tables produce string rows and relative lookup entries

  source_analysis_table_descriptor_exports_consumer_fact
    table descriptor JSON exports consumer offsets, structural proof, and
    table kind without a real target

  source_analysis_table_descriptor_exports_loop_limit_proof
    consumer_structural_scan and consumer_structural_stop survive JSON export

  source_analysis_table_entry_exports_status
  source_analysis_data_reference_exports_table_entry
    table entries and references are exported independently of Pandora

  facts_v2_policy_runtime_entrypoint_maps_absolute_load
  listing_navigation_reports_runtime_views
    runtime view records and entry reasons are exported from compact inputs
```

That is a cleaner boundary than keeping one real Pandora child test as the only
visible failure for table caps, runtime views, entry/reference export, and
false-positive exclusions.

#### Data-Class Candidate Pre-Research

The candidate-generation lower seam already exists:

```text
tests/test_reversing_loop.py
  test_listing_data_symbol_candidates_use_runtime_ref_identity
  test_listing_data_symbol_candidates_use_data_class_row_identity
  test_listing_data_symbol_candidates_use_rename_existing_for_named_rows
  test_listing_data_symbol_candidates_skip_existing_manual_name
  test_listing_data_symbol_candidates_skip_conflicting_existing_data_ref_name
  ...
```

Those tests directly feed synthetic rows to:

```python
reversing_loop._listing_data_symbol_candidates([row])
```

That means the real GenAm loop in the original
`test_real_dll_render_plan_data_classes_reach_listing_rows_navigation_and_candidates`
did not need to prove candidate command shape. The real test should narrow to:

```text
real data-class sentinel
  expected data_class rows exist for Bloodwych / GenAm / MonAm
  no data_class is attached to instruction or label-only rows

real navigation sentinel
  Bloodwych and GenAm data_class rows reach typed-data navigation once

synthetic candidate contract
  existing tests/test_reversing_loop.py row packets prove candidate identity,
  action kind, verifier kind, existing-name skip, and conflict skip behavior
```

This is another example where the overreach is not just runtime. It is a
diagnostic problem: a candidate-generation regression should fail in
`test_reversing_loop.py`, not after analyzing GenAm.

Implementation checkpoint:

```text
test_real_dll_render_plan_data_classes_reach_listing_rows
  narrowed to real data_class row survival sentinels
  no longer calls reversing_loop._listing_data_symbol_candidates()
  no longer generates typed-data navigation for a real target
  uses one MonAm row-window listing payload because it carries lookup_table,
  pointer_table, and string data_class rows

tests/test_reversing_loop.py
  retains direct synthetic data-symbol candidate coverage

src/test_m68k_ir.c
  retains direct C coverage for listing_navigation_uses_render_plan_data_class
```

Measured result:

```text
pytest tests\test_c_backend.py -m real_integration -k "data_classes_reach_listing_rows" -q --durations=10
  1 passed, 223 deselected in 1.69s
  slowest call: 0.81s

pytest tests\test_reversing_loop.py -k "listing_data_symbol_candidates_use_data_class_row_identity or listing_data_symbol_candidates_use_runtime_ref_identity" -q
  2 passed, 434 deselected in 0.33s
```

This pass improves ownership of failures but does not materially reduce the real
sentinel cost. The next runtime reduction is to split the three real target
analyses into one target per sentinel or to add synthetic row/navigation
contracts for the navigation projection itself.

### GenAm Agent Loop Sentinels

The real agent tests had the same shape as the earlier route-command tests:
they used a full real target loop to force individual planner/candidate cases.

Current broad shape:

```text
test_agent_real_genam_autonomous_rsset_candidate_converges_semantic_state
test_agent_real_genam_autonomous_lvo_library_base_candidate_converges
test_agent_real_genam_autonomous_data_symbol_candidate_is_not_generic_progress

each:
  copy targets/amiga_hunk_genam
  copy bin/GenAm
  build real listing/projection
  monkeypatch competing candidate families away
  run one clean-run iteration
```

The lower seams already own the detailed behavior:

```text
tests/test_reversing_loop.py
  _listing_library_base_candidates()
  _listing_rsset_region_candidates()
  data symbol class/address planner skip
  run_one library-base verifier
  rsset semantic reload verifier
```

The real layer now keeps one GenAm end-to-end sentinel:

```text
test_agent_real_genam_autonomous_rsset_candidate_converges_semantic_state
  real GenAm listing/projection
  clean-run agent loop
  target.rsset_region.add command
  semantic reload verification
```

The LVO and data-symbol real loops were removed because they duplicated direct
candidate and verifier contracts while paying the same real target setup.
The retained RSSET loop was narrowed again: the final explicit full source
render was removed and the test was renamed to
`test_agent_real_genam_autonomous_rsset_candidate_converges_semantic_state`.
Rendered RSSET source and exact rebuild are already owned by
`test_real_dll_manual_rsset_layout_region_renders_source_and_rebuilds` plus
the focused RSSET metadata render tests in `tests/test_c_backend.py`.

Measured result:

```text
pytest tests\test_agent_reversing_loop.py -m real_integration -q --durations=10
  before narrowing: 1 passed, 2 deselected in 3.74s
    slowest call: 3.48s
  after narrowing and rename: 1 passed, 2 deselected in 2.72s
    slowest call: 2.45s

pytest tests\test_c_backend.py -m c_backend -k "rsset_layout_region" -q --durations=10
  2 passed, 221 deselected in 0.26s
```

### Bloodwych Generated Source Exactness

Original test:

```text
test_real_dll_bloodwych_generated_source_assembles_exact
  render full Bloodwych source
  assemble full source
  assert dozens of source snippets
  compare rebuilt hunk section bytes
  assert no instruction byte mismatches
```

Split:

```text
project round-trip report
  Bloodwych content is exact
  known container shape mismatch is reported explicitly

render contracts
  small render fixtures for:
    lookup table line splitting
    RSSET/include/EQU placement
    ORG/runtime label placement
    hardware register naming
    bitmap EQU naming
    copper list rendering
    vector naming
    absolute word call rendering

analysis contracts
  source facts that feed audio, display, disk buffer, bitmap, and table comments
```

The full rebuild should not also be the only test for every renderer string.

Implementation checkpoint:

```text
removed test_real_dll_bloodwych_generated_source_assembles_exact
```

The detailed cases are covered by lower seams that already use small inputs:

```text
test_project_source_facts_v2_biased_absolute_long_dispatch_table_roundtrips
  pointer-table rendering from a compact hunk

test_project_source_facts_v2_pc_indexed_absolute_long_dispatch_table_roundtrips
  lookup-table rendering from a compact hunk

test_real_dll_facts_v2_listing_rows_auto_classifies_copper_list_from_cop_pointer
  copper/display row classification from a small raw packet

test_labelized_table_shape_features_and_xrefs
  target-usage feature extraction from selected listing rows
```

The full-target round-trip invariant is owned by the project-wide rendered
source report that is required for output-affecting commits. In the current
report, `amiga_hunk_bloodwych` is content-exact with `diff_range_count: 0` and
only `container_shape_mismatch`, which is the same ground the test's section
hex comparison covered. Keeping the per-target real test made the real suite
pay another full Bloodwych render/assemble while proving less than the report.

### Slice 4 - Collapse Drift Tests To One Real Pass Per Generator

For each generator:

```text
synthetic parser tests
  prove extraction rules

one committed drift test
  proves generated files match current extraction
```

Avoid this:

```text
extract full baseline metadata
  -> assert Rect
extract full baseline metadata
  -> assert EventRecord
extract full baseline metadata
  -> assert trap calls
extract full baseline metadata
  -> assert generated files
```

Prefer:

```text
small text fixture -> parser rule assertions
full baseline once -> generated output drift assertion
```

### Slice 4 Implementation Checkpoint - Generated/Drift Split

The first implementation pass removed the blanket `codegen_drift` treatment for
the whole M68K coverage and Mac OS runtime generation files.

The selected split is now test-name based:

```python
_CODEGEN_DRIFT_TEST_NAMES = {
    "test_diagnostic_inventory_loads_current_generated_form_tables",
    "test_canonical_inventory_summarizes_current_generated_data",
    "test_diagnostic_check_command_succeeds_with_current_classified_data",
    "test_canonical_check_command_prints_canonical_summaries",
    "test_bootstrap_unsupported_inventory_classifies_current_families",
    "test_generated_mac_os_runtime_metadata_is_current",
}
```

That keeps current generated artifact checks opt-in while returning cheap
synthetic tests to the default loop:

```text
pytest tests\test_m68k_coverage.py tests\test_macos_runtime_generation.py -q
  18 passed, 6 deselected in 0.12s

pytest tests\test_m68k_coverage.py tests\test_macos_runtime_generation.py -m codegen_drift -q
  6 passed, 18 deselected in 3.89s
```

The Mac parser checks no longer call `extract_baseline_metadata()` for parser
rules. They call the same parser functions on small text fixtures:

```python
rect = generator.parse_record(
    [
        "Rect RECORD 0",
        "topLeft ds Point ; offset: $0000 (0)",
        "bottom ds.w 1 ; offset: $0004 (4)",
        "right ds.w 1 ; offset: $0006 (6)",
        "sizeof EQU * ; size: $0008 (8)",
        " ENDR",
    ],
    "Rect",
    "fixture/MacTypes.a",
    {"Point": 4},
)
```

The remaining drift checks are still broader than ideal. In particular, the
M68K coverage CLI report tests now use injected synthetic inventories, so they
prove command dispatch and output formatting without loading current generated
forms:

```python
monkeypatch.setattr(
    m68k_coverage,
    "build_diagnostic_inventory",
    _synthetic_diagnostic_inventory,
)
assert m68k_coverage.main(["report", "--phase", "diagnostic"]) == 0
```

The remaining current-generated M68K checks are intentional drift sentinels:

```text
diagnostic inventory loads current generated form tables
canonical inventory summarizes current generated data
diagnostic check succeeds with current classified data
canonical check succeeds with current classified data
bootstrap unsupported inventory classifies current families
```

### Slice 4B - Collapse Duplicate C Backend Comparator Passes

The non-real C backend layer still had project-scale comparator tests that ran
the same GenAm and MonAm analyses more than once:

```text
indexed pointer table comparator test
  build listing rows for GenAm
  render source for GenAm
  build listing rows for MonAm
  render source for MonAm

wide word dispatch comparator test
  render source for GenAm again
  render source for MonAm again
```

Those were not separate seams. They were the same health assertions over the
same target render path:

```text
asm_source_refused false
required instruction failures zero
unsupported instruction demotes zero
interior conflicts unresolved zero
unresolved labels zero
no bogus ORG $4
```

The cleanup collapsed them into one source-render sentinel per target:

```text
test_project_source_facts_v2_indexed_pointer_table_comparators_stay_clean[GenAm]
test_project_source_facts_v2_indexed_pointer_table_comparators_stay_clean[MonAm]
```

Measured result:

```text
before:
  pytest tests\test_c_backend.py -m "c_backend and not real_integration" -q --durations=15
    93 passed, 131 deselected in 9.87s
    GenAm indexed comparator  1.72s
    MonAm indexed comparator  1.67s
    GenAm wide comparator     0.68s
    MonAm wide comparator     0.68s

after:
  pytest tests\test_c_backend.py -m "c_backend and not real_integration" -q --durations=15
    91 passed, 131 deselected in 6.11s
    MonAm comparator          0.70s
    GenAm comparator          0.65s
```

This is the preferred kind of cleanup: no cache, no parallelism, no weaker
assertion, just removing duplicate crossings of the same expensive seam.

### Slice 4C - Split Mixed Real Corpus Rebuilds Out Of Comparator Tests

The next C backend overreach was a single test name hiding three different
contracts:

```text
test_project_source_facts_v2_inline_tail_dispatch_voodoo_and_comparators_stay_clean

  Voodoo real target
    render source
    prove inline-tail dispatch labels and branches are sane

  GenAm real target
    direct rebuild source
    compare bytes against original

  MonAm real target
    direct rebuild source
    compare bytes against original
```

Those are all useful checks, but they are not one seam. The Voodoo check is an
inline-tail dispatch rendering sentinel. The GenAm and MonAm checks are direct
round-trip rebuild sentinels. Keeping the rebuilds inside the Voodoo test made
the slow test look like one problem and kept real corpus work inside the
non-real C backend layer.

The cleanup splits this into explicit real corpus tests:

```text
test_real_dll_voodoo_inline_tail_dispatch_stays_clean
  render Voodoo source
  assert inline-tail dispatch stays code, not byte junk

test_real_dll_genam_monam_direct_rebuild_stays_exact[GenAm]
test_real_dll_genam_monam_direct_rebuild_stays_exact[MonAm]
  direct rebuild source
  assert rebuild is accepted
  assert rebuilt bytes equal original bytes
```

Focused verification:

```text
pytest tests\test_c_backend.py -m real_integration -k "voodoo_inline_tail_dispatch or genam_monam_direct_rebuild" -q --durations=10
  3 passed, 221 deselected in 2.15s
  MonAm direct rebuild  0.58s
  GenAm direct rebuild  0.49s
  Voodoo inline-tail    0.18s

pytest tests\test_c_backend.py -m "c_backend and not real_integration" -k "inline_tail_dispatch or genam_monam_direct_rebuild" -q --durations=10
  224 deselected in 0.19s
```

### Slice 4C.1 - Stop Re-Rendering Already Rendered Manual-Edit Sources

Several manual-edit tests had this shape:

```python
rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path)
rebuilt, _source_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
    source,
    metadata_path=metadata_path,
    compare_original=True,
)

assert "...expected rendered edit..." in rendered
assert rebuilt == original
assert direct_profile["direct_rebuild_exact"] is True
```

That asks the C backend to render the same source twice. The direct rebuild API
is still important, and it remains covered by explicit direct-rebuild tests.
For tests whose main assertion is the rendered manual-edit output, the cheaper
contract is:

```python
rendered = render_project_source_with_c_backend(source, metadata_path=metadata_path)
rebuilt = _assemble_rendered_amiga_hunk_source(rendered)

assert "...expected rendered edit..." in rendered
assert rebuilt == original
```

This keeps the round-trip proof for the exact rendered text under test, but it
does not also retest the direct-rebuild orchestration path. The first cleanup
pass applied this to the GenAm ASCII-hex table layout hotspot and adjacent
manual data-symbol/A5 decision tests.

### Slice 4C.2 - Split GenAm Source Render From Listing Projection

`test_real_dll_renders_genam` was also doing two jobs:

```text
render bin/GenAm as source
  assert source contains app-slot symbols and does not misname $0098(a1)

build amiga_hunk_genam listing rows
  assert hundreds of app-slot row references exist
  assert representative read/write access rows are projected
```

The listing-row behavior is covered by C listing contracts and the separate
GenAm app-slot profile sentinel. Keeping it in the source-render smoke made one
test pay for both source rendering and listing artifact construction. The
retained real source-render smoke now checks only source-render regressions:

```text
SECTION and instruction text exists
app_0234 RS definition and app_0234(a6) source use survive
$0098(a1) is not misclassified as m68k_vector_trap_6_instruction_vector(a1)
```

### Slice 4C.3 - Replace Runtime Immediate Real Renders With A Rule Fixture

`test_real_dll_runtime_memory_immediates_need_proven_external_role` rendered
both GenAm and MonAm only to assert this negative:

```python
assert "#bitmap_" not in rendered
assert "#disk_buffer_" not in rendered
```

That is a source-quality check, so the project round-trip report cannot replace
it. But it is not a GenAm/MonAm-specific rule. The rule is:

```text
ordinary immediate values stay numeric
bitmap_*/disk_buffer_* names require proven hardware/storage sink semantics
```

The replacement is a compact C render fixture:

```text
facts_v2_runtime_memory_immediate_requires_sink_role
  move.l #$10000,d0
  move.l #$67D00,d1
  assert no bitmap_ or disk_buffer_ symbol appears
  assert the immediates render numerically
```

Positive bitmap and disk-buffer naming remains covered by the hardware/storage
sink C fixtures. The expensive real binary pair no longer owns this generic
negative rule.

### Slice 4D - Narrow MonAm Callback Field Real Sentinel

The MonAm callback-field test was paying two target-scale C crossings:

```text
listing_artifact_source_text_with_c_backend_profile(...)
_facts_v2_listing_analysis_for_project("amiga_hunk_monam302")
```

The direct C unit layer already owns the precise callback-field facts:

```text
facts_v2_callback_field_store_promotes_indirect_call_target
facts_v2_callback_field_target_inherits_call_site_trace_state
```

The retained real MonAm sentinel now proves that the callback target reaches the
rendered source as code rather than remaining raw branch bytes:

```text
movea.l $003E(a3),a0
jsr $0000(a0)
loc_0_00005F32:
  bra.w loc_0_00005F44
```

Focused verification:

```text
pytest tests\test_c_backend.py -m real_integration -k "monam_callback_field_targets" -q --durations=10
  1 passed, 223 deselected in 1.51s
  slowest call: 0.68s
```

### Slice 4E - Narrow Platform Call Unresolved-Site Sentinel

`test_real_dll_platform_calls_are_not_unresolved_indirect_sites` looped GenAm
and MonAm:

```text
GenAm
  recovered platform calls: 128
  unresolved indirect sites: 6

MonAm
  recovered platform calls: 278
  unresolved indirect sites: 0
```

GenAm was originally retained because it had both sides of the invariant, but
the retained test was still a broad disjointness sweep over a real analysis.
The lower C layer owns the core rule that resolved platform calls are not
reported as unresolved indirect sites, and the real OpenLibrary follow-up tests
already assert target-specific platform calls are absent from unresolved-site
sets.

Later cleanup removed
`test_real_dll_platform_calls_are_not_unresolved_indirect_sites` entirely.

The same reasoning applies to
`test_real_dll_monam_openlibrary_app_slot_resolves_dos_calls`. It paid a full
MonAm analysis to prove the opened DOS base can be stored and later used for
LVO call resolution. The compact C fixture already covers that path with
`_LVOOldOpenLibrary`, `h1dl_DOSBase`, follow-up `_LVOOutput`, and zero
unresolved indirect sites. The remaining real OpenLibrary tests keep cheaper
corpus coverage for D0-to-A6 and cross-section library-name variants.

Focused verification:

```text
pytest tests\test_c_backend.py -m real_integration -q --durations=20
  114 passed, 15 skipped, 91 deselected in 36.87s
```

### Slice 4F - Narrow Immediate Text Token Real Sentinel

`test_real_dll_028_immediate_text_tokens_are_instruction_operand_facts` ran the
same exported-token contract over MonAm and GenAm. The C unit layer already
proves immediate text tokens export source offset, operand index, width, value,
text, and JSON fields from a compact instruction fixture.

The real layer briefly kept one corpus sentinel:

```text
MonAm
  text: "DEV "
  source_offset: 186
  operand_index: 0
  width: 4
  value: $44455620
```

Later cleanup removed
`test_real_dll_028_immediate_text_tokens_are_instruction_operand_facts`
entirely. It did not protect a distinct target workflow; it re-ran a full MonAm
analysis to prove the same token-export contract already covered by
`source_analysis_immediate_text_token_exports_operand_fact`.

Focused verification:

```text
pytest tests\test_c_backend.py -m real_integration -q --durations=20
  113 passed, 15 skipped, 91 deselected in 37.37s
```

Updated non-real C backend layer:

```text
pytest tests\test_c_backend.py -m "c_backend and not real_integration" -q --durations=15
  90 passed, 134 deselected in 4.88s
```

This did not remove round-trip coverage. It made the real corpus coverage
visible where it belongs and removed hidden real-target work from the default
C backend contract layer.

### Slice 5 - Packet Fixtures For Mac Real Images

Create a durable imported-packet fixture format:

```json
{
  "platform": "macos",
  "file": {"path": "MPW-GM/MPW/Tools/Asm"},
  "code_resources": [
    {"id": 0, "role": "jump_table_segment"},
    {"id": 1, "role": "code_segment", "code_entry_offset": 40}
  ]
}
```

Then:

```text
real image import test
  reads MPW-GM.img.bin once

projection tests
  read packet fixture only
```

This removes repeated external image/tool work from tests that are really
checking Python presentation behavior.

Measured current layer:

```text
pytest tests -m macos_real_fixture -q --durations=20
  11 passed, 1637 deselected in 7.21s

slowest:
  code1 main decodable by existing m68k listing backend      1.28s
  container payload lists HFS resources                      0.69s
  real Asm item recognized with fork roles                   0.67s
  web source payload exposes pivots                          0.66s
  web payload keeps source and observed binary facts apart   0.65s
  web container payload exposes unsupported state            0.65s
  code inventory matches committed drift metadata            0.64s
  code1 main preview and unsupported state                   0.64s
  container import writes child source descriptor            0.63s
```

This is not currently the biggest cost, but it is a clean example of a layer
boundary:

```text
real image/container smoke
  prove MPW-GM.img.bin can be read and the Asm resource summary still matches

packet projection tests
  prove web payloads, unsupported-state pivots, source descriptors, and
  container child metadata from a compact JSON packet

native code listing smoke
  keep one real CODE 1 listing/backend check
```

Pre-research shows that a naive packet fixture is too large:

```text
build_macos_project_payload(MPW-GM/MPW/Tools/Asm)
  serialized compact JSON size: 61,796,468 bytes
```

So the packet fixture must not be the full UI payload. It should be a compact
source packet containing only the stable inputs needed by projection tests:

```json
{
  "file": {"path": "MPW-GM/MPW/Tools/Asm", "type": "MPST", "creator": "MPS "},
  "resource_fork": {"code_resource_count": 28, "non_code_types": ["acur", "CURS", "cmdo", "vers"]},
  "code0": {"jump_table_entry_count": 346, "a5_world": {"below": 14624, "jump_table": 2768}},
  "code1": {"payload_size": 29024, "entry_offset": 40, "semantic_summary": {"instructions_min": 7000}},
  "resource_summaries": [
    {"id": 0, "role": "code0_metadata"},
    {"id": 1, "role": "selected_full_listing"},
    {"id": 27, "role": "semantic_listing", "incoming_code0_xrefs": true}
  ]
}
```

The real image smoke can be much smaller:

```text
read_macos_hfs_image_bytes(MPW-GM.img.bin)
  0.587s

inspect_macos_hfs_code_summary_with_c_backend(..., MPW-GM/MPW/Tools/Asm)
  0.027s

observed:
  file type MPST / creator MPS
  code_resources 28
  selected CODE 1 payload_size 29024
```

The broad current test should be split into:

```text
real image smoke
  image bytes -> C summary shape only

compact packet projection contracts
  packet -> source quality gate
  packet -> code resource navigation
  packet -> restored source presentation
  packet -> source export body comparison
```

#### Mac Payload Coverage Map

The current slow test is:

```text
test_macos_project_payload_reads_committed_mpw_fixture_when_available
  build_macos_project_payload(real MPW-GM image)
  assert all-resource CODE projection
  assert source quality gate
  assert generated xrefs and labels
  assert restored-source packets
  assert committed source export body matches fresh render
```

Other real Mac tests already cover the image/container/listing boundaries:

```text
test_real_asm_hfs_item_is_recognized_with_fork_roles
  real HFS file identity and fork roles

test_real_asm_code_inventory_matches_committed_drift_metadata
  real resource fork inventory and CODE 0/CODE 1 metadata

test_code1_main_has_code_byte_listing_preview_and_explicit_unsupported_state
  real selected CODE 1 layout and listing preview

test_code1_main_is_decodable_by_existing_m68k_listing_backend
  real CODE bytes enter the native Mac listing backend

test_macos_listing_artifact_uses_macos_source_and_row_provenance
  committed Mac target uses the Mac source descriptor and row provenance

test_committed_macos_asm_artifact_covers_every_code_resource
  committed source export covers all real CODE resources
```

The synthetic payload test already covers most Python projection mechanics:

```text
test_macos_project_payload_uses_c_summary_and_source_fixture_metadata
  fake C summary
  fake HFS resource extraction
  fake Mac listing backend
  parser fact coverage
  non-CODE resource placeholders
  CODE 0 jump-table rows
  selected CODE listing metadata
  semantic preview windows
  restored-source packet propagation
  native-source routing
```

That means the unique expensive coverage is the all-resource MPW semantic source
projection and the committed export comparison. The cleanup should not delete
that test until those two contracts have a replacement:

```text
all-resource source-quality packet contract
  compact packet -> quality gate, xrefs, labels, residuals, semantic rows

source export drift contract
  compact packet + real HFS bytes -> render_macos_example_asm_from_payload()
  equals committed source body
```

The source export comparison is especially important because it is the local
round-trip style gate for the committed Mac source artifact. It can move out of
the broad payload test, but it should remain a named drift/contract check.

#### Slice 5 Implementation Checkpoint - Compact Source Export Contract

The first Mac implementation pass added a compact source-export renderer
contract:

```text
test_macos_example_asm_renderer_accepts_compact_source_packet
  compact payload with CODE 0 and CODE 1 source_body_sections
  fake HFS CODE payload extraction
  render_macos_example_asm_from_payload()
  assert include lines, CODE 0 structured metadata, _LoadSeg entry, CODE 1 rows
```

Measured result:

```text
pytest tests\test_macos_target_artifact.py -k compact_source_packet -q
  1 passed, 10 deselected in 0.19s
```

This does not replace the committed MPW source export drift check yet. It
establishes the lower seam that the broad real payload test can move assertions
onto:

```text
current broad test
  real image -> full payload -> source export comparison

new lower seam
  compact packet -> source export renderer
```

The remaining work is to extract or build the compact all-resource packet that
carries source-quality rows, generated xrefs, labels, and residual summaries
without serializing the 61MB full UI payload.

Additional subtree measurements explain the size problem:

```text
full payload                         61,797,917 bytes
binary_container_view                61,787,129 bytes
code_resource_details                30,329,073 bytes
source_body_sections                 30,245,257 bytes
source_quality_gate                     395,436 bytes
code_segment_map                        390,474 bytes
navigation                              244,115 bytes
code_resources                          143,829 bytes
selected_code_segment                    14,908 bytes
resource_fork                             7,833 bytes
```

The duplicated large fields are the semantic row collections:

```text
CODE 1   section 6,423,132 bytes   semantic rows 9,943
CODE 5   section 4,211,904 bytes   semantic rows 6,632
CODE 3   section 2,251,948 bytes   semantic rows 3,610
CODE 6   section 2,075,675 bytes   semantic rows 3,203
CODE 21  section 1,471,595 bytes   semantic rows 2,282
CODE 12  section 1,438,785 bytes   semantic rows 2,258
```

So the compact all-resource packet should store summaries and sentinels, not
row bodies:

```json
{
  "kind": "macos_source_quality_packet_v1",
  "source_quality_gate": {
    "status": "byte_real_baseline",
    "semantic_closeout_status": "semantic_source_complete_for_known_bounds"
  },
  "resources": [
    {
      "id": 1,
      "status": "selected_full_listing",
      "instruction_row_count": 7000,
      "data_row_count_min": 1,
      "generated_xref_count_min": 1000,
      "generated_label_count_min": 100,
      "required_rows": [
        {"kind": "instruction", "payload_offset": 40, "text": "movea.l (a7)+,a0"},
        {"kind": "data", "payload_offset": 8248, "api_call": "UnloadSeg"}
      ],
      "forbidden_residual_starts": [62]
    }
  ]
}
```

A packet built like this keeps the behavior checks explicit while avoiding the
duplicated full semantic row payload. Tests then become:

```text
packet quality contract
  macos_source_quality_packet_v1 -> quality gate and per-resource sentinels

packet source export contract
  compact source_body_sections + fake/small CODE payload bytes -> renderer lines

real MPW smoke
  real image -> summary shape and one listing backend check
```

#### Slice 5B Implementation Checkpoint - Compact Source Quality Contract

The next Mac pass added a compact source-quality packet test:

```text
test_macos_source_quality_gate_accepts_compact_source_packet
  three CODE resources
  CODE 0 metadata/jump-table evidence
  CODE 1 semantic rows with a resolved control-target xref
  CODE 2 candidate code with explicit semantic gap residuals
  no real HFS image
  no full payload JSON
```

The packet proves the source-quality semantics that the full MPW payload test
was asserting through a large real fixture:

```text
source quality gate kind/status
semantic closeout status
semantic component statuses
explicit non-claims
all checklist entries true
recursive control-target xref accounting
resolved xref target labels
semantic decode gap residual accounting
reachable evidence recorded for candidate resources
```

Focused verification:

```text
pytest tests\test_macos_project_payload.py -k "compact_source_packet or source_quality_gate_accepts" -q --durations=10
  1 passed, 12 deselected in 0.25s
```

This creates the lower seam needed to trim the broad real MPW payload test. The
real test should keep proving that the actual image and C summary still feed the
payload builder, but detailed quality accounting should live in this compact
packet contract.

#### Slice 5C Implementation Checkpoint - MPW Real Smoke Narrowed

The next Mac pass moved two more assertion groups out of the full MPW image
test:

```text
test_macos_non_code_resource_placeholders_accept_compact_inventory
  compact resource type inventory
  CURS type-level semantics
  unsupported non-CODE placeholders
  unlinked placeholder source/reference context

test_macos_source_sections_accept_compact_restored_source_packet
  three compact CODE details
  source section id/status/envelope behavior
  selected CODE listing context
  CODE 0 generated routing xrefs
  incoming CODE 0 xrefs on target sections
```

The real MPW fixture test is now a smoke, not a packed checklist:

```text
test_c_macos_hfs_code_summary_matches_committed_mpw_asm_metadata
  real MPW-GM image
  real C HFS summary
  parser fact references validate
  finder identity
  28 CODE resources
  CODE 0 jump-table/A5 metadata
  selected CODE 1 bounds and far-model header
  segment-loader fixup inventory
  CODE resource extraction starts with the expected entry bytes
```

The former `test_macos_project_payload_reads_committed_mpw_fixture_when_available`
real-image payload build has been removed. It duplicated the real C summary
smoke above while also rebuilding the full UI payload and selected semantic
source. The payload-builder obligations now sit in compact tests:

```text
test_macos_project_payload_uses_c_summary_and_source_fixture_metadata
test_macos_source_quality_gate_accepts_compact_source_packet
test_macos_non_code_resource_placeholders_accept_compact_inventory
test_macos_source_sections_accept_compact_restored_source_packet
```

That gives one real image/import sentinel and keeps source-quality/source-section
failures at compact packet seams.

Focused verification:

```text
pytest tests\test_macos_project_payload.py -q --durations=15
  14 passed, 1 deselected in 0.30s

pytest tests\test_macos_project_payload.py -m real_integration -q --durations=10
  1 passed, 14 deselected in 9.23s
```

#### Planner Selection Implementation Checkpoint - Lower Seam

The next default-suite profile showed a new common pattern after corpus render
duplication had been removed:

```text
test_planner_selects_data_symbol_remove_candidate     0.59s
test_planner_selects_data_symbol_rename_candidate     0.32s
test_planner_skips_already_satisfied_*                0.19s-0.33s
test_planner_ranks_semantic_representation_*          0.29s
```

Those tests were not proving iteration execution. They created a temporary
target, monkeypatched `inspect_target()`, then called `run_one_iteration()` only
to observe pure planner ranking or skip decisions:

```text
run_one_iteration()
  start/resume run state
  inspect target
  select planner command
  check command catalog availability
  write iteration report
```

The behavior under test lives lower:

```text
_select_command_action(inspect_report)
  candidate command options
  skip already-satisfied candidates
  score and rank candidates
  record selected command/verifier in planner report
```

The cleanup therefore keeps full `run_one_iteration()` coverage for availability
drift, report writing, execution, and verifier behavior, but moves pure planner
selection examples to the planner seam:

```python
def _select_planner_action(*candidates: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    inspect_report = _inspect_with_locator()
    inspect_report["verification_paths"] = [{"kind": "round_trip", "available": True}]
    inspect_report["candidate_work"] = list(candidates)
    selected = reversing_loop._select_command_action(inspect_report)
    assert selected is not None
    return inspect_report, selected
```

That changes tests such as data-symbol rename from:

```text
tmp target -> monkeypatch inspect_target -> run_one_iteration -> assert selected command
```

to:

```text
inspect_report packet -> _select_command_action -> assert selected command/planner fields
```

Focused verification:

```text
pytest tests\test_reversing_loop.py -q --durations=20
  436 passed in 2.95s

pytest tests -q --durations=30
  1242 passed, 396 deselected in 14.46s
```

This is the same cleanup principle as the corpus work: use the full workflow
only when the assertion needs the full workflow. Ranking/skip rules belong at
the planner seam.

#### API Durability Matrix Implementation Checkpoint - Real Boundaries Only

The non-real integration profile then exposed another overreach:

```text
test_api_harness_runs_manual_mutation_durability_matrix  2.18s
```

The matrix named six durability boundaries, but four of them did not change
server state in this harness:

```text
immediate                         real server snapshot
browser_refresh_equivalent        no browser is running here
target_reopen                     no target close/reopen transition is simulated
server_restart                    reseeds listing projection
new_context_storage_clear         no browser storage is running here
project_cache_clear               reseeds listing projection
```

Repeating the same route snapshot for browser-only boundaries made the test
look broader than its evidence. The corrected shape keeps the server-visible
boundaries as passed checks and records the browser-only boundaries as explicit
transient entries:

```python
DurabilityBoundary(
    "browser_refresh_equivalent",
    required=False,
    transient_reason="browser refresh is a CDP boundary, not a server route transition",
)
```

The result assertion now documents the coverage honestly:

```text
passed:
  immediate
  server_restart
  project_cache_clear

transient:
  browser_refresh_equivalent
  target_reopen
  new_context_storage_clear
```

Focused verification:

```text
pytest tests\test_api_workflow_harness.py -m integration -q --durations=10
  5 passed in 1.70s
  matrix call time 1.00s
```

This is not moving coverage out of the suite. It removes three repeated server
snapshots that never simulated the named boundary and leaves the real browser
durability claim to the CDP layer.

## Expected End State

The target shape is:

```text
pytest tests
  < 20s
  pure unit/default developer loop

pytest tests -m integration
  wider confidence signal
  still serial, still transparent

pytest tests -m c_backend
  C boundary contracts and selected corpus smoke

pytest tests -m route_integration
  route envelope and server wiring smoke

pytest tests -m codegen_drift
  committed generated artifact freshness

pytest tests -m macos_real_fixture
  real image/tool import smoke

pytest tests\test_web_e2e_cdp.py
  browser/CDP layer
```

The integration layer should get faster because broad tests are moved to the
right seam, not because they are hidden, cached, or parallelized.

## Non-Goals

This proposal does not recommend:

```text
pytest-xdist as the solution
automatic caches to hide repeated work
removing real corpus coverage
weakening round-trip/reassembly gates
turning every slow test into a skip
```

Real target tests remain important. They should be fewer, clearer, and aimed at
real-world regression sentinels rather than carrying all behavioral coverage.

## Verification

Each cleanup slice should report:

```text
before:
  command
  test count
  wall time
  slowest tests

after:
  command
  test count
  wall time
  slowest tests
  coverage moved to synthetic/contract tests
  real corpus sentinel retained
```

For example:

```text
before:
  pytest tests -m route_integration
  133 tests, 24s

after:
  pytest tests -m route_integration
  smaller route-smoke layer

  pytest tests -m "not integration"
  still < 20s

  command catalog unit tests
  now cover command/action combinations without route setup
```

The cleanup is successful only when both statements are true:

```text
developer loop is fast
wide confidence layers remain meaningful and easier to understand
```

## Current Verification Snapshot

After the generated/drift split, route-command split, CDP race fixes, MPW
fixture narrowing, duplicate MPW payload removal, the Bloodwych/string real
fixture cleanup, Damocles copied-stub native execution deferral, Pandora
provider-wrapper validation deferral, GenAm agent RSSET sentinel narrowing,
Bloodwych exact-test removal, Magicland materialization-test removal,
platform unresolved-sweep removal, immediate-text real sentinel removal, and
MonAm OpenLibrary app-slot pass removal, planner-selection lower-seam cleanup,
and API durability matrix narrowing:

```text
pytest tests -q --durations=20
  1242 passed, 399 deselected in 19.79s

pytest tests -m integration -q
  202 passed, 1446 deselected in 30.07s

pytest tests -m real_integration -q --durations=20
  123 passed, 16 skipped, 1502 deselected in 47.84s

uv run ruff check
  passed

uv run mypy
  passed

M68K_RUN_BRAVE_CDP=1 pytest tests\test_web_e2e_cdp.py -q
  57 passed in 141.97s

pytest tests\test_web_app_source.py tests\test_ui_preferences.py tests\test_disasm_server.py -k "ui_preferences or preferences" -q
  6 passed, 199 deselected in 0.31s

pytest tests\test_macos_target_artifact.py -q --durations=10
  5 passed, 6 deselected in 0.32s

pytest tests -m macos_real_fixture -q --durations=10
  11 passed, 1637 deselected in 7.19s

pytest tests\test_macos_target_artifact.py -m real_integration -q --durations=10
  6 passed, 5 deselected in 3.38s

pytest tests\test_c_backend.py -m "c_backend and not real_integration" -q --durations=15
  90 passed, 134 deselected in 4.88s

pytest tests\test_macos_project_payload.py -k "compact_source_packet or source_quality_gate_accepts" -q --durations=10
  1 passed, 12 deselected in 0.25s

pytest tests\test_macos_project_payload.py -q --durations=15
  14 passed in 0.25s

pytest tests\test_macos_c_backend.py -m real_integration -k "committed_mpw_asm_metadata" -q --durations=10
  1 passed, 21 deselected in 1.35s

pytest tests\test_c_backend.py -m c_backend -k "tetragon" -q --durations=20
  4 passed, 220 deselected in 4.07s

pytest tests\test_import_adf.py -k "recognized_unpacker" -q --durations=10
  1 passed, 42 deselected in 0.27s

cmd /c src\test.bat --no-build
  C unit tests passed
  162 Python src unittest tests passed in 14.224s

pytest tests\test_c_backend.py -m real_integration -k "pandora_bk_provider_wrapper" -q --durations=10
  1 passed, 223 deselected in 1.19s

pytest tests\test_c_backend.py -m real_integration -q --durations=20
  112 passed, 15 skipped, 91 deselected in 36.92s

cmd /c src\precommit.bat
  passed
  m68k_ir: all 452 passed

pytest tests\test_c_backend.py -m real_integration -q --durations=20
  111 passed, 15 skipped, 91 deselected in 32.44s

pytest tests -q --durations=20
  1242 passed, 398 deselected in 21.41s

pytest tests\test_c_backend.py -m real_integration -k "genam_ascii_hex_table_data_block_layout or manual_data_symbol_rename_updates_rendered_seeded_entity or manual_data_symbol_remove_suppresses_rendered_seeded_entity or manual_data_symbol_rename_renders_ordinary_data_row or manual_data_symbol_rename_updates_rendered_use_site or accepted_a5_decision or nonaccepted_a5_decision or stale_a5_decision" -q --durations=12
  9 passed, 208 deselected in 1.74s

pytest tests\test_c_backend.py -m real_integration -q --durations=20
  111 passed, 15 skipped, 91 deselected in 29.84s

pytest tests\test_c_backend.py -m real_integration -k "renders_genam or genam_profile_exposes_c_app_slot_analysis" -q --durations=10
  2 passed, 215 deselected in 2.47s

pytest tests\test_c_backend.py -m real_integration -q --durations=20
  111 passed, 15 skipped, 91 deselected in 24.80s

cmd /c src\precommit.bat
  passed
  m68k_ir: all 453 passed

pytest tests\test_c_backend.py -m real_integration -q --durations=20
  109 passed, 15 skipped, 91 deselected in 27.04s

pytest tests -q --durations=20
  1242 passed, 396 deselected in 16.16s

pytest tests\test_reversing_loop.py -q --durations=20
  436 passed in 2.95s

pytest tests -q --durations=30
  1242 passed, 396 deselected in 14.46s

pytest tests -m real_integration -q --durations=20
  120 passed, 16 skipped, 1502 deselected in 38.01s

pytest tests -m "integration and not real_integration" -q --durations=20
  203 passed, 1435 deselected in 44.91s

pytest tests\test_api_workflow_harness.py -m integration -q --durations=10
  5 passed in 1.70s

pytest tests -m "integration and not real_integration" -q --durations=30
  203 passed, 1435 deselected in 32.48s

ruff check
  passed

mypy
  passed

python -m amiga_reversing.tools.rendered_source_roundtrip_report --update-rendered-source --json
  55 targets, 0 failures, 39 full-file exact, 15 content-exact only, 1 unsupported
  no rendered-source file changes

pytest tests\test_web_e2e_cdp.py -m web_e2e -q --durations=20
  57 passed in 162.39s

pytest tests\test_web_e2e_cdp.py -q --durations=20
  57 deselected in 0.23s
  note: default addopts exclude web_e2e, so the explicit web_e2e marker is required for CDP

pytest tests\test_c_backend.py -m real_integration -k "data_classes_reach_listing_rows or 026_table_descriptors" -q --durations=20
  1 passed, 222 deselected in 1.72s

pytest tests\test_active_imports.py -q --durations=10
  5 passed in 1.28s

pytest tests\test_reversing_loop.py -k "inspect_cli_reports_json or decision_journal_report_cli" -q --durations=10
  3 passed, 433 deselected in 1.42s

pytest tests\test_reversing_workspace.py -k "hygiene_cli or clean_run_cli" -q --durations=10
  2 passed, 11 deselected in 0.27s

ruff check
  passed

mypy
  passed

python -m amiga_reversing.tools.rendered_source_roundtrip_report --update-rendered-source --json
  55 targets, 0 failures, 39 full-file exact, 15 content-exact only, 1 unsupported
```

The default loop is back under 20s without parallelism. The integration layer is
still too broad and remains the main cleanup target.

The latest real-integration profile now has no separate Bloodwych runtime/table
listing pass, Damocles candidate analysis no longer pays native copied-stub
execution, Pandora provider-wrapper analysis no longer pays Ancient
decompression just to establish load/entry metadata, and duplicate Pandora table
descriptor coverage has moved to C/source-analysis contracts. The largest
remaining real fixture overreach is:

```text
Damocles deferred-analysis sentinel             2.83s
Magicland loader file transfers                 1.56s
GenAm LVO operand-part sentinel                 1.28s
Starglider app-slot width sentinel              1.19s
Magicland copied-runtime entry                  1.15s
Pandora BK provider wrapper                     1.11s
Voodoo Tetragon comparator                      0.99s
```

The non-real integration layer is now dominated by two deliberate drift-style
checks:

```text
test_generated_mac_os_runtime_metadata_is_current        8.45s
test_diagnostic_inventory_loads_current_generated_form_tables  3.30s
```

Those are not good candidates for assertion trimming. They are the one-real-
world extraction checks that remain after the parser/reporting tests were moved
to synthetic fixtures. The layer routing should keep `codegen_drift` visible as
its own opt-in gate rather than mixing it with developer-loop unit tests.

The Bloodwych generated-source exact test is no longer listed here because the
required full-project round-trip report already covers `amiga_hunk_bloodwych`
as content-exact with no byte diff ranges and an explicit container-shape
diagnostic.

## Trailing Notes And Follow-Up Observations

These observations came out of implementation but are not fully resolved by the
current cleanup slices.

### Real Corpus Cost Is Now Mostly Real Integration Breadth

Damocles used to show that assertion trimming was not enough: analysis itself
was running the full native copied-stub executor. That has been corrected by
deferring native execution to the materialization API. The real Damocles
candidate-analysis sentinel is now about 2.8s.

The remaining Damocles-specific gap is narrower:

```text
small copied-stub materialization fixture
  -> copied-stub native executor
  -> entry validation
  -> materialized bytes/hash

real Damocles corpus sentinel
  -> two Tetragon events exist
  -> expected load/entry ranges survive
  -> section 2 remains materializable with native_execution_deferred
```

The larger remaining real-suite costs are now full-source rebuild sentinels,
agent end-to-end sentinels, and native materialization sentinels.
Those need the same treatment: keep one real corpus sentinel, move detailed
behavior to compact contracts, and avoid making real targets carry every
assertion.

### Default Loop Headroom Is Real But Narrow

The default loop is under 20s in the clean timing run:

```text
pytest tests -q
  1242 passed, 399 deselected in 19.79s
```

The slowest remaining default tests are not the converted route command tests.
They are mostly import-bound or CLI-style tests:

```text
active runtime import boundary
reversing-loop planner/report CLI checks
reversing workspace hygiene/clean CLI checks
reproduction stamp policy check
```

One cleanup pass consolidated the active source import scans:

```text
before:
  separate tests scanned overlapping Python source trees for:
    kb parser imports
    runtime platform CLI references
    runtime import roots
    c_backend subprocess/CLI references

after:
  test_active_source_import_boundaries_are_current
    one source walk
    one text read per file
    AST parse only for runtime roots
    separate offender lists for each boundary

pytest tests\test_active_imports.py -q --durations=10
  5 passed in 1.28s
```

The remaining source-boundary test still costs about 0.72s because it parses the
runtime source tree. That cost is acceptable for now, but if the default loop
drifts again the next cleanup should examine whether the policy can be checked
from a generated import inventory rather than re-parsing every file during the
developer loop.

### CLI Tests Should Not All Start A New Interpreter

The default loop still had several CLI-style tests that each paid `python -m`
startup:

```text
decision-journal-report dry-run JSON
decision-journal-report projection JSON
hygiene JSON
clean-run JSON
inspect JSON
```

The useful contracts are not identical:

```text
module wiring smoke
  python -m amiga_reversing.reversing_loop ... emits JSON

argparse/command JSON contracts
  reversing_loop.main(argv) emits the same JSON shape
  command remains no-write or deletes the expected files
```

The cleanup keeps the `inspect` subprocess test as the module-entry smoke and
moves the other command JSON checks to direct `main()` calls with captured
stdout:

```text
test_inspect_cli_reports_json
  subprocess smoke remains

test_decision_journal_report_cli_reports_json_and_dry_run_without_writing
test_decision_journal_report_cli_includes_projection_without_mutating
test_hygiene_cli_reports_json
test_clean_run_cli_reports_json
  direct reversing_loop.main(argv)
```

Focused verification:

```text
pytest tests\test_reversing_loop.py -k "inspect_cli_reports_json or decision_journal_report_cli" -q --durations=10
  3 passed, 433 deselected in 1.42s

pytest tests\test_reversing_workspace.py -k "hygiene_cli or clean_run_cli" -q --durations=10
  2 passed, 11 deselected in 0.27s
```

The default loop improved without hiding work:

```text
pytest tests -q --durations=20
  1240 passed, 408 deselected in 15.01s
```

### Route Layer Still Has Legitimate Route Tests

Remaining route command tests now mostly cover:

```text
comment.edit route envelope and workflow profile
range locator/query behavior
data-block catalog evidence propagation
library-base/RSSET route contexts
data-symbol locator and projection behavior
public route error codes
```

These should not be blindly moved downward. Each remaining case needs the same
question applied:

```text
Is this testing route/locator/public envelope behavior?
Or is it testing command payload/application behavior?
```

Only the latter should move to direct command fixtures.

### CDP Exposed Two Real Browser Races

Running the explicit CDP layer after the marker split first failed in
`test_brave_cdp_manual_seed_waits_for_analysis_before_review_refresh`.

The failure was not caused by the test cleanup. It exposed a stale listing
request race:

```text
manual seed append
  -> listing cache invalidated
  -> new analysis job starts
  -> old listing request can fail with missing artifact
  -> stale failure still reaches the viewport
```

The fix is in `loadListingWindow()`: aborts still return normally, and
non-abort errors from stale request generations are ignored. Current-generation
listing errors still surface.

The second CDP run exposed a preference persistence race:

```text
browser saves ui_preferences.json
test observes file existence
file is temporarily empty during write_text()
json.loads("") fails
```

The fix is in `save_ui_preferences()`: write complete JSON to a unique temp
file in the target directory, then atomically replace `ui_preferences.json`.

Verification:

```text
pytest tests\test_web_e2e_cdp.py -m web_e2e -k "manual_seed_waits_for_analysis" -q
  1 passed, 56 deselected in 3.20s

pytest tests\test_web_e2e_cdp.py -m web_e2e -k "first_open_selects_source_entrypoint" -q
  1 passed, 56 deselected in 3.49s

M68K_RUN_BRAVE_CDP=1 pytest tests\test_web_e2e_cdp.py -m web_e2e -q
  57 passed in 142.50s

pytest tests\test_web_app_source.py tests\test_ui_preferences.py tests\test_disasm_server.py -k "ui_preferences or preferences" -q
  6 passed, 199 deselected in 0.31s
```

The lesson for the test cleanup is that moving tests to cleaner seams should
not make the browser layer optional. CDP remains valuable for async ordering and
filesystem visibility races that unit tests will not naturally catch.

### Target Render Checks Not Yet Exercised By This Slice

The required full target source refresh was run:

```text
python -m amiga_reversing.tools.rendered_source_roundtrip_report --update-rendered-source --json

summary:
  targets: 55
  failures: 0
  rendered_source_full_file_exact: 39
  rendered_source_content_exact_only: 15
  unsupported: 1
```

The refresh did not introduce target source diffs. It did confirm that the
newly important decompressed/raw targets are exact at the rendered-source
round-trip layer:

```text
Damocles native Tetragon payload 01  exact
Damocles native Tetragon payload 02  exact
Conqueror simulated decrunch child   exact
Midwinter II BK child                exact
Pandora BK child                     exact
Robin Hood bootloader stages         exact
Starglider 2 bootloader stage        exact
```

The audit also exposed a separate class of existing round-trip debt:

```text
content-exact but container-mismatched:
  Damocles menu/trio
  Magicland MD
  Mercenary III crystal
  Midwinter II hunk utilities and MWII
  Pandora main hunk
  Search for the King main hunk
  Starglider SG/SGLOAD
  Bloodwych
  MonAm

unsupported:
  Mac OS rendered-source assembly
```

Those are not caused by the test cleanup, but they matter. They mean source
text can rebuild to equivalent content while hunk container shape, relocation
grouping/order, or policy metadata still diverges. Future target work should
turn these into a named container-round-trip cleanup track instead of letting
them remain as anonymous "not full-file exact" cases.

### Full-Fixture Overreach Map

The remaining broadest tests are now explicit.

The former largest single overreach was:

```text
tests/test_macos_project_payload.py
  test_macos_project_payload_reads_committed_mpw_fixture_when_available
```

It reads the full MPW-GM image and then checks all of these at once:

```text
real HFS image import
Finder/resource fork identity
non-CODE resource placeholder semantics
all CODE resource source sections
CODE 0 jump-table routing xrefs
source-quality gate semantics
semantic residual accounting
selected CODE 1 listing details
restored-source packet shape
navigation/source export drift
committed .s body comparison
```

The corrected split is:

```text
real MPW smoke:
  full image -> finder identity, CODE count, selected CODE 1 sentinel,
  source-quality gate status, source-section coverage count

compact source-quality packet:
  synthetic sections -> residuals, recursive xrefs, label resolution,
  semantic closeout status

compact source-export packet:
  source_body_sections + small fake CODE bytes -> renderer contract

committed artifact drift:
  committed .s -> every real CODE resource is represented
```

That split has now happened. The real MPW payload build was removed, the C HFS
summary remains as the real import smoke, and the source-quality/source-section
behavior is covered by compact packet tests. The remaining broad synthetic
payload test is:

```text
tests/test_macos_project_payload.py
  test_macos_project_payload_uses_c_summary_and_source_fixture_metadata
```

Measured in isolation, it is not a performance offender:

```text
pytest tests\test_macos_project_payload.py::test_macos_project_payload_uses_c_summary_and_source_fixture_metadata -q --durations=10
  1 passed in 0.19s
  call time 0.04s
```

It is still a broad projection contract, so future cleanup may split it for
fault localization. It should not be treated as the next performance target.

Damocles was the clearest single overreach:

```text
tests/test_c_backend.py
  test_real_dll_damocles_tetragon_native_unpacking_candidates
```

It used one full Damocles fixture to prove too many contracts:

```text
Tetragon marker detection
native executor launch
copied decompressor transfer
entrypoint validation
payload role classification
materialized output hashes
profile timing fields
real-world two-payload regression
```

The current split is:

```text
small marker contract:
  synthetic hunk -> Tetragon event metadata

small copied-stub contract:
  synthetic hunk -> copied decompressor target promotion

small entry-validation contract:
  byte packet + entrypoint -> code-bearing payload accepted/rejected

native decompressor contract:
  currently verified by explicit real Damocles materialization probe
  future work: minimal real or extracted compressed stream -> materialized bytes/hash

real Damocles smoke:
  full fixture -> two Tetragon payloads exist
  section 2 -> materializable deferred native execution
```

Other full-file sentinels that should stay real but become narrower:

```text
Pandora BK wrapper:
  keep one absolute-payload smoke, move provider-wrapper metadata details down

Voodoo Tetragon:
  keep one comparator-family smoke, move postpass/comparator metadata to a
  compact contract

Magicland self-decrunch:
  removed the large-output materialization smoke; compact materializer tests,
  Conqueror real materialization, and the rendered-source round-trip report now
  own the relevant coverage
```

This is the next implementation frontier. The default loop is now fast enough;
the remaining value is making real corpus tests carry only real corpus proof.

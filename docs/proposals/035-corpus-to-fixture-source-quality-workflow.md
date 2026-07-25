# Proposal 035: Corpus-To-Fixture Source-Quality Workflow

Status: proposed.

Proposal 032 defines source-quality validation: when the framework emits
impossible or internally inconsistent analysis, that is a framework failure.
Proposal 034 defines the test-suite cleanup direction: nuanced framework
correctness should be proven by small fast fixtures, not only by large target
round-trips.

This proposal joins those two rules into one reversing workflow:

```text
corpus target exposes a failure class
  -> reduce it to a focused C fixture
  -> fix the fact producer or validator at cause
  -> rerender the corpus target to prove composition
  -> keep the corpus target as drift evidence, not the only test
```

## Tutorial: Why This Exists

Real targets are how we discover failure classes. Damocles, Starglider,
Pandora, Bloodwych, Midwinter II, Conqueror, and MacOS CODE resources have all
shown framework failures that would be hard to invent from first principles.

But large targets are poor primary tests for framework nuance:

```text
large target fixture
  -> many producers run
  -> many facts interact
  -> failure is slow
  -> cause is often unclear
```

The correct use of a corpus target is evidence:

```text
target says: this can happen in real input
fixture says: this rule is now defined and protected
target rerender says: the rule still composes in situ
```

The workflow is:

```text
observe
  -> reduce
  -> fixture
  -> repair
  -> rerender
  -> document
```

## Tutorial: Example Failure Class

False accepted code is the motivating example. A byte range can decode and
round-trip while still being data:

```asm
abs_0_00042C00:
    ori.b #$8000,d6
abs_0_00042C04:
    ori.b #0,d0
abs_0_00042C08:
    ori.b #0,d0
```

The bug is not that `ori` is invalid. The bug is accepting the run as code
without enough executable proof:

```text
legal decode
  -> maybe code-shaped observation
  -> not accepted code by itself

accepted code
  -> executable origin
  -> credible control-flow path
  -> credible terminal/fallthrough shape
  -> no fallthrough into owned data/table/string
```

The corpus evidence might come from Damocles or Starglider. The fixture should
not import Damocles or Starglider. It should construct the minimum bytes and
facts needed to prove the invariant.

## Tutorial: Reduction

Reduction starts by asking what fact is wrong, not what line looks odd.

For false code:

```text
wrong fact:
  accepted code run exists at offset X

required proof:
  hard executable origin or proven fallthrough from hard executable origin

missing/invalid proof:
  address observation was treated as control proof
  data/table pointer was treated as dispatch target
  weak decode island was accepted as reachable code
```

For unreferenced generated labels:

```text
wrong fact:
  rendered label statement exists with no visible access

required proof:
  object/container symbol origin
  structured data origin
  accepted code entry/control target
  visible rendered operand/branch/equate access

missing/invalid proof:
  analysis invented a label because a value looked address-like
```

For missing label definitions:

```text
wrong fact:
  rendered operand uses a symbol whose definition is not emitted

required proof:
  same section/offset/domain has a renderable label statement or equate

missing/invalid proof:
  source/runtime domain mapping was only partially applied
```

The reduced fixture should preserve the bad fact shape, not the whole target.

## Tutorial: Fixture Shape

The preferred fixture is C-level because source-quality facts and validators
live in C:

```c
static int test_source_quality_blocks_false_accepted_ori_run(void) {
  M68kSourceAnalysisIR source_analysis;
  M68kSectionAnalysisIR section;
  M68kAcceptedCodeRunIR run;
  M68kCodeStartRefIR weak_ref;
  char *json = NULL;

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_create(&source_analysis));
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_create(&section, test_ir_result_arena()));

  section.section_index = 0;
  section.section_size = 16;

  memset(&run, 0, sizeof(run));
  run.start_offset = 0;
  run.end_offset = 12;
  run.instruction_count = 3;
  run.end_kind = M68K_ACCEPTED_CODE_RUN_END_DECODE_GAP;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_accepted_code_run(&section, &run));

  memset(&weak_ref, 0, sizeof(weak_ref));
  weak_ref.offset = 0;
  weak_ref.reason = M68K_FACT_CODE_START_REASON_CONTROL_TARGET;
  weak_ref.evidence_kind = M68K_CODE_ORIGIN_EVIDENCE_UNKNOWN;
  weak_ref.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  M68K_C_ASSERT_INT(0, m68k_ir_section_analysis_append_code_start_ref(&section, &weak_ref));

  M68K_C_ASSERT_INT(0, m68k_ir_source_analysis_append_section(&source_analysis, &section));
  M68K_C_ASSERT_INT(0, m68k_source_quality_analyze(&source_analysis, NULL, NULL, NULL, NULL));
  M68K_C_ASSERT_INT(0, source_analysis_to_json(&source_analysis, &json, m68k_diag_sink(NULL)));

  M68K_C_ASSERT(strstr(json, "\"kind\":\"unterminated_or_invalid_code_range\"") != NULL);
  M68K_C_ASSERT(strstr(json, "\"blocker\":true") != NULL);

  free(json);
  m68k_ir_section_analysis_destroy(&section);
  m68k_ir_source_analysis_destroy(&source_analysis);
  return 0;
}
```

The exact helper names may differ. The important shape is stable:

```text
construct minimum facts
  -> run source-quality
  -> assert diagnostic/fact directly
  -> assert source refusal if blocking
```

Avoid this:

```text
import full target
  -> render full source
  -> assert one string disappeared
```

That can be useful as integration evidence, but it is not the primary proof.

## Tutorial: Repair At Cause

A fixture should fail before the repair. Then fix the producer that made the
bad fact possible.

For false code:

```text
bad producer candidates:
  control-target promotion too broad
  address observation bridged into code start
  table target promotion without table ownership proof
  fallthrough accepted through weak/unowned decode island
```

For labels:

```text
bad producer candidates:
  label premark from address-looking value
  source/runtime domain mismatch
  rendered access recorder missed operand form
  label statement emitted without durable origin
```

The repair is not:

```text
hide diagnostic
downgrade to warning
special-case target
teach UI to tolerate broken source
add a manual-review item for framework inconsistency
```

The repair is:

```text
bad fact no longer produced
  or
contradiction is classified as conflict and blocks export
```

## Tutorial: Corpus Evidence

Each source-quality invariant should have an inventory row:

```text
invariant
  -> corpus evidence
  -> focused fixture
  -> expected fact/diagnostic
  -> source refusal yes/no
  -> target rerender evidence
```

Example rows:

```text
false accepted ori/andi-shaped code run
  -> Damocles Tetragon 02, Starglider SG
  -> source_quality_blocks_false_accepted_ori_run
  -> unterminated_or_invalid_code_range
  -> source refusal: yes until producer is fixed
  -> rerender: target no longer emits false code

object/container symbol may be unreferenced
  -> synthetic hunk data_ref symbol
  -> source_quality_analyze_accepts_unreferenced_object_symbol_label_statement
  -> M68K_SYMBOL_ORIGIN_OBJECT_SYMBOL
  -> source refusal: no
  -> rerender: no target label-access regression

materialized runtime operand target must define label
  -> Magicland, Pandora, Bloodwych
  -> facts_v2_runtime_ref_labels_backward_materialized_data_target
  -> rendered operand and label statement agree
  -> source refusal: no
  -> rerender: full/content round-trip preserved
```

The inventory belongs near the proposal or in a linked validation document. It
should not be buried in free-form commit messages.

## Tutorial: Target Rerender Role

After the focused fixture passes, rerender affected targets:

```text
target command-line render/update
  -> generated .s changes
  -> round-trip report
  -> inspect render diff
```

The target sweep answers:

```text
did the fix compose with real inputs?
did source text drift unexpectedly?
did content/full-file reproduction regress?
did diagnostics surface at the right target/offset?
```

It does not answer:

```text
is the invariant precisely tested?
is the failure cause isolated?
is the validator too broad?
```

That is why both are required.

## Tutorial: Failure Policy

When a new corpus target fails validation:

```text
source-quality blocker
  -> analysis is inconsistent
  -> reduce to fixture
  -> fix producer or conflict classifier
  -> rerender target
```

Do not treat the new failure as an excuse to stop:

```text
"target now fails"
  -> useful reproduction
  -> not a blocker to investigation
```

The only acceptable temporary state is a failing fixture while implementing the
repair. The final state must be either:

```text
target renders cleanly
```

or:

```text
target refuses source with a correct diagnostic because the framework cannot
yet produce valid source for that case
```

If source is refused, the diagnostic must explain the cause and must be tracked
as remaining framework work, not user review work.

## Implementation Plan

1. Add or maintain an invariant inventory.
2. For each corpus-discovered failure, write the smallest C fixture first.
3. Fix the fact producer, validator, or conflict classifier at cause.
4. Add source-quality diagnostics only for hard framework invariants.
5. Rerender affected targets and update generated `.s` only when verified.
6. Run focused C tests, full C tests, Python tests, ruff, mypy, CDP, and
   precommit for output-affecting changes.
7. Commit the fixture, fix, proposal/inventory update, and target render drift
   together. Keep benchmark/timing churn separate unless it is the subject of
   the change.

## Acceptance Criteria

This proposal is working when:

```text
every new source-quality rule has a focused fixture
every corpus-discovered failure has an inventory row
large target tests are used for composition, not primary proof
validation failures drive producer fixes
source export cannot hide bad accepted code or bad symbols
CDP/precommit gates prove UI diagnostics for refused source
```

The immediate next candidate is accepted-code credibility:

```text
Damocles/Starglider false code evidence
  -> reduced C fixture
  -> hard executable-origin and terminal-shape validation
  -> producer repair so false code is not accepted
  -> target rerender proves the bad ori/andi run is gone
```

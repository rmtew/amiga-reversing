# Proposal 024: Classic Mac OS Segment Loader Fixups

Status: active

## Purpose

Decode Classic Mac OS Segment Loader relocation/fixup evidence far enough that
Mac CODE source presentation stops relying on broad deferred fixup placeholders
where the resource bytes contain parseable fixup information.

Proposal 023 made the current source presentation honest: CODE resources are
visible, CODE 0 routing is represented, A5/world context is deferred, and
Segment Loader effects are source-visible placeholders. 024 is the next step:
turn those placeholders into decoded source reference records where the bytes
support it, while keeping unsupported custom extension bytes explicit and
deferred.

Mac remains a restored-source platform, not a resource-fork round-trip target.
Amiga and Atari exact gates must remain green when shared code changes.

## Target Outcome

For the committed MPW `Asm` fixture, a reverser should be able to inspect a CODE
resource and see Segment Loader fixup evidence as concrete source records:

```text
CODE resource bytes
  -> Segment Loader fixup block/span discovery
  -> decoded fixup records where supported
  -> unsupported/custom extension placeholders where not
  -> source_reference_records attached to ownership ranges/source rows
  -> artifact/web/API display
  -> verifier proof that no decoded effect is silently dropped
```

Illustrative record shape:

```json
{
  "kind": "segment_loader_fixup",
  "resource_type": "CODE",
  "resource_id": 27,
  "byte_space": "code_resource_payload",
  "source_offset": 204,
  "source_range": {"start": 204, "end": 208, "size": 4},
  "effect": "relocate_long",
  "target": "CODE:27+0x0000",
  "status": "decoded",
  "fact_status": "candidate",
  "parser_use": "candidate_only",
  "source_visible": true
}
```

Unsupported effects must stay precise:

```json
{
  "kind": "segment_loader_fixup_placeholder",
  "resource_id": 1,
  "source_range": {"start": 40, "end": 29024, "size": 28984},
  "status": "deferred",
  "reason": "custom extension opcode not decoded",
  "source_visible": true
}
```

## Stopping Contract

024 is complete when the committed Mac fixture has:

- a C-owned Segment Loader fixup parse model for the current CODE bytes;
- decoded records for every supported fixup form encountered, if any are proven
  from actual fixup encoding bytes;
- typed placeholders for unsupported, malformed, or custom extension spans;
- restored-source `source_reference_records` using decoded records where
  available instead of broad-only placeholders;
- artifact/web/API output exposing decoded effects and residual placeholders;
- tests proving absent/unsupported evidence cannot become accepted references;
- Proposal 023 source-presentation behavior still intact;
- no Mac round-trip claim.

## Implementation Direction

- Implement parsing and record emission in C. Python may expose and test it.
- Start with current MPW `Asm` fixture bytes and current parser evidence.
- Prove where fixup encoding bytes come from in the resource format before
  decoding them. A CODE payload candidate span is not, by itself, fixup encoding
  provenance.
- Decode only forms that are understood from bytes and existing facts.
- Keep unsupported forms deferred with byte spans, reasons, and provenance.
- If 024-001 finds no supported fixup form, stop the decoder track, record the
  blocker in this proposal, and do not force 024-003/024-005 implementation.
- Attach decoded effects to restored-source ranges/rows when possible.
- Keep A5 lifetime proof out of scope unless directly required to describe a
  decoded fixup target safely.
- Do not weaken Amiga/Atari round-trip proof.

## Work Items

### 024-001: Current Fixup Byte Inventory And Parser Boundary

Build a narrow C/API/test harness that locates current Segment Loader fixup
candidate spans in the committed MPW `Asm` fixture, proves where actual fixup
encoding bytes come from, and records what bytes are parseable versus still
custom/unknown.

This issue must end with executable evidence, not only documentation.

024-001 boundary result:

- The C-owned Mac resource parser now emits
  `segment_loader_fixup_inventory_v1` in the Mac CODE summary. The committed
  MPW `Asm` fixture produces deterministic inventory records for all 28 CODE
  resources.
- CODE 0 is classified as `absent`. Nonzero CODE resources are classified as
  `custom_unknown` with deferred status, exact candidate affected-byte spans,
  provenance, source visibility, and `encoding_byte_provenance.known=false`.
- No record is `parseable`, and no record identifies a real Segment Loader
  fixup encoding byte stream. The current candidate CODE payload span remains
  visible only as bytes that may be affected by fixups, not as bytes that encode
  fixups.
- Decode work is therefore blocked after 024-001. 024-003 and 024-005 must not
  emit decoded records until a future issue proves actual on-disk fixup encoding
  byte provenance for a supported form.

Review correction after 024-001:

- The 024-001 result is a current-parser boundary, not a final platform
  boundary. Classic Mac OS Segment Loader/CODE layout is old documented
  technology; lack of provenance in our current parser means the parser is
  incomplete, not that the evidence cannot be identified.
- Continue with a documentation-backed implementation slice. Use primary
  Apple/MPW documentation where available, including Inside Macintosh Runtime
  Architectures / Segment Manager material and MPW Segment Loader notes, to map
  the CODE segment layout and locate A5 relocation and segment relocation
  information.
- Do not decode from guesses or broad CODE payload spans. The next issue must
  connect documented layout fields to resource bytes, add parser support, and
  update the inventory from `custom_unknown` to parseable/unsupported/malformed
  states only where the documented layout supports it.

### 024-002: C Fixup Record Model

Add a C-owned Segment Loader fixup record model that can represent decoded
effects and deferred placeholders with resource identity, byte span, status,
reason, provenance, and source visibility.

Superseded ordering note: 024-002 is paused until 024-009 researches and
implements documented CODE segment layout extraction. The record model must be
based on that parser boundary, not the pre-024-009 `custom_unknown` inventory.

### 024-003: Decode First Supported Fixup Form

Implement the first supported fixup decoder found in the MPW `Asm` fixture and
emit decoded source reference records for it. Keep all other forms deferred. If
024-001 does not prove any supported form, this issue must not invent one; it
must record the blocker and leave later decode-expansion issues blocked.

Paused until 024-009 identifies documented fixup encoding byte provenance and
024-002 adds the record model.

### 024-004: Attach Fixups To Restored Source Rows

Attach decoded fixup records and residual placeholders to restored-source
ownership ranges/source rows so artifact/web/API users can navigate from source
to fixup evidence.

Paused until 024-009 and 024-002 provide a documented parser/model boundary.

### 024-005: Expand Supported Fixup Forms

Decode the remaining supported forms found by 024-001 where the format is clear
from bytes and current evidence. Leave custom/ambiguous forms as typed
placeholders.

Paused until 024-009/024-003 prove one or more supported forms.

### 024-006: Replace Broad Fixup Placeholders

Remove broad Segment Loader placeholder output where decoded records or precise
per-span placeholders now exist. Keep fail-closed behavior for missing parse
model output.

Paused until decoded records or precise per-fixup placeholders exist. Current
broad placeholders remain transitional evidence, not a final decoder result.

### 024-007: Source Display And Web/API Exposure

Expose decoded fixup effects and residual placeholders in existing source,
artifact, web, and API surfaces without a UI redesign.

Paused until decoded records or precise per-fixup placeholders exist.

### 024-008: Closeout Proof

Close 024 by proving decoded fixup records, residual placeholders, source
presentation, and cross-platform gates together.

Paused: 024 cannot close its decoder track until 024-009 resolves the documented
layout/parser boundary or records a primary-source contradiction.

### 024-009: Documented CODE Segment Layout Parser

Research documented Classic Mac OS CODE segment layout and implement the parser
boundary needed to locate Segment Loader relocation/fixup encoding bytes.

Required outcome:

- Primary Apple/MPW documentation is cited in Proposal 024 with the specific
  fields/offsets relevant to code bytes, A5 relocation information, and segment
  relocation information.
- The C Mac resource parser maps those documented fields onto current CODE
  resource bytes where the fixture supports it.
- `segment_loader_fixup_inventory_v1` no longer treats all nonzero CODE payload
  candidate spans as `custom_unknown` merely because the old parser lacked a
  model.
- Records become `parseable`, `unsupported`, `malformed`, or still
  `custom_unknown` according to documented layout evidence.
- If the current MPW `Asm` fixture uses a custom extension or variant not
  covered by the docs, the blocker is recorded as that specific documented
  mismatch, not as generic missing provenance.
- No decoded fixup effect is emitted until the parser has identified the actual
  encoding byte span and format.

## Verification Plan

Minimum proof for every issue:

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
git diff --check
```

Shared C/source-output changes must also run:

```powershell
cmd /c src\precommit.bat
.\src\build\m68k_c_unit_tests.exe
```

## Issue Ordering

- 024-001 starts first.
- 024-009 follows 024-001 and reopens the path after the current-parser
  boundary result.
- 024-002 follows 024-009.
- 024-003 follows 024-002.
- 024-004 follows 024-003.
- 024-005 follows 024-004.
- 024-006 follows 024-005.
- 024-007 follows 024-006.
- 024-008 closes the proposal.

## Non-Goals

- Classic Mac OS resource-fork round-trip.
- A5 lifetime proof beyond safe fixup context.
- Broad non-CODE resource payload decoding.
- 017 cascade/evidence-review protocol changes.
- UI redesign.

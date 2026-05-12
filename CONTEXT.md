# Amiga Game Disassembly Project

This context describes the project language around reverse engineering Amiga and related 68000 binaries into reproducible, editable source.

## Language

**Reproduction Comparison**:
The check that decides whether rebuilt bytes preserve the original target at the selected exactness level, possibly producing adjusted rebuilt bytes when container shape can be preserved without changing semantics.
_Avoid_: Diff, verification

**Source Rendering**:
The production of assembler source text from analysed target facts.
_Avoid_: Disassembly when specifically referring to emitted source text

**Assembly**:
The production of rebuilt bytes from rendered source.
_Avoid_: Rebuild when specifically referring to the assembler step

**Assembler Policy**:
The policy values that control how assembly emits target bytes, including container encoding choices such as relocation record type and optional symbols.
_Avoid_: Assembler options when referring to the normalized policy model

**Project Rebuild**:
The production of rebuilt target bytes for a project using original target metadata and preserving recognized original container shape by default.
_Avoid_: Assembly when specifically referring to project-aware reproduction output

**Round-Trip Verification**:
The workflow that renders source, assembles rebuilt bytes, runs reproduction comparison, and records the result.
_Avoid_: Reproduction comparison

**Container Shape**:
Bytes and records that affect the file container representation but not the program payload semantics at the selected exactness level.
_Avoid_: File shape when specifically referring to non-semantic container representation

**Original File Structure**:
User-facing wording for non-content parts of the original target file that may need to be preserved or explained.
_Avoid_: Container record

**Container Layout**:
C-emitted byte ranges that classify original or rebuilt bytes by container role, such as header, section payload, relocation records, symbols, debug, or section end.
_Avoid_: File layout when specifically referring to binary container ranges

**Container Encoding**:
The concrete container record choices used to represent content, such as relocation record type, ordering, grouping, header flags, and terminators.
_Avoid_: Container layout when referring to record representation choices

**Reproduction Comparison Context**:
The C-owned state used to compare original bytes and rebuilt bytes under a selected backend and reproduction policy.
_Avoid_: HUNK-specific fixer context

**Workflow Arena**:
C-owned temporary memory for one top-level C workflow call, destroyed before the call returns and never used for returned artifacts.
_Avoid_: Global scratch arena, process scratch arena, returned artifact arena

**Scratch Mark**:
A saved position in a **Workflow Arena** that is rewound before leaving a local analysis or rendering pass.
_Avoid_: Free list, object destructor, result owner

**Result Arena**:
C-owned memory that lives exactly as long as a C result object and is destroyed by that object's destroy function.
_Avoid_: Workflow scratch, caller-freed output buffer

**Arena Builder**:
A growable C collection or output accumulator that allocates from an explicit arena and finalizes into arena-owned storage without later per-buffer free calls.
_Avoid_: realloc-owned vector, hidden heap list

**Caller-Freed Output Buffer**:
A plain text or byte buffer returned through a public C API and released by the caller with the matching free function.
_Avoid_: Result arena pointer, workflow arena pointer

**Local C API**:
A C interface consumed only by this repository and changeable when a cleaner ownership model requires it.
_Avoid_: External ABI contract, compatibility boundary

**Compatibility Shim**:
Legacy adapter code that preserves an older internal API shape after repository-owned callers have moved to a cleaner interface.
_Avoid_: Migration helper, local API cleanup

**Reproduction Exactness**:
The level at which rebuilt bytes preserve the original target, ranging from full-file equality through content equality to mismatch.
_Avoid_: Pass/fail when the distinction matters

**Full-File Exactness**:
The condition where rebuilt bytes are byte-for-byte identical to the original target, including payload, container layout, and container encoding.
_Avoid_: Container exactness

**Content Exactness**:
The condition where rebuilt bytes preserve the target's meaningful payload or content even when the surrounding container representation is not full-file exact.
_Avoid_: Exact reproduction when full-file bytes differ

**Relocation Fixup Set**:
The resolved set of relocation fixups a container applies to payload bytes, independent of how those fixups are encoded in container records.
_Avoid_: Relocation order when referring to payload relocation meaning

**Policy Divergence**:
The condition where the selected assembler policy emits a different container shape than the recognized original container shape.
_Avoid_: Unsupported shape

**Unsupported Container Shape**:
Original container shape that is observed but not understood well enough to preserve or fully check.
_Avoid_: Policy divergence

## Relationships

- **Round-Trip Verification** includes **Source Rendering**, **Project Rebuild**, and **Reproduction Comparison**.
- **Project Rebuild** supplies an **Assembler Policy** to **Assembly**.
- Standalone **Assembly** uses an ideal/default **Assembler Policy** unless the caller overrides selected policy values.
- **Reproduction Comparison** consumes original bytes and rebuilt bytes.
- **Reproduction Comparison** runs inside a **Reproduction Comparison Context**.
- A **Workflow Arena** supplies temporary C memory within one top-level workflow call.
- A **Scratch Mark** creates a nested temporary lifetime inside a **Workflow Arena**.
- A **Result Arena** owns internal pointers inside one C result object.
- An **Arena Builder** is a reusable building block for append-style collections in either a **Workflow Arena** or **Result Arena**.
- A **Caller-Freed Output Buffer** must not point into a **Workflow Arena** or **Result Arena**.
- C modules that allocate internal pointers choose a **Workflow Arena** or **Result Arena** explicitly at their interface.
- C allocation cleanup starts by classifying every allocation site by lifetime; only workflow and result ownership sites are converted first.
- Internal C ownership migrations replace old ownership paths instead of keeping compatibility or fallback paths.
- A **Local C API** may change when arena ownership makes a cleaner interface.
- A **Compatibility Shim** is avoided for repository-owned code because this project has no external compatibility contract.
- **Project Rebuild** preserves recognized original **Container Shape** by default.
- **Original File Structure** is the user-facing way to describe **Container Shape** differences.
- **Container Shape** can differ while **Reproduction Comparison** still reports **Content Exactness**.
- **Container Layout** gives Python the byte ranges it needs for report and row issue mapping.
- **Container Encoding** is used to derive the **Assembler Policy** for **Project Rebuild**.
- **Reproduction Exactness** is reported by **Reproduction Comparison**.
- **Full-File Exactness** is the strongest kind of **Reproduction Exactness**.
- **Content Exactness** is a kind of **Reproduction Exactness**.
- A changed **Relocation Fixup Set** prevents **Content Exactness**.
- A preserved **Relocation Fixup Set** with different record ordering or grouping is a **Container Shape** difference.
- **Policy Divergence** means the original **Container Shape** was recognized but not selected by **Assembler Policy**.
- **Unsupported Container Shape** means the original **Container Shape** was not understood well enough to derive a preserving **Assembler Policy**.

## Example Dialogue

> **Dev:** "Did round-trip verification fail in source rendering, assembly, or reproduction comparison?"
> **Domain expert:** "Assembly succeeded; reproduction comparison found only a reloc record ordering difference that can be preserved without changing semantics."

## Flagged Ambiguities

- "reproduction" was used for both the whole verification workflow and the byte comparison step; resolved: **Round-Trip Verification** is the workflow, **Reproduction Comparison** is the byte comparison step.

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

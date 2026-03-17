# Amiga Game Disassembly Project

## Project Purpose
LLM-assisted reverse engineering of Amiga game binaries. The goal is a fully
reassemblable, documented disassembly with named symbols, typed data, and
cross-references.

## Spec-Driven Development

All M68K tooling (disassembler, assembler, simulator, effect predictor) is
generated from structured data extracted from the Motorola 68000 Programmer's
Reference Manual PDF. Nothing is hardcoded from human memory of the spec.

### The Pipeline

```
PDF  →  parser  →  JSON (knowledge base)  →  generated tools
                                                  ↕
                                          independent oracles
```

1. **PDF → JSON**: Parsers extract structured data from the PDF into
   `knowledge/m68k_instructions.json`. Encodings, EA modes, forms, constraints,
   condition code effects, SP effects — all derived mechanically.
2. **JSON → Tools**: Disassembler, assembler, effect predictor, and any future
   tools are driven from the JSON. No tool encodes M68K knowledge independently.
3. **Oracles verify tools**: External implementations we did not write (vasm for
   assembly, machine68k/Musashi for execution) serve as ground truth. They exist
   only to verify our generated code — they are not components in the tool chain.

### Rules

- **Never hardcode M68K knowledge.** If a tool needs a fact about an instruction,
  that fact must be in the JSON, extracted from the PDF by a parser.
- **Fix upstream, not downstream.** If generated code is wrong, fix the parser or
  the extraction — don't patch the generated tool.
- **If the JSON can't express it, extend the JSON.** Add new fields to the schema,
  add a new parser phase, re-extract from the PDF.
- **Parser-asserted KB entries are allowed** when the PDF implies but does not
  explicitly state a fact (e.g. "carry is generated" without defining carry).
  The parser inserts the interpretation into the JSON with a code comment that:
  (1) cites the PDF page/section, (2) explains why it cannot be parsed directly,
  and (3) states the universal or standard definition being asserted.
  Downstream tools read these entries identically to parsed ones — no special cases.
- **Oracles are black boxes.** We don't modify vasm or Musashi. We only ask them
  questions and compare answers.

## Key Conventions

### Entity Tracking
- Every address range in the binary is an **entity** tracked in `targets/<name>/entities.jsonl`
- Entities have types: `code`, `data`, `bss`, `unknown`
- Data entities have subtypes: `sprite`, `bitmap`, `copper_list`, `palette`,
  `tilemap`, `string`, `pointer_table`, `sound_sample`, `level_data`,
  `struct_instance`, `lookup_table`, etc.
- Entity status progression: `unmapped → typed → named → documented`
- Confidence levels: `tool-inferred`, `llm-guessed`, `verified`

### Target Output
- Per-target output goes in `targets/<name>/` (entities, disassembly, progress)
- Disassembly output is vasm-compatible `.s` files
- Use symbolic names from entities for all labels and references
- Hardware register accesses must use symbolic names from `knowledge/amiga-hardware.md`
- OS library calls must reference names from `knowledge/amiga-os.md`

### Verification
- **Round-trip test is mandatory**: reassemble with vasm, binary-diff against original
- Run `scripts/validate.py` after every batch of changes
- Never mark an entity as `verified` unless it passes round-trip or type-specific checks

### Knowledge Files
- `knowledge/m68k.md` — 68000 ISA reference
- `knowledge/amiga-hardware.md` — custom chip register map
- `knowledge/amiga-os.md` — OS library calls and structures
- `knowledge/game-specific.md` — discovered game conventions (updated as we learn)
- Load knowledge files on-demand, not all at once

### Working With Entities
- When analyzing a code entity, always check its xrefs first
- Propagate naming: if a function is named, its data references can often be named too
- When naming, prefer descriptive names: `update_player_position` not `sub_1234`
- Record all cross-references bidirectionally (calls/called_by, reads/read_by, etc.)

### Binary Files
- Original binary goes in `bin/` — never modify originals
- Reassembled test binaries go in `bin/rebuilt/` (gitignored)

# Amiga Game Disassembly Project

## Project Purpose
LLM-assisted reverse engineering of Amiga game binaries. The goal is a fully
reassemblable, documented disassembly with named symbols, typed data, and
cross-references.

## Key Conventions

### Entity Tracking
- Every address range in the binary is an **entity** tracked in `entities.jsonl`
- Entities have types: `code`, `data`, `bss`, `unknown`
- Data entities have subtypes: `sprite`, `bitmap`, `copper_list`, `palette`,
  `tilemap`, `string`, `pointer_table`, `sound_sample`, `level_data`,
  `struct_instance`, `lookup_table`, etc.
- Entity status progression: `unmapped → typed → named → documented`
- Confidence levels: `tool-inferred`, `llm-guessed`, `verified`

### Disassembly Output
- All disassembly output goes in `disasm/` as `.s` files (vasm-compatible syntax)
- Use symbolic names from `entities.jsonl` for all labels and references
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

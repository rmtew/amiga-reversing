# Explicit optional binary corrections

The canonical target source reconstructs the original, including its bugs.
`amiga_reversing.tools.optional_patch` creates a separate rebuilt artifact only
when invoked explicitly. With no `--enable`, its output is the original bytes.
It never changes the target binary, generated assembly, or Manual Action Log.

The first supported layout is a raw, single-section payload. Each selected
manifest record carries canonical instruction boundary keys, expected original
bytes, equal-length replacement bytes, an annotated assembly source and hash,
rationale, preconditions, and conflicting patch IDs. The CLI checks the whole
original hash, selected ranges and conflicts, then resolves both boundaries
against the current native listing. Unknown IDs, stale bytes, overlaps, size
changes, and unresolved boundaries are refused before output is created. Output
must be a new directory beneath `bin/rebuilt`. Hunk mapping, relocation,
code-cave allocation, automatic patch selection and emulator admission of these
artifacts are deliberately outside this initial fixed-layout proof.

## Pandora NULL animation-node guard

[Manifest](../patches/pandora/optional-patches.json) and
[assembly](../patches/pandora/null-node-guard.s) replace only source
`$867E..$86A6`, the 40-byte state-exchange helper. The default remains original.

```sh
.venv/bin/python -m amiga_reversing.tools.optional_patch \
  --manifest patches/pandora/optional-patches.json \
  --output-directory bin/rebuilt/pandora-original-copy

.venv/bin/python -m amiga_reversing.tools.optional_patch \
  --manifest patches/pandora/optional-patches.json \
  --enable guard-null-state-node \
  --output-directory bin/rebuilt/pandora-null-guard
```

The correction skips node mode/phase resets for a NULL incoming node, while
still exchanging the active and saved position states. Object offsets `$2C`
and `$4E` are the descriptor and saved-state pointers; state offset `$08` is
the animation node; node offsets `$0A` and `$10` are mode flags and frame/phase.
A temporary `MOVE.L` push sets Z, and `MOVEA` pops without changing CCR before
`BEQ`. Removing two explicit zero displacements recovers the four bytes needed
for the check. No code/data address moves and no helper storage is allocated.

Preconditions retain valid object, state and descriptor pointers, and require
12 writable stack bytes below entry SP, disjoint from those records and code.
The original required eight. The additional four-byte scratch write is explicit;
this is not an alias-safe routine for arbitrary overlapping pointers/stacks.
Final registers, SR/CCR, state exchange and non-NULL node effects match original
CPU execution in the focused cases. NULL cases preserve the low-memory sentinel
instead of changing byte `$A` and word `$10`. The actual original message and
health-draw callees also complete with either helper in a synthetic death-branch
fixture, without restoring registers between callees.

[Gameplay evidence](../runtime/observations/pandora-combat-null-node.json)
separately proves the original bug through normal input and checkpoint execution:
first security damage, then combat defeat, then a NULL reset that zeros the high
word of the illegal-instruction vector. No guest predicates were edited for that
proof. The corrected variant has **not** been run through gameplay; its current
scope is independent vasm assembly and bounded CPU equivalence/correction tests.

```sh
.venv/bin/python -m pytest -q tests/test_optional_patch.py \
  tests/test_pandora_optional_patch.py tests/test_pandora_security.py \
  tests/test_pandora_state_transitions.py
```

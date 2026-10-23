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
code-cave allocation and automatic patch selection remain outside this
fixed-layout mechanism.

The resulting `receipt.json` is admitted by the headless runtime through
`--derived-artifact`. Admission reconstructs the entire corrected payload from
the original plus the exact selected patch records, verifies its hash and size,
and rechecks canonical boundaries. It adds no memory reservation or runtime
predicate edit. Boot handoff and materialization verify the corrected bytes.
Checkpoints bind the payload, receipt, media, ROM and emulator hashes; original
snapshots cannot be substituted for a fresh corrected boot.

Original instruction anchors inside a rewritten range are refused. Functions
intersecting that range are omitted from canonical runtime symbols, and a
paused PC inside it is not presented as an original instruction. Use unchanged
caller/return anchors for observations. Each public CLI invocation owns one
immutable canonical analysis snapshot shared by admission, compilation and
reporting; all byte/hash checks remain active, and the snapshot is closed on
success or failure. It is not cached across invocations.

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
proof. The corrected variant has also completed the same ordinary combat-defeat
route from a fresh corrected boot. The vectors remain intact, the state exchange
returns normally, and eight subsequent main-loop visits retain HP 0, the defeated
flag and static pose with combat mode clear. The exit counter remains 70 during
that bounded window; a complete exit/title transition is not claimed.

The original bus-error vector at `$8..$B` remains `$00FC0818`: byte `$A` is `$08`
and its bit 0 was already clear. The illegal-instruction vector at `$10..$13`
changes `$00FC081C` to `$0000081C` in the original and remains `$00FC081C` with
the guard. These are vector addresses, not overwritten handler instructions.
No visual comparison or exception-consequence test was performed. Treat this
as a low-impact original bug and an optional-fix mechanism proof, with no
demonstrated player-visible improvement.

The non-NULL entry-officer exchange also matches original captured registers,
state/node bytes and vectors. Its only observed difference is the declared extra
four-byte stack scratch. The normal caller had already reset this node; the CPU
tests above cover nonzero mode/phase inputs separately. All captures in the eight
shared west-through-first-damage segments match their original counterparts.
See [corrected gameplay evidence](../runtime/observations/pandora-corrected-combat-defeat.json).

```sh
.venv/bin/python -m pytest -q tests/test_optional_patch.py \
  tests/test_pandora_optional_patch.py tests/test_pandora_security.py \
  tests/test_pandora_state_transitions.py
```

## Reproduce the corrected route

Build a fresh enabled artifact with the command above, then supply its
`receipt.json` to **every** runtime segment using `--derived-artifact`. Do not
load an original-build checkpoint. Use a new run directory if destinations exist.

The corrected root uses the existing corridor recipe with two read-only caller
probes inserted after the officer's item transfer. This composition avoids
copying the entire corridor scenario and leaves its input schedule unchanged:

```sh
pandora_run=.runtime-state/pandora-corrected-reproduction
.venv/bin/python - "$pandora_run" <<'PY'
import json, sys
from pathlib import Path
root = json.loads(Path('runtime/scenarios/pandora-corridor-actors.json').read_text())
probe = json.loads(Path('runtime/scenarios/pandora-nonnull-exchange.json').read_text())
root['identifier'] = 'pandora-corridor-nonnull-exchange'
i = next(i for i, p in enumerate(root['phases'])
         if p['name'] == 'entry_officer_card_transferred') + 1
root['phases'][i:i] = [p for p in probe['phases']
                       if p['name'].startswith('nonnull_exchange_')]
assert len(root['phases']) == 64
path = Path(sys.argv[1]) / 'root-scenario.json'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(root, indent=2) + '\n')
PY
pandora_target=amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
pandora_artifact=bin/rebuilt/pandora-null-guard/receipt.json
pandora_rom=/workspace/attachments/30c1a24c-f353-4e4e-9dc0-36ce5cee8932/kick13.rom
pandora_emulator=/workspace/copperline-assessment/squashfs-root/usr/bin/copperline
.venv/bin/python -m amiga_reversing.tools.copperline_session \
  --target "$pandora_target" --rom "$pandora_rom" --copperline "$pandora_emulator" \
  --direct-payload-contract pandora --derived-artifact "$pandora_artifact" \
  --state-directory "$pandora_run/root" --scenario "$pandora_run/root-scenario.json" \
  --checkpoint-save "$pandora_run/corridor.json" --run
```

The composed raw scenario SHA256 for this proof is
`1198dcc1ae704751f861bb696df3bbe921fc956f8eb87f2466799eca09693cc6`.
Continue with the same command and artifact, replacing the state directory,
scenario and checkpoint arguments as follows. Scenarios are under
`runtime/scenarios/`; each state directory must be fresh.

| Scenario | Load receipt | Save receipt/state directory |
|---|---|---|
| `pandora-rifle-west-staging.json` | corridor | west |
| `pandora-flight-model-crossing.json` | west | east |
| `pandora-rifle-approach.json` | east | ready |
| `pandora-rifle-pickup.json` | ready | rifle |
| `pandora-rifle-checkpoint-audit.json` | rifle | audit |
| `pandora-camera-idle-observation.json` | audit | neutral |
| `pandora-reverse-flight-staging.json` | neutral | reverse-stage |
| `pandora-reverse-security-damage.json` | reverse-stage | damage |
| `pandora-corrected-combat-defeat.json` | damage | defeat |

For example, add `--checkpoint-load "$pandora_run/corridor.json"` and use
`--checkpoint-save "$pandora_run/west.json"` for west staging. The separate
original non-NULL baseline uses `pandora-nonnull-exchange.json` from fresh boot,
without a derived artifact or checkpoint load.

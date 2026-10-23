# Runtime memory relocation proof

Architecture follow-up: [Proposal 046](046-canonical-memory-layouts.md) proposes
consolidating region/address resolution and adding canonical fixed-layout export.
It preserves the bounded proofs/refusals below without requiring this deferred
keyboard proof to close before reproducing the demonstrated Pandora layout.
The successful source-patched relocation experiment is separate from admission
through this single-region proof/build path.

The first connected target is Pandora's 128-byte keyboard state. Region identity,
native references, same-extent rewrites, whole-payload identity, checked allocation
and bounded original-layout runtime evidence exist. The target relocation remains
incomplete: five accepted pointer paths have unresolved address/frame obligations.
This proposal describes the next general proof capability, not an authorization to
patch a refused target or a claim that observed scenarios establish closure.

## Implemented relative frame step

`m68k_memory_frame_prefix.inc` interprets accepted native instructions from a
canonical entry to a selected pointer producer. It handles bounded direct calls,
balanced word/long stack transfers, MOVEM aggregate spans, immediate affine SP
adjustments and direct SP-relative LEA. Branches retain both outcomes. Every CALL
owns a distinct intact return slot; normal returns must balance their frame.
Unknown writes through another base, SP escape/replacement, unsupported implicit
effects and inconsistent join deltas refuse. State, depth and extent limits are
explicit refusals rather than evidence that an omitted path is harmless.

Region references expose the prefix's entry, relative delta/envelope, state/path
counts and failure instruction. `absolute_sp` stays null. A balanced prefix may
support a normal borrowed caller context, but cannot establish separation between
another base register and the frame. Root proofs retain their alias checks.

Signed address-source arithmetic now consumes `source_sign_extend` from the
existing Motorola-derived KB and generated operand widths. Abstract and concrete
simulation agree on WORD extension and defined unsigned wrapping. Unknown or
truncated section-pointer sources remain unknown. Independently encoded vasm
fixtures and actual Copperline execution check this transfer, including unchanged
ADDA/SUBA SR. This is a shared simulator correction, not a Pandora instruction
special case. Generated metadata layout changes require rebuilding all consumers.

An additional test observation is outside this correction: abstract ADDQ/SUBQ to
an address register can lose SR because the extracted conditional CCR behavior is
not represented. Its parser/execution model needs a separate grounded extension;
do not encode a mnemonic exception in the relocation interpreter. Current prefix
proof explores both branch outcomes and does not rely on that CCR result.

## Bounded leaf liveness and Pandora's actual interrupt configuration

`m68k_memory_pointer_liveness.inc` projects future uses after an adjacent bounded,
non-mutating leaf read. It follows accepted branches, calls and register aliases,
stopping a path at independent overwrite, observation, escape or an unsupported
observer. It retains tail-return uncertainty, rejects partial alias overwrites,
and does not admit a first leaf that overwrites the producer through MOVEM or can
raise a described exception. Event/state/depth limits never certify omitted paths.
The result explicitly does **not** discharge relocation, frame integrity, IRQ
observers or instruction/interrupt timing. Root and prefix proofs now also refuse generated exception triggers
and bounds traps; a CHK path must not silently become closed.

For Pandora's `$9062` root, the current native audit visits 109 states after the
read at `$9068`: no later pointer use, independent overwrites at `$2D2A`, `$6122`
and `$921A`, and a mode/exception barrier at warm restart `$464`. These are source
offsets; the materialized program view starts at runtime `$10000`.

The relevant environment is the original A500/68000 game after its bootstrap,
with no external vector/callback patching, debugger-injected exceptions, NMI or
trace execution, and an intact game-owned stack and original resources. Startup
installs TRAP0 at `$482`, executes it at `$486`, sets SR to `$2700` at `$488`, and
later `$2000` at `$512`. The remaining recognized SR writes use `$2700`/`$2000`,
or restore the locally saved SR in the atomic callback setter `$2656..$2660`.
Thus warm restart's `$2700` write does not leave supervisor mode in this game
configuration; arbitrary user-mode entry is not the relevant blocker.

Setup installs the level-3 handler `$8E4` through vector `$6C` at `$4E0`, clears
INTENA, and enables master/Copper/VBL with `$C030` at `$516`. Title transitions
toggle the master bit, not another interrupt source. The handler saves
D0/A0-A1/A5-A6, replaces A0 with a callback, then restores it before each RTE.
The interrupted A0 slot is `8(SP)` at callback entry and `60(SP)` at the audio
callee reached through the gameplay VBL wrapper's `$9D0` call. Recognized
dispatcher/callback stack accesses do not explicitly read that interrupted slot.

This is insufficient for closure: gameplay VBL reaches audio entry `$4D8FC`,
whose live stream decoder reaches the **unresolved native indexed jump `$4DC2A`**.
The table at `$4DCE8` contains eleven commands `$80..$8A`; the instruction path
alone admits `$80..$9F`. The existing original-resource token observations do not
establish a native invariant over mutable stream cursors, configuration selectors
and all their writers. Assuming an intact stack or unchanged input file cannot
substitute for that missing continuation bound. No observed saved-A0 read is
claimed, but not every callback continuation is certified. The root and region
therefore retain their refusals (five unresolved roots); no pair lowering,
conditional runtime guard or changed instruction mapping has been introduced.

Keyboard relocation is deferred. The smaller active region is
`audio_master_volume`, source `$4DD00`, two bytes initially `$0040`: native facts
identify two PC-relative reads and three absolute writes, including one high-byte
write. The mapped-source plan retains both PC-displacement instruction forms and
uses `$65400` with an eight-byte backing lease. Moving these accesses changes no
address register or IRQ save payload. Accepted-reference closure is narrower than
whole-program alias or future-resource closure.

The direct shim now owns the complete loaded input before reading it; a contained
destination shares that lease. Allocating the destination after reading was
observed to corrupt live source bytes through Exec split metadata. The mandatory
materialization protocol verifies full input, stops at the declared native copy
handoff, verifies the full copied image, then initializes exactly the logical
bytes with readback and a reverse anchor. Consumption at that boundary is an
explicit payload-bound loader assertion. Native owner regions, runtime-equate
extents and materialized views remain placement exclusions; allocator success
alone never makes a destination safe. Current execution coverage and outstanding
writer coverage are in the [target ledger](../targets/pandora-restoration-status.md).
A normal-input comparison now exercises both WORD writers and a note output at volume 6 in both
layouts, preserving the old-address guard. The separate high-byte writer remains
uncovered even after a passing normal inventory/combat route defeats the Feed in
both layouts: combat clears the shared audio bit, and the BYTE reset requires that
bit set as well as defeat. The secondary setter has no accepted incoming references/CFG edges; this does
not prove it unreachable. A separate direct weapon-kill path can preserve the
armed flag, unlike full combat: the selected-item ray runs before same-frame
proximity audio, and its callbacks clear the adjacent audio/event bytes rather
than the shared flag. This remains conditional until ordinary acquisition, aim
and hit predicates are observed.

The compact Pandora world model now predicts the specific pianist encounter that
blocked the rifle route and validates its following UI/movement transition. It
uses native symbols/schemas, original script opcode values and verified captures;
unknown actor state and patrol timing remain explicit. Its conservative swept
patrol envelope admits a staging goal but not a complete rifle route. The next
step is a short-horizon actor-state predicate, not more guessed routes or a
general game-playing engine. No forced state or keyboard-region proof expansion
is implied. See the [target ledger](../targets/pandora-restoration-status.md).
The twelve-byte `camera_scroll_profiles` table is another bounded CPU-only data
family (two three-WORD records), with additional PC-indexed access, caller/index
and pointer-lifetime obligations. The camera candidate is not a ready plan, and slicing
the keyboard buffer does not remove its indexed writers or inherited aliases.

## Shared storage identities

Region definitions can now retain intersecting semantic identities. The previous
parser/action rejection could not express an input buffer that is also part of
another subsystem's snapshot. Native facts enumerate each exact intersection,
its offsets in both identities, and an open `coordinated_source_placement`
obligation. Both directions remain open even if one identity has no direct
instruction reference. Adjacent intervals retain their previous independence.

The single-region planner refuses `overlapping_source_regions`; this is no
joint-move implementation and no assertion of phase exclusion. Pandora records
the 32-byte work-buffer palette input at `$77FE0` inside the 768-byte hit snapshot
at `$77D00`. Preserving the alias requires a common placement/offset relationship,
or a separately established semantic split with all producers and consumers
retargeted. CPU-only use of one identity does not remove the other identity's
chip-DMA requirement. Persistent identifies fixed storage, not immutable bytes,
exclusive allocation or an established caller lifetime.

## Address and frame provenance

The next step needs tagged values: unknown, absolute runtime address with native
producer identity, and frame-relative address with frame identity and offset.
Affine transfers and matching saved/restored registers preserve their lineage.
Native runtime views resolve source placement; rendered text and an assumed load
base must never become another address database. Values loaded from mutable game
memory stay unknown unless a native writer invariant establishes their range.

Pandora establishes an application base with a native LEA and initializes a stack
in its materialized image. Those producers are evidence candidates, not global
invariants: audio code changes A6, callers restore saved values, and interrupts
push hardware and register-save frames. A typed application slot alone cannot
discharge an alias obligation. Every admitted memory write needs a proved range
disjoint from the keyboard region and every live return/saved-pointer slot.

## Optional conditional execution contract

An explicit conditional route can be useful without claiming whole-game closure.
It would require a distinct `ready_for_context` result; existing unconditional
`ready` must retain its current meaning. No conditional API/build path is currently
implemented. A future context must bind:

- Original and derived full hashes, analysis subject, native plan and predicates.
- Canonical execution mapping, supervisor state and relevant absolute bindings.
- An initial SP interval and the entire future stack envelope within owned storage.
- Current allowed caller/return ancestry and any consumed preexisting saved-An slot.
- Allowed interrupts and preservation of live pointer/binding/alias state.

The native proof must hold for every admitted state, not just captured register
values. Prefix summaries can describe candidate frame layouts; validating a current
frame does not prove the integrity of its history. A saved A6 slot can contain an
audio/custom-register base even when the current IRQ A6 is the application base.

The runner must validate every required predicate before each affected instruction,
including direct references without a LEA producer. It must arm all required guards
before releasing HAND, stop on missing/uncertain guards or violations, and prohibit
uncontrolled timeout/continue paths. A breakpoint temporarily removed for stepping
must not permit reentry or an interrupt to bypass another required guard. Interrupt
register saves/restores and callback effects need native preservation proof; later
use-point snapshots alone do not prove that an escaped saved pointer was harmless.
If Copperline cannot supply the required before-execution guarantee, the runtime
must refuse that contract. Such experiments remain conditional scenario evidence.

## Completion gate

Close the five native roots with independently reviewed address/frame evidence,
then use the normal verified build operation for all seven rewrites. Revalidate
the manifest, reserve destination storage before HAND, and compare reset, keys
11/12 press/release and gameplay against the original baseline, checking both new
storage and old-address guards. Preserve original expanded/compact exact assembly,
all existing facts/assets and append-only interpretation/review history.

## Bounded Pandora volume CPU comparison: generated width gap

The separate two-byte master-volume experiment has a closed relocation manifest
and normal execution evidence for both WORD writers. Normal BYTE reachability
remains unobserved. A verified rifle checkpoint and tighter camera timing remove
repeated acquisition/model uncertainty, but its return encounters failed ID
clearance (source `$887C`, HP95→44). Another valid ID/trade quest is deliberately
outside this bounded relocation comparison; the gameplay path is not declared
impossible or complete.

Before expanding that route, the local CPU tool validates the manifest and a
canonical checkpoint donor, projects original/derived code into separate local
memories, and keeps modeled call/guard inputs separate from Copperline. Direct
entry at the manifest BYTE store agrees for every initial 16-bit word. This is
an instruction contract, not guard reachability, full-routine equivalence,
allocation proof or Paula/DMA behavior. The partial result exits 2 and preserves
its refusal rather than accepting equality under a bad CPU model.

The attempted full routine exposes a general tooling gap. The KB already says
`size_by_ea_category: register=l, memory=b` for bit operations. The generated
concrete operand binding does not carry this rule to effective-width selection:
`sim_effective_operand_width` in `src/m68k_simulator.c` falls back to longword
for absent IR size. BTST/BCLR concrete reads/writes consume that width, although
bit-mask selection separately knows a memory destination has an eight-bit bit
index. The observed shared-flag BCLR write spans four bytes instead of one.
Original/derived equality under that behavior cannot qualify the routine.
The checked report accepts no routine cases, including the captured natural
case. No target predicate or native CPU implementation was edited to bypass it.

The next framework slice must bind the existing KB EA-category rule upstream
into generated operand semantics, then use one consistent effective width for
concrete reads/writes, EA update and flag semantics. Add positive and conservative
regressions for register versus memory, immediate versus dynamic bit index,
postincrement/predecrement and adjacent-byte guards/CCR, checked against an
independent CPU oracle where available. Re-extract only if an actual source/KB
fact is missing; do not encode Pandora addresses or duplicate instruction facts
in a handwritten runtime switch. Retry the same provenance-bound local cases
only after this fix. A general generator/runtime change and unavailable local
machine68k oracle are outside this bounded two-byte validation slice, so the
missing capability remains explicit rather than hidden behind a target shim.

See `runtime/observations/pandora-volume-local-comparison.json` and
`docs/copperline-runtime.md` for the scoped result, donor and reproduction.
No local result upgrades the two-of-three normal game writer coverage.

### Width repair and subsequent arithmetic refusal

The width gap is repaired in the authoritative parser/binding path. An EA
operand with a PDF-derived `size_by_ea_category` rule now uses normalized
`width_source: ea_category`; generated form metadata carries both category
widths. The runtime resolves the decoded category for reads, writes and EA
updates. Bit-index/flag selection consumes the same generated widths; the old
independent register-long/memory-byte width helper is removed. The concrete bit
path now calls the existing predecrement preparation helper before accessing its
operand, exposed by the new focused matrix. This adds no instruction facts or
target-address cases to CPU semantics.

The extraction facts were already correct, so only execution metadata was
regenerated from the preserved PDF-backed KB fields. Reproduce that bounded
stage without a fresh PDF parse (the regression checks the resulting bindings):

```sh
.venv/bin/python - <<'PY'
import copy, json, sys
from pathlib import Path
sys.path.insert(0, 'src/scripts')
from kb.m68k_parser import apply_execution_metadata
from generate_c99_assembler_corpus import _item_forms
path = Path('knowledge/m68k_instructions.json')
kb = json.loads(path.read_text())
for entry in kb['instructions']:
    if not entry.get('size_by_ea_category'):
        continue
    expanded = copy.deepcopy(entry)
    expanded['forms'] = _item_forms(kb, entry)
    apply_execution_metadata([expanded])
    entry['execution'] = expanded['execution']
path.write_text(json.dumps(kb, indent=2, ensure_ascii=False))
PY
.venv/bin/python src/scripts/generate_c99_simulator_subset.py
make -j4 all
```

Only eight destination bindings change (four operations, two forms), alongside
regenerated simulator tables. Focused tests prove regeneration reproduces those
bindings, modified category data drives emitted widths, missing category data
refuses generation, and committed tables match fresh generation. Native tests
cover 64 combinations of four bit operations, immediate/dynamic index,
register/indirect/postincrement/predecrement destination and old bit value;
all untouched neighbours and non-Z flags are preserved. Abstract tests exercise
32 corresponding register/indirect combinations and byte access footprints.

The original/derived comparison is rerun against the same donor and complete
manifest. Eight cases satisfy bounded local contracts and normalized state,
control-flow and write equivalence. In particular, five modeled dead/armed
calls execute the guard, reset helper and BYTE store and return normally.
The 65,536-word direct-store result is byte-for-byte unchanged. The old negative
receipt is retained; the new result is
`runtime/observations/pandora-volume-local-comparison-width-fixed.json`.

A different valid form now exposes the next concrete CPU capability gap. The
alive/near case executes source `$55310`, `subi.w #840,d0` (bytes `04400348`).
With D0 `$00070328` and SR `$2000`, its concrete direct-register arithmetic
branch yields `$0006ffe0` and unchanged SR instead of the word-preserving
`$0007ffe0` and SR `$2019`. The BPL therefore skips the NEG required for absolute
distance, producing volume 64 instead of53. The abstract arithmetic path already
uses width-aware arithmetic and flag helpers; concrete direct-register ADD/SUB
currently adds a full-register delta and omits data-arithmetic CCR updates.

This arithmetic repair is intentionally outside the requested generated
bit-width slice. The next general framework fix must preserve narrow Dn upper
bits, update data-arithmetic CCR from existing generated rules, preserve An
semantics and signed source extension, and cover immediate/register/quick and
signed/unsigned/wrapping boundaries with an independent oracle when available.
Do not mask the gap by choosing only coordinates that avoid negative deltas.
The comparison reports `refused_local_routine_contract`, continues independent
cases and exits 2 even when both layouts agree on the bad result. Whole-routine
coverage therefore remains bounded and partial, not a general equivalence proof.
Normal game BYTE reachability is still separate and unobserved; clearance-ID
route expansion remains paused.

### Concrete arithmetic gap closed for the bounded comparison

The arithmetic defect described above is fixed at the existing general concrete
execution layer. Its direct-register shortcut ignored data widths and CCR; the
replacement reuses normalized operand evaluation, source extension, arithmetic,
sized writes and generated CCR formulas. Dn/memory destinations use their
access widths; An destinations retain full-register results and unchanged SR.
Existing EA preparation/update helpers preserve pre/post addressing behavior.
No instruction-name/address exception or new M68K fact is added.

A minimal regression was red before the fix (`04400348`, D0 `$00070328` → bad
`$0006ffe0`) and now verifies the correct `$0007ffe0`/SR `$2019`. Explicit
byte/word/long boundary vectors exercise N/Z/V/C/X, carry/borrow and signed
limits, preservation of all other SR bits, all untouched D/A registers and
memory bytes, quick amounts 1/8, memory access boundaries, source extension and
An wrapping. Invalid accesses stop without completed instructions/writes; a
prepared EA register update is not promised to roll back. These tests use
generated assembly and explicit expected results. An independent machine68k
oracle remains unavailable, so this is not claimed as independent CPU proof.

The matrix also uncovered a valid reversed-form binding gap: changing a base
register operand into an EA did not change register-read/write access into EA
access. `_form_adjusted_access_kind` now normalizes both directions. Rebuilding
the normal execution-metadata stage from the existing extracted KB fields
changes exactly seven access kinds in five instructions: ADD/AND/OR/SUB and
three PMOVE forms. The simulator tables are regenerated; other instruction
facts, encodings and generated assembler/disassembler tables are unchanged.
PMOVE remains unsupported by concrete execution where previously unsupported.
The generator tests reproduce these bindings and verify conservative category
handling; concrete AND/OR memory cases cover the shared normalization.

For this metadata refresh, use the previous preserved-KB regeneration recipe
with the selection `if 'execution' not in entry: continue` in place of the
EA-category-only selection, then regenerate simulator tables and rebuild.
Only the seven documented access kinds change. Generator freshness and parser
reproduction regressions enforce the resulting artifacts.

The same verified donor and complete five-rewrite relocation manifest now admit
all nine bounded local calls. Near-player arming avoids audio initialization,
executes both absolute-distance NEG instructions and returns volume 53 in 21
steps. The five modeled dead/armed BYTE calls return in 26 steps per layout;
all normalized states, writes and control paths match. The 65,536-word direct
store result is unchanged. The new arithmetic-fixed receipt preserves earlier
refusals as history, reports no refused cases, and the CLI exits 0. Those are
bounded modeled CPU-call equivalence results. Normal game BYTE reachability,
Paula/DMA behavior, arbitrary contexts, interrupts and allocation proof remain
separate; clearance-ID gameplay remains paused.

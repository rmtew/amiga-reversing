# Runtime memory relocation proof

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
The twelve-byte `camera_scroll_profiles` table is another bounded CPU-only data
family (two three-WORD records), with additional PC-indexed access, caller/index
and pointer-lifetime obligations. The camera candidate is not a ready plan, and slicing
the keyboard buffer does not remove its indexed writers or inherited aliases.

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

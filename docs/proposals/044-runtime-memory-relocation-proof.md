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

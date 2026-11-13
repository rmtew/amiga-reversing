# Starglider II: linked releases and ST startup

The catalog in `games/starglider2.json` connects the existing Amiga restoration
with the supplied Atari ST release. It records byte identities, private input
sources, the checked recovery recipe, target load contexts and accepted range
matches. It contains no game bytes or machine-specific input paths.

## Use the linked targets

Build the native tools with `make`. Use Python 3.14 for the commands below.
Bind the supplied ZIP once; replace the path with its local path:

```sh
python -m amiga_reversing.tools.game_catalog --family starglider2 bind \
  --artifact 6a25ccb01084c666241556e5f98fdfec260415bd9ca259ac688fddcaf99a2d22 \
  --path '/path/to/Starglider 2 (1988)(Rainbird).zip'
python -m amiga_reversing.tools.game_catalog --family starglider2 inspect
python -m amiga_reversing.tools.game_catalog --family starglider2 materialize \
  --artifact 20c19400180d7e846b78aa615b68446293f8ca54015c4f4a42a77f03b24e8260
```

The last command runs the original loader instructions through the bounded
native CPU witness. It checks the recipe and each output identity. Sibling
outputs enter the private cache together, so opening a second view does not
run the decoders again. Derived artifacts cannot override their recipe with a
private file binding. Cache corruption and changed recipe identities cause an
error. Private paths and bytes stay under ignored `.amiga_reversing` state.

Open either target through the normal project browser and restoration service:

| Target | Input and load context |
| --- | --- |
| `atari_st_starglider2_main` | 419,308 bytes at `$1000`; entry `$1000`; actual ST handoff |
| `atari_st_starglider2_main_pre_handoff` | Same range before the loader changes the entry flags |
| `amiga_raw_starglider2_game` | Existing Amiga target and its authoritative source history |

The loader changes the WORD at `$1002` from `$8000` to `$0001`. These are two
content identities and two analysis contexts. Do not transfer startup assumptions
between them. The release label comes from the recovered header: version 1.05,
1 September 1988. The supplied filename does not authenticate an original release.

Project details and corpus entries show the family, release and artifact phase.
Browsing a target with missing private media does not start recovery. Existing
Amiga source and decompression records remain authoritative; the catalog refers
to them. A full migration of the older disk/decompression schemas remains open.

## Bounded startup evidence

`tests/test_starglider2_linked_startup.py` executes the actual ST handoff image,
from `$1000` to `$10D6`. It permits only the observed writes and refuses unknown
reads, unknown instruction bytes or other writes. With unrelated registers seeded
with `$DEADBEEF`, the original code takes 26,025 instructions to reach the stop.
It stores `$61668` at `$27BE`, clears exactly `$6598` bytes from that workspace,
and leaves A0 at `$67C00` and A7 at `$3386`.

The stop is before the first platform helper. This proves this startup slice;
it does not prove ST hardware initialization, display output or a normal FDC boot.
The separate [loader recovery](starglider2-st-loader-recovery.md) explains which
physical sector instances supplied the image and how the decoders were checked.

The normal restoration command batch names the entry flags, initializer, clear
loop and workspace pointer from this evidence. These names describe observed
purpose. They do not claim that the whole workspace layout has been recovered.

## Accepted cross-platform matches

Offsets below are payload file offsets. Both payloads are mapped at `$1000`.
The catalog binds each range to its target, complete artifact identity and range
hash. A byte search proposes a match only when there is one occurrence. Naming
still requires interpretation of the code or data and its references.

| Match | Amiga offset | ST offset | Size | Evidence |
| --- | --- | --- | --- | --- |
| `shared_prng_step` | `$1662` | `$1676` | 28 bytes | Identical instructions; 15 native ST references; isolated state-contract test |
| `game_over_message_pair` | `$074A` | `$0766` | 52 bytes | Two adjacent terminated game-over strings; one native ST reference to each |

The random step reads two LONGs at A6+`$60` and A6+`$64`. It rotates the first
LONG left by three bits, subtracts seven from its low WORD, and XORs that WORD
with the second state's low WORD. It shifts the old second state into the first
slot, writes the result to the second slot and D0, and preserves D1. The witness
runs the original instructions from both payloads with boundary and ordinary
state values and compares them with that arithmetic contract. It supplies the
same isolated A6 layout; it does not establish every live caller's A6 value.

The strings are `POWER DRAINAGE TOO GREAT!` and `ICARUS DESTROYED!`, including
the original spacing and terminators. Their unique correspondence supports the
ST message names. These small matches do not transfer the Amiga application
structure or platform code wholesale.

```sh
python -m amiga_reversing.tools.game_catalog --family starglider2 verify-links
SGII_LINKED_FIXTURES=1 python -m pytest tests/test_starglider2_linked_startup.py -q
```

The Amiga target's private source must also be available for these comparisons.
Its existing source binding is used by default. A rebuilt original image may be
bound with the catalog's `bind` command only if its size and complete identity
match the existing Amiga artifact.

## Encoded novella check: why `$15350` was not ST code

The raw handoff analysis followed a jump to `$152F2`. The stored bytes there
looked like `BPL $1534E`, which led to a coincidental scaled-index instruction at
`$15350`. That instruction was not evidence of a 68020 requirement.

The original setup at `$1F0E` identifies the range `$131E0..$155C8` and the
incrementing LONG key `$32597635`. The loop at `$1F28` subtracts that key. The
original rotation loop at `$1F60` rotates the first WORD of each LONG left twice
and the second right three times. The source-bound recipe
`targets/atari_st_starglider2_stx/protection_plan.json` executes these instructions
with writes restricted to the declared range. It uses 6,901 instructions for the
subtraction, six to replay the original address/count setup, and 13,788 for the
rotation. The setup replay supplies no invented register values.

This reconstructs 9,192 bytes of novella word-check records, prompts and code.
A further 576 original bytes provide unchanged helper context. The separate
`atari_st_starglider2_protection_view` target maps those 9,768 bytes at `$131E0`,
with entry `$152F2` and phase `decoded_snapshot`. It is an analysis view, not a
replacement game image. The recipe reconstructs a conditional decode state; it
does not prove that normal ST startup reached the word check. Hardware and helper
returns outside the captured range remain separate questions.

The decoded entry selects English, German or French, initializes three attempts,
then chooses and checks a novella word. Original consumers multiply accepted
selectors by 16. They read three coordinate BYTEs, then a terminated answer from
the remaining 13 bytes. All physical records satisfy that layout:

| Language | Record base | Physical records | Accepted selector count |
| --- | --- | --- | --- |
| English | `$131E0` | 163 | 147 |
| German | `$13C10` | 129 | 128 |
| French | `$14420` | 133 | 130 |

The extra stored records are not claimed reachable through these selectors.
`SG2NovellaWordRecord`, the three arrays, the entry and all directly referenced
language prompts are recorded through the normal restoration commands. The
later original integrity comparison expects WORD `$6100` at `$15330`; the
reconstructed view has exactly that value.

The parent now classifies this range as `novella_protection_encoded`. Its bytes
are unchanged. Both the native assembler and independent **68000** vasm build
reproduce all 419,308 parent bytes exactly. The seven previously pending names,
the encoded range and its two decoder-loop labels are accepted against that
strict verification. All 24 decoded-view actions also have an exact strict
verification and review. The rendered ST view source is committed in its target
directory. It is generated from the facts, not edited separately. The existing
macro exporter falls back to ordinary directives for the 13-byte answer field;
this does not change the data or prevent exact assembly.

`novella_english_instructions` adds a third qualified cross-platform match. It
connects 273 identical bytes in the existing Amiga decoded view at file offset
`$AD9` to the ST decoded view at `$1D75`, from the English heading through the
sentence about exhausted attempts. The match is unique in both views. It does
not assume that the two full word tables, language sets or routines are identical.
The existing Amiga view and its provenance remain unchanged.

```sh
python -m amiga_reversing.tools.game_catalog --family starglider2 materialize \
  --artifact 9be0a7243fce8c7202abb71271994f4f3ef654c15c559f9e1868c86f9c67082d
SGII_LINKED_FIXTURES=1 python -m pytest tests/test_starglider2_linked_startup.py -q
```

The catalog now accepts the shared `mapped_cpu_recovery` derivation for ordinary
source artifacts. It uses the same closed load/run/capture executor as STX
recovery. Input ranges retain source offsets; undeclared writes, missing input
bytes, register injection and wrong output identities are refused. No second
arithmetic decoder or private mutation path is needed for the ST view.

## Validation and remaining work

Native regressions cover exact row identities and platform-specific naming.
Those fixes and raw Atari reproduction remain covered. Mapped-recipe tests cover
source ranges, input identity, action bounds and catalog materialization. Private
SGII tests compare both original-instruction stages with an independent scalar
formula, check the unchanged helper tail and all 425 records, and verify the
qualified English correspondence. Original selector instructions are also run
with first/last valid and first/maximum invalid values for each language,
including unrelated upper register bits. The supplied media and recovered binaries are
not committed.

This slice does not resume unrelated Amiga reconstruction. Remaining milestones
include wider ST startup analysis, normal ST hardware boot, more qualified
correspondences, the broader source-schema migration and a generated shared-source
package that builds both original payloads. There is no hand-maintained common
assembly tree and no claim that either restoration is complete from byte equality.

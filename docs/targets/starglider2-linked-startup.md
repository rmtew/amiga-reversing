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

## Validation and remaining work

The native C renderer and assembler plus independent vasm must reproduce the ST
handoff payload exactly before the naming batch is accepted. The native C build is byte-exact for
all 419,308 bytes. Independent vasm with `-m68020 -no-opt -Fbin` also reproduces
the full payload exactly. This is a lossless encoding check, not ST CPU proof.
The standard `-m68000` oracle currently rejects a speculative instruction at
runtime `$15350`: `movea.w -$6C(a3,a7.l*8),a1`. Its scaled index needs a later
CPU. This unresolved region must be classified or the target CPU legality
contract improved before that gate can pass. The seven naming actions remain
unreviewed; no successful strict verification receipt is claimed.

Full-source validation exposed two
general framework issues: a label and instruction at one coordinate were confused
when validating evidence, and Amiga hardware/LVO symbols could leak into an Atari
analysis. Native tests cover exact row identities and platform-specific naming.
The fixes use the shared native analysis and restoration boundaries. Raw Atari
reproduction also now uses the existing flat-byte comparison and Atari includes,
rather than the PRG container comparison.

This slice does not resume unrelated Amiga reconstruction. Remaining milestones
include wider ST startup analysis, normal ST hardware boot, more qualified
correspondences, the broader source-schema migration and a generated shared-source
package that builds both original payloads. There is no hand-maintained common
assembly tree and no claim that either restoration is complete from byte equality.

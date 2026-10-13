# Typed structures, pointer domains, and optional source macros

## Baseline and problem

The Pandora audit at `5845c83b` inspected 439 bound layouts and 33 custom
structure types. It found 1,057 explicit schema pointers: 416 null, 613 named,
27 with generated names, and one nonnull field interrupted by a required
source boundary. No complete nonnull explicit pointer remained numeric.

Another 1,171 pointer-named scalar fields contained 153 nulls, 497 numeric
longwords, 520 byte rows, and one interrupted field. Names are candidates,
not proof of pointer semantics. A separate selector check found 30 known
absolute script pointers, eight audio cursor candidates requiring further
family evidence, and 66 correctly excluded packed scalar pairs.

The 318 graphics records already had valid canonical bindings. Their two
longword fields were nevertheless declared scalar. An independent projection
bug required four-byte alignment for LONG, so their 18-byte stride alternated
between `dc.l` and four `dc.b` values. The 68000 permits a longword at an even
address. Correcting directive emission and assigning pointer semantics are
separate changes; neither requires inventing new instance layouts.

## Canonical contract

Structure definitions and instance bindings remain the sole typing model.
Pointer semantics must be explicit in that definition. A pointer's encoded
value and canonical source identity are different coordinates, especially in
copied execution views. Resolution must use the existing view facts and reject
conflicting mappings, rather than subtract a game-specific load address.

Generated RAM pointers need a separate address domain. A bounded runtime
address symbol can describe a proven bank base and extent without pretending
that the RAM occupies bytes in the original file, that it contains a particular
structure, or that an EQU allocates storage. Namespace qualification prevents
unrelated banks from resolving a field. An interior reference can render as
`bank+$offset`; it does not need a new fact or EQU for every value.

The graphics evidence supports 59 disjoint constructor write extents totaling
43,160 bytes and 318 image/mask pairs. All images match existing physical
owners, with 49 at named bases and 269 inside those owners. All mask pointers
fall inside generated banks, and image offsets equal four times mask offsets.
The shifted clipping path can read before a nominal frame. These facts do not
establish every DMA read extent, lifetime, later writer, or phase alias.

The ordinary schema-edit and EQU commands persist these rules once. Bound-field
projection and native rendering apply them to every existing instance; no
per-instance pointer annotation is needed for the proved family. The ordinary
restoration query and UI **Pointer exceptions** button summarize the whole
population and page only unresolved/invalid fields when requested. This is the
reversing productivity improvement; compact macro output is a separate choice.
No token or time speedup is claimed without measurement.

Nulls remain zero. Other sentinel or tagged values require explicit schema or
consumer evidence. Plausible addresses, pointer-like names, and comments do not
authorize bulk promotion. A bulk report must distinguish resolved, null,
unmapped, conflicting, unsupported, and interrupted fields. Remaining scalar
families require their own consumer and variant review.

## Optional macro view

A structure macro is an alternative serialization of already resolved fields.
It must derive its directives, field order, widths, and documentation from the
same canonical schema as expanded output. Arguments reuse the resolved native
expressions. There is no independent macro definition or per-instance fact
store. Expanded source remains available and is the default.

Compact output is useful for uniform records with a small number of fields:
one invocation makes an image/mask/dimensions record easier to scan. It is less
useful for large, conditional, overlapping, or partially understood records.
Interior labels and unsupported layouts require an explicit expanded fallback;
symbols must never disappear just to obtain compact output. Macros introduce
no implicit padding or stronger alignment.

The baseline probe assembled an 18-byte, seven-field Devpac-style positional
macro with vasm, exactly matching its expanded form. The baseline native
assembler rejected `Frame18 macro`, while the expanded control succeeded.
Therefore native expansion support is required before claiming that emitted
macro artifacts pass the project's two-assembler verification. Vasm syntax
compatibility is not a test using the original Devpac assembler.

## Verification boundaries

Focused regression tests must cover even and odd field addresses, view/domain
separation, ambiguous or absent mappings, nulls, owner offsets, symbol encoding,
atomic refusal, and macro fallback. Both native C and vasm must assemble the
actual emitted expanded and macro artifacts. Comparing only an expanded
reference would miss incorrect macro definitions or argument order.

Full exact reassembly establishes the original bytes, directive widths,
symbol values, and ordering. It does not prove pointer meaning, uniform pointee
extent, lifetime, reachability, or relocatability. Fixed RAM and hardware
addresses remain fixed; macros alone do not make an absolute game relocatable.

## Implementation results

The framework upgrade is implemented through the existing catalog, Manual
Action Log, native projection, restoration API and UI. Three schema edits and
59 constructor-bank facts automatically resolve **666 bound fields**: 318 image
pointers, 318 generated-mask pointers and 30 script pointers. There are **zero
per-instance pointer actions**. Another 59 ordinary representation actions name
the decoded constructor destinations, preserving their forced-long encodings.
The 121 new facts passed independent review and were accepted through two
revision-bound `review_batch` calls (100 and 21), using the full-image receipt.
This measures annotation actions avoided; it does not measure elapsed time or
LLM token savings.

The ordinary `typed_pointers` API now reports 1,723 explicit bound pointer
fields: 1,306 symbolic, 415 null, and two unresolved boundary fragments at
`$49030` and `$49134`. The graphics and script families have zero exceptions.
A Chromium check loaded the actual target, observed 121 visible listing rows,
and clicked **Pointer exceptions**, displaying both exceptions and the full
population counts. Initial hydration of this 41,616-row target took roughly
30 seconds in this environment. The service runs on loopback port 8123; no
public hosting was configured.

The actual second musician frame now emits these expressions in expanded
source, with its other five WORD fields kept in canonical order:

```asm
dc.l scene_pixel_cells_for_mask_bank_42+$1F0
dc.l scene_mask_bank_42+$7C
```

Opt-in compact package output emits the same frame as:

```asm
STRUCT_WorldPositionAnimationFrame_8606c611 musician_frames_4870E_1,1,scene_pixel_cells_for_mask_bank_42+$1F0,scene_mask_bank_42+$7C,$0002,$001F,$0020,$0000,$0000
```

Both the expanded source and the actual exported compact ZIP reproduce all
376,832 original bytes through **native C and independent vasm**, with SHA256
`70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f`.
The expanded verification receipt is
`a3e5d87c032e8c2e5898d047757bf4f7f9738ef0b5ef736dae93edc22ae297fa`;
its source SHA256 is
`00fa1b127c413024e2a953f8bb4b0624a1baa18a048bb02672be726a502781b4`.
The compact source SHA256 is
`28699143d1716c4fbe308fa0beccde55d92af13688d50f84f8e7a4d36c1e42de`.
The package contains source, 68 assets, nine SDK includes and its manifest.
All 77 pre-existing companions retain their original hashes; both historical
MAL and DJ prefixes are preserved. Canonical counts remain 439 layouts,
33 types, 60 summaries and 114 comments. Equates increase to 213 and
representations to 1,773.

Compact export selects 1,920 custom-structure records: 27 derived definitions
compact 1,283 records; 637 records retain expanded output. Its 453 fallback
groups report overlap/boundary (1), noncanonical interior label (6), package
span not uniquely identifiable (281), more than nine positional arguments (76),
and schema gaps/overlaps/unsupported fields (89). These are group counts,
not record counts. SDK bindings and unrelated layouts are outside this selector.
Original Devpac was **not run**; macro export currently supports the vasm
profile only. The C parser expands the bounded supported macro subset and
leaves the SDK include scanner intact.

Validation includes 134 consolidated focused Python tests, four explicit HTTP
source-export route integration tests, the native IR fixtures, Ruff on changed
Python files and JavaScript syntax checks. Additional domain-focused tests
exercise actual C/vasm artifacts, ambiguity, unsigned bounds and atomic refusal;
their counts overlap the consolidated run and must not be added to it.

Remaining work is explicit: the two required pointer-boundary fragments,
27 generated semantic names, and 535 pointer-named scalar candidates (153 zero,
382 nonzero) need further family-specific evidence. Eight audio cursor candidates
remain outside the promoted families. A matching symbolic expression does not
prove pointee type, RAM lifetime, relocatability or all clipped DMA accesses.
No new runtime probe was needed for this framework change.

## Reproduction

Use the existing Python 3.14 environment and native toolchain in this checkout:

```sh
make -j4
.venv/bin/python -m amiga_reversing.tools.disasm_server --host 127.0.0.1 --port 8123
```

Open
`http://127.0.0.1:8123/amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`.
The server must be ready before invoking revision-bound restoration operations.
In another terminal:

```sh
TARGET=amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8
.venv/bin/python -m amiga_reversing.tools.restoration --target "$TARGET" state
.venv/bin/python -m amiga_reversing.tools.typed_pointer_report --target "$TARGET" --summary
.venv/bin/python -m amiga_reversing.tools.source_export "$TARGET" --structure-macros --binary-assets --verify-package --output /tmp/pandora-compact.zip --json
.venv/bin/python -m pytest -q tests/test_typed_long_emission.py tests/test_absolute_operand_symbol_catalog.py tests/test_structure_macros.py tests/test_typed_pointer_domains.py tests/test_typed_pointer_report.py tests/test_restoration_operations.py tests/test_restoration_interfaces.py tests/test_source_export.py
```

For an API exception page, copy the current `revision` from `state`:

```sh
.venv/bin/python -m amiga_reversing.tools.restoration --target "$TARGET" query --kind typed_pointers --exceptions-only --limit 25 --expected-revision CURRENT_REVISION
```

Evidence is retained locally under
`.runtime-state/pandora-analysis/connected-5845c83b/upgrade/`, including the
requests, native reports, two assembler verifications, independent review,
preservation proof, browser result and bounded test/build logs. Runtime state
and temporary compact packages are not required repository deliverables.

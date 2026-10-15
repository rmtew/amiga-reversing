# Pandora preserved unpacked tail

The initial investigation started from published `358a085b` and was recorded
at `ffae9904`, without changing tail bytes or classifications. The subsequent
canonical correction and asset restoration are described below.

The parent `pandora` hunk's original ByteKiller header at section offset `$E8`
contains `$0002E23C,$0005C000,$23F12ECD`: packed stream extent, declared unpacked
size, and checksum. Its code sets output A1 to `$20000`, decompresses backwards
through A2, checks the checksum and jumps to `$20000`. The import manifest records
this derived target as ByteKiller output, 376,832 bytes, load/entry `$20000`.
Thus this tail is part of the declared decompressed payload, not merely disk
sectors appended by the importer. Whether it was deliberately retained fill,
prepacking memory residue or meaningful data requires further evidence; the
repeated bytes alone do not identify its author or purpose.

The child bootstrap copies only source `[0,$55370)` to `$10000`, then enters
`$1046A`. The full raw image is assembled under the materialized `$10000` view;
that presentation does not prove the remaining bytes were copied there. In the
original unpacked `$20000` view, the tail resides at `$75370..$7C000`. The same
file offsets appear as `$65370..$6C000` in the generated source. The first cursor
DMA buffer is runtime `$65370`, immediately beyond the copied prefix. Its LEAs
are workspace references, not proof that the noncopied file tail initializes it.
The generated `ORG $10000` is a reconstruction address view, not the original
unpacker destination.

Source `[ $55370,$55400 )` contains 144 bytes after the final RTS; the following
27,648 bytes `[ $55400,$5C000 )` are four-byte records. Every record begins
`44 6F`; the third byte is one of `53,57,5B`; its fourth byte counts `00..FF`
every 1 KiB. All of these checks use the original binary, not rendered text.
No game role is inferred from the pattern.

The orphan `abs_0_0006AFFA` has canonical source offset `$5AFFA`, with zero
recorded symbol origins and no corresponding manual label/entrypoint. Previous
native evidence already records the inconsistency: the instruction at source
`$576` is `4E B9 00 05 AF FA`; an operand reference used target offset `$5AFFA`,
whereas the native CFG resolves the call correctly to source `$4AFFA` (runtime
`$5AFFA` in the copied image). That function is now named
`initialize_player_and_fixed_animation_nodes`. The orphan's `$6AFFA` spelling
is the rendered `$10000` view applied to the stray source target `$5AFFA`.
It falls two bytes into a patterned record. It is a generated declaration from
inconsistent address/reference projection, not evidence of a function there.
The saved canonical evidence is `resource-next/{symbols-tail,tail-refs,
tail-consumer,tail-edge}.json` under ignored analysis storage. Zero origins limit
how precisely the original label-production event can be attributed; avoid
claiming a manually seeded label or deleting a fact without tracing its producer.

The inspected fixed-copy route excludes the tail; the parent unpack route
materializes it at its original address. No additional consumer has been
established. This is not proof that no indirect, disk or alternate entry route
can consume it. A full ownership/lifetime or all-load-path claim remains open.

Recommended canonical presentation: preserve all 27,792 bytes as an opaque
binary asset, provisionally named `unpacked_tail_not_in_fixed_copy` (with the
144-byte prefix and patterned body documented separately). Use normal data
range/layout and binary-asset output commands, keeping the original source
extent, and verify exact C/vasm reconstruction. First correct or explicitly
retain the orphan boundary through the normal native reference/label pipeline;
do not hand-delete the label or edit generated assembly. Do not call the bytes
unused, free RAM, disk padding or relocatable storage on current evidence.

## Canonical correction and preservation

The producer is now traced: the render-plan symbol-access stage attached the
raw decode candidate's target after the instruction operand had already resolved
the copied execution view. It now uses that resolved coordinate for the call,
xref and required declaration. No manual tail label or unexplained original
bytes were deleted. The old renderer fails the new copied-bootstrap regression;
the corrected renderer removes the phantom declaration and remains byte-exact.

The new general source-symbol representation identity carries native section,
source offset, rendered address view and encoded value. Its locked preflight
checks the native literal and width before append; rendering resolves the name
by identity. Pandora's tile-bank subtraction at `$9302` exercises this path
without introducing a duplicate equate.

The incoming-source-reference query initially also exposed two runtime EQU
values at `$77D00` and `$77FE0`. Their references remain named, but are no longer
misreported as source-byte targets solely through numeric coincidence. These
workspace addresses overlap the original unpacked tail window, so later reuse
of the same RAM must remain distinct from reading its initial payload contents.
The now-empty direct source-reference query still does not prove absence of
indirect consumers or alternate routes.

The tail is preserved through a normal `opaque_data` layout and raw element as
`preserved_uncopied_payload_tail`: one asset for source `$55370..$5C000`, retaining
the 144-byte prefix and the separately documented patterned body. The new opaque
asset capability keeps the existing native boundary/expression/fixup guards;
unclassified bytes do not become assets automatically. This provisional name
means excluded from the inspected fixed-copy path. It is not a claim of unused
storage, original fill purpose, exclusive ownership or relocation safety.

The final native-boundary fix preserves the retained analysis labels while using
only planned declarations as source rendering boundaries. The old unbounded
blitter rename was inspected and left unchanged; it was not the asset blocker.
Final asset SHA256:
`3fb12746fa5b4e89048231415d5173d571633dffcc89d15d926ce7a3dc0eb1ba`.
Full C/vasm receipt:
`0c11b57ba11fc0b92b6f84e360120cd3463aac16b314fef724d9b3b832bdd0b2`.
See `pandora-tail-asset.json` for the canonical range, native queries and
preservation/source-size audit. The original image remains unchanged.

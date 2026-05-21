# Classic Mac OS Targets

The committed Classic Mac OS example target is:

```text
targets/macos_hfs_mpw_gm/
  .project.json
  targets/macos_file_mpw_tools_asm/
    .project.json
    asm.s
```

`macos_hfs_mpw_gm` represents `resources/platform_macos/MPW-GM.img.bin`.
The subtarget `macos_file_mpw_tools_asm` represents the HFS file
`MPW-GM/MPW/Tools/Asm`.

`asm.s` is an illustrative source-quality artifact generated from the durable
C-backed HFS/resource/CODE summary plus the Mac CODE listing adapter over the
shared m68k analysis renderer. It is not an MPW Asm/Link/Rez round-trip
contract.

The header records Finder type/creator, HFS path, data/resource fork hashes,
resource type counts, `CODE 0` jump-table metadata, all known `CODE` resources,
CODE resource coverage status rows, non-CODE resource placeholders, and
unsupported Segment Loader/runtime areas. The body renders the selected
`CODE 1 Main` bytes as Mac-facing m68k listing rows with HFS/resource/range
provenance. Other CODE resources are explicitly marked metadata-only, partial,
or deferred with concrete reasons until full per-resource expansion has
relocation/source-boundary context.

Manual/progress facts should only be committed here when they describe durable
Mac semantic progress. Timestamp-only project state and cosmetic source churn
are not accepted target progress.

Regeneration is checked by `tests/test_macos_target_artifact.py`; if the
C-backed renderer changes, update `asm.s` through
`python -m amiga_reversing.disasm.macos_target_artifact --write` and review the
diff for source-quality changes before committing.

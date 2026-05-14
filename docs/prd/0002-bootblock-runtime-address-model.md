# PRD 0002: Bootblock Runtime Address Model

## Problem Statement

Bootblock targets are still rendered as if the extracted bootblock source bytes are an absolute `$70000` program. This contradicts the raw target descriptor's `local_offset` model and makes `ORG $70000` appear as a source-level runtime view even when no internal bootstrap has proven that view. It obscures real bootblock behavior, weakens browsing, and leaves downstream bootstraps such as `DoIO` reads and low-memory copies under-modeled.

## Solution

Make bootblock analysis keep storage offsets, boot ROM load addresses, and proven runtime views separate. Bootblock metadata should seed the boot entry, structured boot header fields, and entry register context, but it should not materialize a full `$70000` ORG range for a `local_offset` raw target. ORG/runtime views should only be emitted for proven internal copies, reads, relocations, or bootstrap handoffs that provide source bytes, destination address, size, and entrypoint evidence.

## User Stories

1. As a reverse engineer, I want bootblock source rendered at local offsets by default, so that the listing reflects the extracted bootblock bytes.
2. As a reverse engineer, I want bootblock load metadata kept separate from source ORG rendering, so that `$70000` does not masquerade as proven source layout.
3. As a reverse engineer, I want the boot entry labeled from bootblock metadata, so that the real entry point remains easy to find.
4. As a reverse engineer, I want boot magic, checksum, and root block fields rendered as structured data, so that the bootblock header remains readable.
5. As a reverse engineer, I want `A6` seeded as ExecBase at boot entry, so that Exec calls are named correctly.
6. As a reverse engineer, I want `A1` seeded as the boot IO request at boot entry, so that trackdisk request setup can be understood.
7. As a reverse engineer, I want `IOStdReq` field writes rendered symbolically, so that `DoIO` setup is readable instead of raw offsets.
8. As a reverse engineer, I want saved boot IO request pointers propagated through local storage slots, so that type knowledge survives simple save/load patterns.
9. As a reverse engineer, I want `CMD_READ` setup recognized from typed IO fields, so that disk reads become analysis facts.
10. As a reverse engineer, I want read destination addresses recorded as runtime memory ranges, so that loaded stages become navigable.
11. As a reverse engineer, I want read length and disk offset recovered from IO setup when possible, so that materialized child stages are byte-accurate.
12. As a reverse engineer, I want bootstrap memory copies recognized after reads, so that copied low-memory payloads are not left as raw absolute literals.
13. As a reverse engineer, I want copied runtime ranges to emit ORG only when backed by source bytes and entry evidence, so that ORG stays meaningful.
14. As a reverse engineer, I want absolute handoff targets symbolized when backed by a runtime range, so that `jsr` and `jmp` targets are browseable.
15. As a reverse engineer, I want weak low-memory addresses kept as numeric or equate symbols, so that temporary trampolines do not produce false ORGs.
16. As a reverse engineer, I want bootblock-stage children created only from concrete bytes, so that inferred-only regions are not presented as real targets.
17. As a reverse engineer, I want the Epic bootblock to render without `ORG $70000`, so that the known regression is fixed.
18. As a reverse engineer, I want the Epic bootblock `DoIO` request setup to use IO field names, so that the loader behavior is self-explanatory.
19. As a reverse engineer, I want the Epic `$1E200` read and `$864` bootstrap copy modeled, so that the real later-stage entrypoints are visible.
20. As a reverse engineer, I want target browsing to distinguish source offsets from runtime addresses, so that navigation does not imply false provenance.
21. As a reverse engineer, I want runtime-view comments or memory-map rows to show why a range was or was not materialized, so that analysis decisions are auditable.
22. As a reverse engineer, I want exact round-trip reproduction preserved, so that better labels and ORG decisions do not change bytes.
23. As a maintainer, I want bootblock policy rules centralized, so that import metadata, analysis policy, and rendering do not disagree.
24. As a maintainer, I want `local_offset` raw sources to remain local unless explicitly promoted by proven runtime evidence, so that the address model contract stays stable.
25. As a maintainer, I want `runtime_absolute` raw sources to keep their current single load range behavior, so that real loaded child payloads do not regress.
26. As a maintainer, I want bootblock metadata parsing to seed facts without overriding the raw source address model, so that metadata cannot silently force ORG.
27. As a maintainer, I want IO request type propagation tested independently, so that future platform-structure work can reuse it.
28. As a maintainer, I want disk-read inference tested independently, so that stage materialization can depend on a small, stable interface.
29. As a maintainer, I want runtime-copy materialization tests to cover false-positive suppression, so that weak bootstrap hints do not create noisy ORGs.
30. As a maintainer, I want existing real-target regressions pinned, so that Epic and similar bootblocks stay fixed.

## Implementation Decisions

1. Treat bootblock load address as provenance and execution context, not automatic source ORG evidence.
2. Keep the raw source address model authoritative. `local_offset` means entry analysis uses local offsets unless a separate runtime view is proven.
3. Preserve current `runtime_absolute` raw target behavior: one policy runtime range covers the source payload and one runtime entrypoint marks the transfer address.
4. Change bootblock metadata ingestion so it adds boot entry, boot header structured data, and entry register seeds without adding a full bootblock runtime range for local-offset sources.
5. Add an explicit way for analysis policy to represent bootblock environment load context without forcing materialized ORG output.
6. Keep ORG emission governed by runtime-view evidence: source bytes, destination range, extent, entrypoint or handoff, accepted code, and no stronger conflict.
7. Model boot IO request setup through existing platform structure knowledge rather than target-specific hardcoding.
8. Propagate register type facts through simple local storage save/load patterns when the storage address is proven and unambiguous.
9. Recognize `DoIO` disk reads from typed IO request fields, including command, offset, length, and data destination when available.
10. Feed concrete disk-read outputs into the existing child target materialization path only when bytes can be sliced from the parent disk image.
11. Represent post-read memory copies as runtime-copy candidates, then materialize only when source bytes, destination, length, and entry evidence are sufficient.
12. Symbolize proven absolute runtime destinations with runtime labels or equates even when ORG is suppressed.
13. Avoid adding target-local special cases for Epic. Epic should be a regression fixture for general bootblock behavior.
14. Keep bootblock regression work in the C analysis and rendering path, not in generated source patches.
15. Do not mutate original binaries. Rebuilt or materialized outputs remain generated artifacts.

## Testing Decisions

1. Tests should assert external behavior: effective policy, rendered source text, analysis facts, materialized child targets, and round-trip bytes.
2. Add or update a real-target test proving the Epic bootblock no longer emits `ORG $70000`.
3. Keep the existing real-target test proving Epic's copied runtime destination remains separate from load ORG, but change the expected load behavior.
4. Add a narrow local-offset raw bootblock fixture proving bootblock metadata seeds the entry and header fields without creating a runtime range.
5. Keep the runtime-absolute raw target fixture proving loaded child payloads still emit their single ORG.
6. Add IO request propagation fixtures covering register seed, save to local storage, reload, field writes, and `DoIO`.
7. Add disk-read inference fixtures that verify destination, length, disk offset, and command facts from typed IO setup.
8. Add runtime-copy fixtures covering `$source -> destination` copy, entry handoff, materialized ORG, and suppressed weak low-memory trampoline.
9. Add negative tests where bootblock metadata has a load address but no proven copy or handoff, and assert no source-level ORG.
10. Run round-trip reproduction for affected real targets and require exact rebuilt bytes where source output is regenerated.
11. Good tests should avoid internal implementation details and check stable observable contracts: policy JSON, listing source, memory-layout records, and materialized target descriptors.

## Issues

1. [0002-001 Stop Bootblock Load Address From Emitting ORG](../issues/0002-001-stop-bootblock-load-org.md)
2. [0002-002 Symbolize Boot IO Request Setup](../issues/0002-002-symbolize-boot-io-request-setup.md)
3. [0002-003 Materialize Bootblock Disk Read Stages](../issues/0002-003-materialize-bootblock-disk-read-stages.md)
4. [0002-004 Materialize Post-Read Runtime Copy Handoffs](../issues/0002-004-materialize-post-read-runtime-copy-handoffs.md)

## Out of Scope

1. Full WinUAE or emulator-guided tracing.
2. Custom raw-track decoding beyond currently materialized bytes.
3. General packer/decruncher identification.
4. Broad UI navigation redesign for runtime-address search.
5. Hardware register propagation unrelated to bootblock IO and bootstrap flow.
6. Fixing unrelated Bloodwych, Pandora, Damocles, or assembler coverage TODOs.
7. Manual review workflow changes.

## Further Notes

1. Status: implemented.
2. This PRD follows the existing rule that ORG is for proven source-level runtime views, not for hiding missing analysis.
3. The first implementation slice should remove the false bootblock `$70000` ORG while preserving boot entry and header rendering.
4. The second slice should improve IO request field symbolization and `DoIO` read inference.
5. The third slice should materialize concrete read/copy/handoff boot stages such as the Epic `$1E200 -> $864` path.

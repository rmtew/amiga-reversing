# Proposal 039: Corpus Build Observability, Resource Discipline, and Analysis Coverage

Status: Complete — 2026-07-28.

## Problem

The full `target_usage_manifest build` path is the normal way to regenerate
the indexed corpus. A fresh run requested eight workers, but showed sustained
single-process CPU work and large transient private-memory growth (roughly
5.5 GiB during the observed run) before later collection released memory. It
also writes its artifacts only after the expensive analysis phase, so the
operator has no durable progress or phase information while waiting.

This is a corpus-tooling observability, resource-lifecycle, and coverage
concern. It is not evidence that the typed-pointer analysis is incorrect, and
it must not be worked around by silently analysing a smaller corpus,
publishing stale corpus artifacts as fresh, reducing scope, or adding
retry/fallback paths.

The Proposal 038 baseline also found zero emitted typed-pointer-store facts.
That does **not** mean the corpus contains no pointer writes. It means the
common corpus build has insufficient source-analysis coverage for this audit:
most executable inputs lack recovered typed destination contracts, and
reconstructed raw project targets such as Pandora are catalogued as project
metadata rather than passed through their normal source-analysis projection.
An audit cannot measure facts that its input model discards.

## Goal

Make a full indexed-corpus build predictably bounded, observable, and
meaningfully parallel where analysis permits it, while ensuring that every
analysable target contributes its normal source-analysis facts to the common
corpus. Preserve deterministic corpus facts and artifact schemas except where
a deliberate schema extension is required to carry previously omitted facts.

The solution must identify the actual expensive phases and memory owners,
then correct their ownership, lifetime, scheduling, or serialization. It must
not introduce a second reduced-fidelity analysis pipeline.

## Completion Evidence

A fresh full build was run with the normal corpus manifests and eight workers.
It completed 428 entries in 550.69 seconds: 319 file entries and 59 project
targets. The measured task-time utilisation was 5.19 for file analysis and
3.06 for project analysis, with eight active workers in both phases. Its OS
private-allocation high-water mark was 7,854,493,696 bytes. This is real
concurrent source analysis, not executor-only parallelism.

The build now gives every completed target a bounded lifetime: its row, xrefs,
and listing snippets are sorted and written to a private staging shard before
the next completed result is retained. Aggregate reports replay those shards
in stable target order. Final artifacts are completely prepared and checked in
a private directory before any canonical artifact is replaced; each published
file is an atomic replacement. Progress is an immutable numbered-snapshot
directory, so a reader can never lock a future writer's file. There is no
reduced input path, stale-artifact fallback, target exception, or retry path.

The one-worker and eight-worker full builds produced byte-identical SHA-256
hashes for the manifest, xrefs, snippet index/blob, variant index, type-flow
report, unresolved-field report, and coverage report. Both produced 428
entries, 3,842,359 xrefs, 601,480 snippet rows, 249 type-flow rows, and 68
unresolved typed-field rows.

The coverage report records 293 `source_analyzed`, 106 `catalog_only`, and
29 `analysis_failed` inputs with stable per-record source kind and reason.
Pandora's reconstructed raw-binary project targets are now source-analysed by
the same listing-artifact path as other supported project sources. The fresh
pointer-value audit consequently found 45 observed typed pointer stores in
Pandora (4 immediate and 41 propagated), making Proposal 038's corpus audit
measurable rather than structurally empty.

Focused corpus tests passed (`32 passed`): they cover progress metrics,
coverage categorisation, deterministic staging xrefs/snippets, and existing
corpus behavior. The full builds above validate the complete normal artifact
set.

## Investigation Required Before Design

Profile one representative full build with phase-level timing, item counts,
worker utilisation, and process memory high-water marks. Attribute time and
memory to concrete operations, including:

- input reconstruction and target discovery;
- C-backend analysis and any serialization lock or shared mutable state;
- listing/snippet extraction;
- xref and report construction;
- compression and artifact writes; and
- retained Python and C allocations between target analyses.

Also inventory corpus input kinds against the source-analysis paths available
to them. For each kind, establish whether the corpus receives only catalog
metadata or the same analysis facts, listing locators, and durable type
contracts available to a normal reconstructed target.

Establish whether the observed low parallelism is caused by the Python
executor, a backend lock, global backend state, allocator retention, or a
particular class of target. Do not assume that garbage collection, lower worker
counts, process restarts, or a larger machine is a fix.

## Required Design Properties

- Each target analysis has an explicit lifetime; per-target Python and C
  allocations are released when its derived rows have been emitted.
- Concurrency is real and measurable for independent targets, or a documented
  backend constraint is removed so it becomes real. A `--workers` setting must
  not merely create threads that serialize behind hidden shared state.
- Progress reports identify phase, completed/total targets, elapsed time,
  worker utilisation, and current/high-water memory without changing corpus
  contents.
- Every analysable reconstructed project target enters the common source
  analysis path. Its typed fields, pointer stores, and other durable analysis
  facts are represented with the same stable target and listing identity as
  executable corpus inputs.
- Inputs that genuinely cannot be source-analysed state that explicit reason
  in a stable coverage record; they are not silently represented as if their
  catalog metadata were analysis evidence.
- Output remains deterministic across worker counts, including stable row ids,
  ordering, compressed snippet indexes, and all existing report schemas.
- A failed build leaves no partially published corpus in the canonical output
  location. Atomic publication is allowed only after complete successful
  generation and validation.
- There are no reduced-corpus modes, stale-artifact fallbacks, silent retries,
  target-specific exclusions, or compatibility paths that conceal an
  incomplete build.

## Acceptance Criteria

- A reproducible profiling report names the dominant time and memory costs for
  a full corpus build and records the baseline command, corpus identity,
  machine-independent counts, elapsed time, and peak memory.
- The implemented lifecycle removes any identified retained per-target
  allocations and has focused regression coverage for the ownership boundary.
- A full build at a declared worker count demonstrates actual concurrent
  analysis when independent inputs exist, with measured utilisation and no
  correctness difference from a single-worker build.
- Full-build artifacts produced at one and multiple worker counts compare
  byte-for-byte where compression is deterministic, or compare by a specified
  deterministic semantic checksum where a format intentionally carries no
  byte-stability guarantee.
- Peak memory is bounded by the configured concurrency and measured input
  size, rather than monotonically retaining completed-target state.
- A coverage report identifies every corpus input kind, its analysis status,
  and the reason for any unavailable analysis. Reconstructed Pandora is
  included as a source-analysed target, not only a decompression/reproduction
  catalog row.
- A regenerated typed-pointer audit contains observed pointer-store rows when
  the underlying analysed targets have proven pointer destination contracts;
  an empty result is acceptable only when the coverage report proves there are
  no such contracts, not because a target class was omitted.
- Existing corpus-tool tests pass, and a fresh full build completes with all
  normal manifest, xref, snippet, variant, type-flow, and unresolved-field
  artifacts validated.

## Non-Goals

- Changing pointer propagation semantics, renderer behaviour, or target Manual
  Actions.
- Making an incomplete or selectively rebuilt corpus appear fresh.
- Replacing the corpus format solely to evade a measurable lifecycle problem.

## Relationship to Proposal 038

Proposal 038's typed-pointer corpus audit remains a separate, read-only
consumer of a fresh corpus. This proposal exists because the build that should
produce that baseline exposed a general framework performance concern. Complete
this work independently before resuming a full-corpus audit only if profiling
shows the current build cost prevents routine, reliable regeneration.

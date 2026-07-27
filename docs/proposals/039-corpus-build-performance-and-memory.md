# Proposal 039: Corpus Build Performance and Memory Discipline

Status: Deferred.

## Problem

The full `target_usage_manifest build` path is the normal way to regenerate
the indexed corpus. A fresh run requested eight workers, but showed sustained
single-process CPU work and large transient private-memory growth (roughly
5.5 GiB during the observed run) before later collection released memory. It
also writes its artifacts only after the expensive analysis phase, so the
operator has no durable progress or phase information while waiting.

This is a corpus-tooling performance and resource-lifecycle concern. It is
not evidence that the typed-pointer analysis is incorrect, and it must not be
worked around by silently analysing a smaller corpus, publishing stale corpus
artifacts as fresh, reducing scope, or adding retry/fallback paths.

## Goal

Make a full indexed-corpus build predictably bounded, observable, and
meaningfully parallel where analysis permits it, while preserving exactly the
same deterministic corpus facts and artifact schemas.

The solution must identify the actual expensive phases and memory owners,
then correct their ownership, lifetime, scheduling, or serialization. It must
not introduce a second reduced-fidelity analysis pipeline.

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
- Existing corpus-tool tests pass, and a fresh full build completes with all
  normal manifest, xref, snippet, variant, type-flow, and unresolved-field
  artifacts validated.

## Non-Goals

- Changing analysis facts, pointer propagation, renderer behaviour, or target
  Manual Actions.
- Making an incomplete or selectively rebuilt corpus appear fresh.
- Replacing the corpus format solely to evade a measurable lifecycle problem.

## Relationship to Proposal 038

Proposal 038's typed-pointer corpus audit remains a separate, read-only
consumer of a fresh corpus. This proposal exists because the build that should
produce that baseline exposed a general framework performance concern. Complete
this work independently before resuming a full-corpus audit only if profiling
shows the current build cost prevents routine, reliable regeneration.

# Shared source restoration operations

The product is progressively understandable, maintainable, byte-exact source.
UI, CLI and MCP operate the same target workflow; MCP is a transport adapter.

## Reviewed design

Independent architecture and migration review approved this design before major
implementation. Native facts remain authoritative. The Manual Action Log owns
manual source changes; the existing Decision Journal owns evidence decisions.
No separate restoration database, assembly scraping, or navigation-JSON trimming
layer is introduced.

1. Extend the resident native artifact with bounded queries for symbols,
   references, instructions, CFG edges and typed field uses. Return deterministic
   pages with explicit scope, provenance and unresolved cases. Function ownership
   remains derived from accepted CFG facts, never next-label extents.
2. Add one shared restoration domain service to the existing server. Its revision
   binds source/backend state and both histories. Cursors bind revision and
   filters. Mutations compare the exact revision under a target lock; stale
   locator recovery remains navigation behavior, not write authorization.
3. Preserve old JSONL bytes and unknown fields. New actions may carry evidence;
   missing evidence projects as legacy/unassessed. Decision status has one
   authority in the Decision Journal. Writes use cross-process target locking,
   full batch validation and atomic replacement. Corrections append history.
4. Separate the verification subject (source/backend and generating manual
   actions) from the concurrency revision (also decision history). Recording a
   result must not invalidate its own proof. Exact rebuild proves encoding, not
   interpretation. Probe questions, setup and outcomes bind to that subject;
   timeout means not observed under those conditions, not unreachable.
5. Expose compact discovery/inspection, interpretation, verification, probe and
   review/history through shared operations. UI and CLI use the existing HTTP
   process; a stdio MCP adapter uses the official SDK and the same operations.
   Retire overlapping old reference consumers after identifying callers; keep
   distinct navigation grouping functionality.

## Phases and acceptance

- Native queries and shared revision contract: bounded payloads, stable paging,
  explicit unknowns, stale-page and stale-write refusal.
- Safe histories and interpretation: preserve legacy names/comments/types and
  representations; concurrent writes cannot lose actions; correction/rollback
  remains visible and does not erase user history.
- Interfaces and verification: equivalent UI/HTTP/CLI/MCP results; actual MCP
  initialization/tools/calls; evidence visible in UI; exact rebuild and bounded
  probe receipts required only where relevant, not for every routine edit.
- Pandora demonstration: choose a connected source improvement from code facts,
  retrieve compact evidence, record interpretation, regenerate, rebuild exactly,
  run existing validated Copperline checkpoints and review the result. Measure
  against the prior 4.93 MB references and 101 KB/27-row responses. Independent
  final and migration review precede draft publication. No merge or tennis edits.

Known baseline fixture/provider failures remain explicit. Historical reports
remain historical evidence; active guidance must describe the implemented path.

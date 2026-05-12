# Advanced Arena Forms Stay Out of Production

Advanced arena forms from PRD005 do not move to production implementation now.

Evidence:

- `docs/arena-measurement-report.md`: current linked-block Arena is not a proven bottleneck.
  PRD001-004 already removed the largest raw temporary allocation clusters through explicit
  Workflow Arenas, Result Arenas, Scratch Marks, and Arena Builders.
- `docs/arena-virtual-reserved-prototype.md`: virtual reservation gives contiguous addresses and
  can reduce committed waste in one measured large transient case, but adds reserve/commit failure
  modes, platform-specific implementation work, and policy questions.
- `docs/arena-growable-pool-prototype.md`: a fixed-size pool beats plain arena allocation for a
  repeated same-size node workload, but only when objects need individual reuse inside a workflow.
  That is not currently a measured production hotspot.
- `docs/arena-scratch-frame-fit-analysis.md`: per-thread scratch arenas add hidden lifetime coupling,
  and frame/double-buffer arenas need a repeated workflow with a hard discard boundary that has not
  been measured as a bottleneck.

Decision:

- Keep the production allocator model as explicit linked-block Arena ownership.
- Continue using Result Arena for durable object/model outputs.
- Continue using Workflow Arena for operation-scoped temporary data.
- Continue using Scratch Marks for nested staging lifetimes.
- Continue using Arena Builder for append-and-flatten construction.
- Do not implement production virtual-reserved arenas, growable pools, per-thread scratch arenas, or
  frame/double-buffer arenas under PRD005.

No follow-up implementation PRD is opened. A future PRD may revisit one advanced form only with a
specific measured workflow bottleneck and a rollback plan. Until then, prototypes remain test-only or
documentation-only evidence.

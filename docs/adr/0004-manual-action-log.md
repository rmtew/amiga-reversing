# Manual Action Log For User Review State

Manual review state is stored as an ordered per-target action log rather than separate mutable current-state files. Replaying the log projects the current Manual Seeds and Manual Resolutions, which preserves user action order, supports undo and redo through compensating actions, and lets regenerated Manual Review Items be matched against prior resolutions without making generated review items the durable source of truth.

The tradeoff is that readers must project state before analysis instead of reading a single current-state object, but this keeps manual intervention auditable and avoids stale stored review queues after analysis improves.

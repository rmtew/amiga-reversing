# C Arena Ownership

C internals use explicit lifetime ownership for workflow-temporary memory and result-object memory instead of ad hoc `malloc`/`free` ownership.

Repository-owned APIs should name the lifetime role they need:

- workflow-temporary data belongs to a Workflow Arena, often through a Workflow Context when a top-level operation needs more than an arena
- nested temporary data uses Scratch Marks on the current Workflow Arena
- persistent result internals belong to a Result Arena, caller-provided arena, or model-owned arena
- plain caller-freed buffers remain only at Python, CLI, or public C API edges that genuinely need standalone text or bytes

Generic heap-backed allocator facades are not an acceptable production ownership model. They hide `malloc/free` without answering the lifetime question. Existing heap-backed allocator facade call sites should be removed in focused ownership clusters, with each cluster moved to an explicit workflow, result, model, or public-edge output contract.

The repository is the only consumer of its C APIs, so internal and local C interfaces may change to make ownership explicit; compatibility or fallback paths are avoided because they preserve old lifetime complexity.

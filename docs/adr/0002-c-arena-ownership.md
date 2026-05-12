# C Arena Ownership

C internals use explicit arena ownership for workflow-temporary memory and result-object memory instead of ad hoc `malloc`/`free` ownership. The repository is the only consumer of its C APIs, so internal and local C interfaces may change to make ownership explicit; compatibility or fallback paths are avoided because they preserve the old lifetime complexity. Plain caller-freed buffers remain only where a Python or CLI edge genuinely needs standalone text or bytes.

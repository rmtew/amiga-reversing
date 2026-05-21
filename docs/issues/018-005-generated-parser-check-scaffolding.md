Status: open
Source proposal: docs/proposals/018-platform-executable-format-knowledge.md

Scope:
Generate or validate parser/check scaffolding from executable-format KB records.

Acceptance criteria:
- C parser output can be checked against KB-defined regions and metadata.
- Standard code/data/bss/reloc/symbol enumeration is tested per platform.
- Generated checks fail when parser output contradicts cited platform facts.

Blocked by:
- 018-001.
- At least one platform record from 018-002, 018-003, or 018-004.

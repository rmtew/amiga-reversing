Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Reconcile the Proposal 012 current-state text with the implemented starter
milestone.

Problem:
The proposal still listed several starter paths as "Still absent" after issues
012-005 through 012-010 implemented generated Mac OS runtime tables, reusable
resource/CODE parsing, MPW `Asm` container import, and the starter web payload.
That stale section made the next work queue look broader than the actual
remaining gaps and obscured the real deferred boundary: full Mac target
lifecycle creation, Segment Loader relocation/fixups, and byte-for-byte
roundtrip.

Acceptance:
- The proposal status reflects the implemented starter milestone.
- Implemented paths are no longer listed as absent.
- Deferred work is stated as future/out-of-scope rather than a current starter
  blocker.
- Issue 012-009 is marked implemented in the issue breakdown seed.

Result:
- Proposal 012 now separates implemented starter support from explicit deferred
  work and records that this closeout was a documentation-state fix, not a new
  importer or UI feature.

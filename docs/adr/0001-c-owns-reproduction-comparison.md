# C Owns Reproduction Comparison

Reproduction comparison is C-owned because it depends on platform container facts such as Amiga HUNK relocation records and Atari ST PRG layout, while Python owns round-trip verification orchestration, reporting, and UI row mapping. The C interface should be generic through a reproduction comparison context with normalized policy fields and typed internal results; status, diagnostic, policy, and layout kinds are enum ids or bitflags rather than text. JSON is only a DLL boundary transport for the local Python caller, and Python maps ids to text at output edges. There is no compatibility layer, adapter fallback, or second Python implementation: unsupported comparison cases fail simply, and migrated Python platform-comparison code is deleted.

C result shapes should remain compact, simple, and efficient. They should not be made verbose for Python-facing convenience; Python expands ids and bitflags into report and UI labels.

Loader-owned object metadata records container layout and recognized container encoding details needed to reproduce non-standard shape with the same content. Project rebuilds use that metadata to preserve recognized original container shape by default; reproduction comparison verifies and reports rather than being the steady-state place for post-hoc byte adjustment. Unrecognized container variation is reported as container feedback while preserving content comparison, rather than being collapsed into a content mismatch. Existing semantic-exactness wording should be retired in favour of full-file exactness, content exactness, and container-shape diagnostics.

Project rebuild derives assembler policy from loader metadata in C. The default requested result is full-file exactness; target policy may explicitly accept content exactness for known container limitations. Policy divergence and unsupported container shape are reported distinctly.

The steady-state round-trip path is direct C project rebuild plus C reproduction comparison. Source-text assembly remains only a debug or comparison mode; the direct C path should become the default and only normal path once migration is complete.

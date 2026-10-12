# Native comment write contract and scalable storage

## Implemented boundary

The shared Manual Action Log append service validates changed effective manual
entry comments before its atomic history write. Undo and redo use the same
projected-state comparison. Removing or replacing invalid legacy text remains
possible; unchanged legacy text is not revalidated during unrelated actions.

Native exports report the text capacity from
`sizeof(M68kAnalysisEntryComment.comment) - 1` and the policy count capacity from
`M68K_ANALYSIS_ENTRY_COMMENT_LIMIT`. Python stores no duplicate numeric limits.
The validator parses the exact JSON string representation used by effective
metadata with `json_string_value_local`, then compares it with the requested
UTF-8 text. Oversized or lossy text is refused before persistence. The current
metadata codec strips escape prefixes rather than decoding Unicode/control
escapes; Unicode escapes, newlines, tabs, NUL and invalid Unicode are therefore
unsupported here until the shared codec is repaired. Quotes and backslashes
that survive the codec are accepted.

The active manual-comment count check is a conservative boundary, **not a full
native policy capacity guarantee**. Seeded entry-point/label comments,
generated declarations and other metadata also consume the native policy's
entry-comment collection. A combined-policy preflight must use the actual
effective metadata and native policy builder before claiming total capacity
coverage. Direct metadata writers and other comment-bearing fact kinds remain
outside this narrow Manual Action Log guard.

## Storage migration proposal (not implemented)

Full-project documentation should use a heap-owned growable entry-comment
vector and an owned UTF-8 string arena, with explicit byte lengths or stable
string handles. It should not enlarge inline arrays or policy stack frames.
Keep address/section identity on each entry and deterministic insertion order;
retain the existing duplicate and suppression semantics.

Migration requires explicit allocation-failure handling and ownership in
`m68k_analysis_policy_init_default`/`m68k_analysis_policy_destroy`, an audit of
policy copies and stack-allocated policies, widening the current `uint16_t`
count, and removing count-limit bounds from policy validation/JSON/render loops.
Metadata entry-point, label and comment readers currently use fixed text
buffers. Render lookup instruction comments use a separate 384-byte inline
buffer, and assembly rendering has additional fixed scratch buffers. Those
paths must either borrow arena strings or compose into dynamic builders, so
long text is preserved through parsing, lookup, source IR and final assembly.
The source IR already represents comments as `char *`, making it a useful
downstream ownership boundary. Repair the shared JSON decoder with Unicode,
control-character and surrogate-pair tests before enabling arbitrary UTF-8.

Validate the migration with total seeded/manual/generated capacity tests,
long-comment rendering and exact-byte round trips, deletion/undo/redo,
allocation-failure cleanup and memory diagnostics. Existing history and native
metadata identity must remain stable.

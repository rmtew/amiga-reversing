# Optional schema-derived structure macro export

`structure_macros=true` is an opt-in vasm source-export presentation. Expanded
canonical source and accepted facts remain the default. The option composes with
the existing binary-assets package projection; INCBIN bytes and provenance stay
unchanged. Macro definitions and invocations are in the actual exported source,
which must assemble through both the C assembler and vasm.

Types, field order, sizes, record count, stride and ownership come exclusively
from effective canonical `custom_structs` and `data_block_layouts` bindings.
Native plan rows/subline source ranges establish exact field boundaries. The
renderer copies already rendered numeric or symbolic expressions as arguments;
comments and source spellings never establish typing. Native canonical spans
must agree with source bytes. Package projection additionally requires one exact
occurrence of the selected native block. No independent schema or fact store is
created.

Definitions document field names, offsets, sizes and positional argument order.
Canonical generated field labels are retained as prefix/index substitutions
inside the macro at their original byte positions. The public instance label
remains outside the first invocation. This preserves symbol and section identity
without introducing numeric EQU aliases. Meaningful extra field annotations are
retained beside the invocation; canonical field-name comments are documented once
in the definition.

The initial supported shape is a complete flat contiguous schema whose fields
are single BYTE/WORD/LONG directives with one literal or symbolic expression.
Exact arrays may use the schema size as stride. The assembler supports at most
nine positional arguments: nine fields without label arguments, eight with a
prefix, seven with an array prefix and index. Padding, overlapping fields,
inherited/nested schemas, noncanonical interior labels, interior directives,
ambiguous native spans, unsupported expressions or argument limits retain the
original expanded source. Fallbacks are reported, never forced compact.

The initial selection is custom-structure bindings only; platform structures and
other element types remain expanded and do not count as candidates or fallbacks.
The response identifies this selection and its `candidate_record_count`, plus
definition/instance counts, `fallback_record_count`,
`fallback_group_count`, reason counts and at most 100 detailed fallback groups.
`fallback_count` aliases the record count; groups whose invalid record count
cannot be established are counted separately as `fallback_unknown_count_groups`.

The C assembler's bounded source-local macro subset accepts `name MACRO`,
`ENDM`, and positional substitutions `\1` through `\9` outside quoted strings
and comments. Definitions precede invocations; invocation labels are separate
source lines. Arguments split on commas outside quotes and parentheses. Nested
invocations, recursion, conditional/repetition directives, local/unique labels
and other assembler metaprogramming are unsupported when invoked. Unused complex
definitions do not change output. SDK INCLUDE scanning keeps its existing
behavior and does not expand SDK macro definitions. Source and expanded output
are bounded at 64 MiB, lines at 8191 bytes and definitions at 128.

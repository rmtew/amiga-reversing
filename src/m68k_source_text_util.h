#ifndef M68K_SOURCE_TEXT_UTIL_H
#define M68K_SOURCE_TEXT_UTIL_H

#include "m68k_object.h"

#include <stddef.h>

char *m68k_trim_in_place(char *text);
void m68k_strip_comment_in_place(char *line);
size_t m68k_split_delimited_in_place(char *text, char delimiter, char **parts,
                                     size_t max_parts);
char *m68k_next_token_in_place(char **text);
int m68k_split_operands_in_place(char *text, char **operands,
                                 size_t max_operands, size_t *out_count);

void m68k_normalize_zero_base_displacement_in_place(char *text);
int m68k_is_elided_lea_noop(const char *line_text);
int m68k_rewrite_cmp_zero_to_tst(const char *line_text, char *out_text, size_t out_text_size);
char m68k_requested_size_suffix_from_text(const char *line_text);
int m68k_parse_section_kind(const char *text, M68kSectionKind *out_kind);
char *m68k_find_label_delimiter(char *text);

#endif

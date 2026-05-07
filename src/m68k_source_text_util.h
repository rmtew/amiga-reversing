#ifndef M68K_SOURCE_TEXT_UTIL_H
#define M68K_SOURCE_TEXT_UTIL_H

#include "m68k_object.h"

#include <stddef.h>
#include <stdint.h>

char *m68k_trim_in_place(char *text);
void m68k_strip_comment_in_place(char *line);
size_t m68k_split_delimited_in_place(char *text, char delimiter, char **parts,
                                     size_t max_parts);
char *m68k_next_token_in_place(char **text);
int m68k_split_operands_in_place(char *text, char **operands,
                                 size_t max_operands, size_t *out_count);

char m68k_requested_size_suffix_from_text(const char *line_text);
int m68k_parse_section_kind(const char *text, M68kSectionKind *out_kind);
int m68k_parse_section_spec(const char *text, M68kSectionKind *out_kind, uint8_t *out_platform_mem_type,
                            uint32_t *out_platform_mem_attrs);
int m68k_format_section_spec(M68kSectionKind kind, uint8_t platform_mem_type, uint32_t platform_mem_attrs,
                             char *out_text, size_t out_text_size);
char *m68k_find_label_delimiter(char *text);

#endif

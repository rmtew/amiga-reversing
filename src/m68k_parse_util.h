#ifndef M68K_PARSE_UTIL_H
#define M68K_PARSE_UTIL_H

#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

uint32_t m68k_sign_extend32(uint32_t value, unsigned bits);
int m68k_appendf(char *buffer, size_t buffer_size, const char *format, ...);
int m68k_lower_copy(char *out, size_t out_size, const char *text);

int m68k_text_uses_short_branch_suffix(const char *text);
int m68k_is_symbol_name(const char *text);
void m68k_normalize_register_alias_tokens_in_place(char *text);
void m68k_normalize_pc_current_expr_in_place(char *text);
int m68k_parse_number_u32(const char *text, uint32_t *out_value);
int m68k_parse_register_token(const char *text, char prefix, uint8_t *out_reg);
int m68k_parse_register_pair_token(const char *text, char first_prefix, char second_prefix, uint8_t *out_reg,
  uint8_t *out_pair_reg);
int m68k_parse_rn_pair_token(const char *text, uint8_t *out_reg, uint8_t *out_pair_reg,
  uint8_t *out_reg_is_address, uint8_t *out_pair_reg_is_address);
int m68k_parse_control_register_token(const char *text, uint8_t target_cpu, uint8_t *out_id, uint32_t *out_value);
int m68k_parse_cpu_name(const char *text, uint8_t *out_cpu);
int m68k_set_bounded_string(char *dest, size_t dest_size, const char *value);
int m68k_parse_render_policy_option(int argc, char **argv, int *io_argi,
  M68kRenderPolicy *policy, char *error_buf, size_t error_buf_size);

#endif

#ifndef M68K_PARSE_UTIL_H
#define M68K_PARSE_UTIL_H

#include "m68k_diagnostics.h"
#include "m68k_ir.h"

#include <stddef.h>
#include <stdint.h>

typedef enum M68kSourceDirectiveToken {
  M68K_SOURCE_DIRECTIVE_NONE = 0,
  M68K_SOURCE_DIRECTIVE_INCLUDE,
  M68K_SOURCE_DIRECTIVE_EQU,
  M68K_SOURCE_DIRECTIVE_SET,
  M68K_SOURCE_DIRECTIVE_SECTION,
  M68K_SOURCE_DIRECTIVE_EVEN,
  M68K_SOURCE_DIRECTIVE_END,
  M68K_SOURCE_DIRECTIVE_COMMENT,
  M68K_SOURCE_DIRECTIVE_MACRO,
  M68K_SOURCE_DIRECTIVE_ENDM,
  M68K_SOURCE_DIRECTIVE_IFND,
  M68K_SOURCE_DIRECTIVE_IFC,
  M68K_SOURCE_DIRECTIVE_IFNC,
  M68K_SOURCE_DIRECTIVE_ENDC,
  M68K_SOURCE_DIRECTIVE_STRUCTURE,
  M68K_SOURCE_DIRECTIVE_STRUCT,
  M68K_SOURCE_DIRECTIVE_LABEL,
  M68K_SOURCE_DIRECTIVE_BYTE,
  M68K_SOURCE_DIRECTIVE_UBYTE,
  M68K_SOURCE_DIRECTIVE_WORD,
  M68K_SOURCE_DIRECTIVE_UWORD,
  M68K_SOURCE_DIRECTIVE_BOOL,
  M68K_SOURCE_DIRECTIVE_SHORT,
  M68K_SOURCE_DIRECTIVE_USHORT,
  M68K_SOURCE_DIRECTIVE_RPTR,
  M68K_SOURCE_DIRECTIVE_LONG,
  M68K_SOURCE_DIRECTIVE_ULONG,
  M68K_SOURCE_DIRECTIVE_FLOAT,
  M68K_SOURCE_DIRECTIVE_FPU,
  M68K_SOURCE_DIRECTIVE_APTR,
  M68K_SOURCE_DIRECTIVE_BPTR,
  M68K_SOURCE_DIRECTIVE_BSTR,
  M68K_SOURCE_DIRECTIVE_CPTR,
  M68K_SOURCE_DIRECTIVE_FPTR,
  M68K_SOURCE_DIRECTIVE_DOUBLE,
  M68K_SOURCE_DIRECTIVE_ALIGNWORD,
  M68K_SOURCE_DIRECTIVE_ALIGNLONG,
  M68K_SOURCE_DIRECTIVE_BITDEF,
  M68K_SOURCE_DIRECTIVE_LIBINIT,
  M68K_SOURCE_DIRECTIVE_LIBDEF,
  M68K_SOURCE_DIRECTIVE_LIBENT,
  M68K_SOURCE_DIRECTIVE_DEVINIT,
  M68K_SOURCE_DIRECTIVE_DEVCMD,
  M68K_SOURCE_DIRECTIVE_ENUM,
  M68K_SOURCE_DIRECTIVE_EITEM,
  M68K_SOURCE_DIRECTIVE_DC_B,
  M68K_SOURCE_DIRECTIVE_DC_W,
  M68K_SOURCE_DIRECTIVE_DC_L,
  M68K_SOURCE_DIRECTIVE_DCB_B,
  M68K_SOURCE_DIRECTIVE_DCB_W,
  M68K_SOURCE_DIRECTIVE_DCB_L,
  M68K_SOURCE_DIRECTIVE_DS_B,
  M68K_SOURCE_DIRECTIVE_RSSET,
  M68K_SOURCE_DIRECTIVE_RS_B,
  M68K_SOURCE_DIRECTIVE_RS_W,
  M68K_SOURCE_DIRECTIVE_RS_L
} M68kSourceDirectiveToken;

typedef struct M68kParseMnemonicResult {
  uint8_t mnemonic_id;
  char size_suffix;
} M68kParseMnemonicResult;

typedef struct M68kParseU32Result {
  uint8_t ok;
  uint32_t value;
} M68kParseU32Result;

typedef struct M68kParseRegisterResult {
  uint8_t ok;
  uint8_t reg;
  uint8_t pair_reg;
  uint8_t reg_is_address;
  uint8_t pair_reg_is_address;
} M68kParseRegisterResult;

typedef struct M68kParseControlRegisterResult {
  uint8_t ok;
  uint8_t id;
  uint32_t value;
} M68kParseControlRegisterResult;

typedef struct M68kParseDataDirectiveResult {
  uint8_t ok;
  uint8_t width_bytes;
  uint8_t is_repeat;
} M68kParseDataDirectiveResult;

typedef struct M68kParseOffsetDirectiveResult {
  uint8_t ok;
  uint32_t delta;
} M68kParseOffsetDirectiveResult;

typedef struct M68kParseCpuResult {
  uint8_t ok;
  uint8_t cpu;
} M68kParseCpuResult;

uint32_t m68k_sign_extend32(uint32_t value, unsigned bits);
unsigned m68k_popcount16(uint16_t value);
int m68k_appendf(char *buffer, size_t buffer_size, const char *format, ...);
int m68k_lower_copy(char *out, size_t out_size, const char *text);
int m68k_ascii_equal_ci(const char *left, const char *right);
int m68k_ascii_prefix_equal_ci(const char *text, const char *prefix);
M68kParseMnemonicResult m68k_parse_mnemonic_token(const char *token);
uint8_t m68k_parse_special_register_token(const char *text);
M68kParseU32Result m68k_parse_cache_selector_token(const char *text);
M68kSourceDirectiveToken m68k_parse_source_directive_token(const char *text);
M68kParseDataDirectiveResult m68k_parse_data_directive_token(M68kSourceDirectiveToken token);
M68kParseOffsetDirectiveResult m68k_parse_offset_directive_token(M68kSourceDirectiveToken token);

int m68k_text_uses_short_branch_suffix(const char *text);
int m68k_is_symbol_name(const char *text);
void m68k_normalize_register_alias_tokens_in_place(char *text);
void m68k_normalize_pc_current_expr_in_place(char *text);
M68kParseU32Result m68k_parse_number_u32(const char *text);
M68kParseRegisterResult m68k_parse_register_token(const char *text, char prefix);
M68kParseRegisterResult m68k_parse_register_pair_token(const char *text, char first_prefix, char second_prefix);
M68kParseRegisterResult m68k_parse_rn_pair_token(const char *text);
M68kParseControlRegisterResult m68k_parse_control_register_token(const char *text, uint8_t target_cpu);
M68kParseCpuResult m68k_parse_cpu_name(const char *text);
int m68k_set_bounded_string(char *dest, size_t dest_size, const char *value);
int m68k_parse_render_policy_option(int argc, char **argv, int *io_argi,
  M68kRenderPolicy *policy, M68kDiagSink diagnostics);

#endif

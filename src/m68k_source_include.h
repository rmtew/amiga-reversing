#ifndef M68K_SOURCE_INCLUDE_H
#define M68K_SOURCE_INCLUDE_H

#include <stddef.h>
#include <stdint.h>

typedef struct M68kSourceIncludeState {
    int inside_macro_definition;
    struct {
        int parent_active;
        int this_active;
    } conditionals[64];
    size_t conditional_count;
    char include_dir[512];
} M68kSourceIncludeState;

typedef int (*M68kSourceIncludeLookupFn)(const char *name, uint32_t *out_value, int require_constant, void *user_data);
typedef int (*M68kSourceIncludeSetConstantFn)(const char *name, uint32_t value, int allow_redefine, void *user_data);
typedef int (*M68kSourceIncludeParseConstantFn)(const char *text, uint32_t *out_value, void *user_data);

typedef struct M68kSourceIncludeContext {
    void *user_data;
    M68kSourceIncludeLookupFn lookup_defined;
    M68kSourceIncludeSetConstantFn set_constant;
    M68kSourceIncludeParseConstantFn parse_constant;
} M68kSourceIncludeContext;

void m68k_source_include_state_init(M68kSourceIncludeState *state, const char *include_dir);
int m68k_source_include_process_file(const M68kSourceIncludeContext *context, M68kSourceIncludeState *state,
    const char *path, char *out_error, size_t out_error_size);

#endif

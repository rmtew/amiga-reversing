#include "m68k_source_macro.h"
#include "m68k_source_text_util.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#define MACRO_LIMIT 128U
#define LINE_LIMIT 8192U
#define OUTPUT_LIMIT (64U * 1024U * 1024U)
typedef struct Buffer { char *text; size_t size, capacity; } Buffer;
typedef struct Macro { char name[96]; Buffer body; } Macro;

static int append(Buffer *buffer, const char *text, size_t size) {
  size_t capacity; char *grown;
  if (size > OUTPUT_LIMIT - buffer->size) return 0;
  if (buffer->size + size + 1U > buffer->capacity) {
    capacity = buffer->capacity ? buffer->capacity : 1024U;
    while (capacity < buffer->size + size + 1U) capacity *= 2U;
    grown = (char *)realloc(buffer->text, capacity);
    if (!grown) return 0;
    buffer->text = grown; buffer->capacity = capacity;
  }
  memcpy(buffer->text + buffer->size, text, size); buffer->size += size;
  buffer->text[buffer->size] = '\0'; return 1;
}
static int same(const char *left, const char *right) {
  while (*left && *right && tolower((unsigned char)*left) == tolower((unsigned char)*right)) { ++left; ++right; }
  return !*left && !*right;
}
static int name_valid(const char *name) {
  if (!isalpha((unsigned char)*name) && *name != '_') return 0;
  while (*++name) if (!isalnum((unsigned char)*name) && *name != '_') return 0;
  return 1;
}
static Macro *find(Macro *macros, size_t count, const char *name) {
  size_t index; for (index = 0U; index < count; ++index) if (same(macros[index].name, name)) return &macros[index];
  return NULL;
}
static int arguments(char *text, char **args, size_t *count) {
  char *start = text, quote = '\0'; unsigned depth = 0U;
  *count = 0U; text = m68k_trim_in_place(text); start = text;
  if (!*text) return 1;
  for (;;) {
    char ch = *text;
    if (!quote && ((!depth && ch == ',') || !ch)) {
      if (depth || *count == 9U) return 0;
      *text = '\0'; args[(*count)++] = m68k_trim_in_place(start);
      if (!*args[*count - 1U]) return 0;
      if (!ch) return 1;
      start = text + 1;
    } else if (ch == quote) quote = '\0';
    else if (!quote && (ch == '\'' || ch == '"')) quote = ch;
    else if (!quote && ch == '(') ++depth;
    else if (!quote && ch == ')') { if (!depth) return 0; --depth; }
    if (!ch) return 0;
    ++text;
  }
}
static int expand_body(const Macro *macro, char **args, size_t count, Buffer *output,
    Macro *macros, size_t macro_count) {
  const char *cursor = macro->body.text ? macro->body.text : "";
  size_t highest = 0U; char quote = '\0'; int comment = 0;
  Buffer body = {0};
  while (*cursor) {
    char ch = *cursor++;
    if (!quote && !comment && ch == '\\') {
      unsigned argument = (unsigned)(*cursor - '0');
      if (argument < 1U || argument > 9U || argument > count) goto failed;
      ++cursor;
      if (isdigit((unsigned char)*cursor)) goto failed;
      if (argument > highest) highest = argument;
      if (!append(&body, args[argument - 1U], strlen(args[argument - 1U]))) goto failed;
      continue;
    }
    if (!comment && ch == quote) quote = '\0';
    else if (!comment && !quote && (ch == '\'' || ch == '"')) quote = ch;
    else if (!quote && ch == ';') comment = 1;
    if (ch == '\n') { if (quote) goto failed; comment = 0; }
    if (!append(&body, &ch, 1U)) goto failed;
  }
  if (highest != count || quote) goto failed;
  /* Leave unused complex definitions untouched; reject unsupported constructs
   * only when invoked. Recursive/nested invocations are deliberately excluded. */
  cursor = body.text ? body.text : "";
  while (*cursor) {
    const char *end = strchr(cursor, '\n'); size_t size = end ? (size_t)(end - cursor) : strlen(cursor);
    char line[LINE_LIMIT], *rest, *token;
    if (size >= sizeof(line)) goto failed;
    memcpy(line, cursor, size); line[size] = '\0'; m68k_strip_comment_in_place(line);
    rest = m68k_trim_in_place(line); token = m68k_next_token_in_place(&rest);
    if (find(macros, macro_count, token) || same(token, "MACRO") || same(token, "ENDM") ||
        same(token, "REPT") || same(token, "ENDR") || same(token, "IF") || same(token, "IFD") ||
        same(token, "IFND") || same(token, "ELSE") || same(token, "ENDC") || same(token, "EXITM")) goto failed;
    cursor += size; if (*cursor) ++cursor;
  }
  if (!append(output, body.text ? body.text : "", body.size)) goto failed;
  free(body.text); return 1;
failed: free(body.text); return 0;
}

int m68k_source_macro_expand(const char *text, char **expanded, M68kDiagSink diagnostics) {
  Macro *macros = NULL, *active = NULL; size_t count = 0U, index; int ok = 0;
  Buffer output = {0}; const char *cursor = text;
  if (!expanded) return 0;
  *expanded = NULL;
  if (!text) return 0;
  if (strlen(text) > OUTPUT_LIMIT) goto done;
  macros = (Macro *)calloc(MACRO_LIMIT, sizeof(*macros)); if (!macros) goto done;
  while (*cursor) {
    const char *end = strchr(cursor, '\n'); size_t size = end ? (size_t)(end - cursor) : strlen(cursor);
    char line[LINE_LIMIT], *rest, *first, *second, *args[9]; size_t argc = 0U; Macro *invoked;
    if (size >= sizeof(line)) goto done;
    memcpy(line, cursor, size); line[size] = '\0'; m68k_strip_comment_in_place(line);
    rest = m68k_trim_in_place(line); first = m68k_next_token_in_place(&rest);
    if (active) {
      if (same(first, "ENDM") && !*m68k_trim_in_place(rest)) active = NULL;
      else if (!append(&active->body, cursor, size) || !append(&active->body, "\n", 1U)) goto done;
      if (!append(&output, "\n", 1U)) goto done;
    } else if (same(first, "ENDM")) goto done;
    else {
      invoked = find(macros, count, first);
      if (invoked) {
        if (!arguments(rest, args, &argc) || !expand_body(invoked, args, argc, &output, macros, count)) goto done;
      } else {
        second = m68k_next_token_in_place(&rest);
        if (same(second, "MACRO")) {
          if (count == MACRO_LIMIT || !name_valid(first) || strlen(first) >= sizeof(macros[0].name) ||
              find(macros, count, first) || *m68k_trim_in_place(rest)) goto done;
          active = &macros[count++]; strcpy(active->name, first);
          if (!append(&output, "\n", 1U)) goto done;
        } else if (same(first, "MACRO")) goto done;
        else if (!append(&output, cursor, size) || !append(&output, "\n", 1U)) goto done;
      }
    }
    cursor += size; if (*cursor) ++cursor;
  }
  if (active) goto done;
  if (!output.text && !append(&output, "", 0U)) goto done;
  *expanded = output.text; output.text = NULL; ok = 1;
done:
  if (macros) for (index = 0U; index < count; ++index) free(macros[index].body.text);
  free(macros); free(output.text);
  if (!ok) m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PARSE_FAILED,
    "unsupported, malformed or oversized source macro expansion (literal MACRO, positional 1..9 only)");
  return ok;
}

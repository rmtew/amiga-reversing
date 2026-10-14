#include "m68k_source_package.h"
#include "json_builder.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int overlaps(uint32_t left, uint32_t left_size, uint32_t right, uint32_t right_size) {
  return (uint64_t)left < (uint64_t)right + right_size &&
    (uint64_t)right < (uint64_t)left + left_size;
}

static int contains(const M68kRenderPlanRow *row, uint32_t offset) {
  return offset >= row->source_offset && (uint64_t)offset < (uint64_t)row->source_offset + row->source_size;
}

/* Text is consulted only to preserve comments and validate an already native-
 * classified row's layout, never to infer asset classification or boundaries. */
static int data_line(const char *line, size_t size) {
  while (size && (*line == ' ' || *line == '\t')) { ++line; --size; }
  return (size >= 5U && (!memcmp(line, "dc.b ", 5U) || !memcmp(line, "dc.w ", 5U) ||
    !memcmp(line, "dc.l ", 5U))) ||
    (size >= 6U && (!memcmp(line, "dcb.b ", 6U) || !memcmp(line, "dcb.w ", 6U) ||
    !memcmp(line, "dcb.l ", 6U)));
}

/* Numeric dc/dcb payloads only. A native expression projection should already
 * exclude symbolic uses; this rejection guard also protects render spellings
 * that are not yet represented in that projection. */
static int plain_data_line(const char *line, size_t size) {
  const char *end = line + size;
  if (!data_line(line, size)) return 0;
  while (line < end && (*line == ' ' || *line == '\t')) ++line;
  while (line < end && *line != ' ') ++line;
  for (;;) {
    const char *digits;
    while (line < end && (*line == ' ' || *line == '\t')) ++line;
    if (line < end && (*line == '-' || *line == '+')) ++line;
    if (line < end && *line == '$') {
      digits = ++line;
      while (line < end && ((*line >= '0' && *line <= '9') ||
          (*line >= 'a' && *line <= 'f') || (*line >= 'A' && *line <= 'F'))) ++line;
    } else {
      digits = line;
      while (line < end && *line >= '0' && *line <= '9') ++line;
    }
    if (line == digits) return 0;
    while (line < end && (*line == ' ' || *line == '\t' || *line == '\r')) ++line;
    if (line == end || *line == ';') return 1;
    if (*line++ != ',') return 0;
  }
}

static int eligible(const M68kObject *object, const M68kRenderPlan *plan,
    const M68kRenderPlanRow *row, uint32_t minimum) {
  const M68kSection *section;
  size_t index;
  const char *cursor;
  unsigned line_index = 0U;
  int saw_data = 0;
  if (row->kind != M68K_RENDER_PLAN_ROW_DATA || !row->has_statement_metadata ||
      row->statement_kind != M68K_STATEMENT_DATA || !row->has_source_range ||
      row->source_size < minimum || row->source_section_index >= object->section_count ||
      row->label_line_mask || !row->text ||
      (row->data_class_flags != M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP &&
       row->data_class_flags != M68K_ANALYSIS_STRUCTURED_DATA_ROLE_SOUND_SAMPLE)) return 0;
  section = &object->sections[row->source_section_index];
  if (section->kind == M68K_SECTION_BSS || !section->data ||
      row->source_offset > section->data_size || row->source_size > section->data_size - row->source_offset ||
      row->source_offset > section->size || row->source_size > section->size - row->source_offset) return 0;
  for (index = 0; index < object->fixup_count; ++index) {
    const M68kFixup *fixup = &object->fixups[index];
    if (fixup->section_index == row->source_section_index &&
        overlaps(row->source_offset, row->source_size, fixup->offset, (uint32_t)fixup->width)) return 0;
  }
  for (index = 0; index < plan->expression_count; ++index) {
    const M68kRenderPlannedExpression *expression = &plan->expressions[index];
    if (expression->source_section_index == row->source_section_index && contains(row, expression->source_offset))
      return 0;
  }
  for (index = 0; index < plan->label_count; ++index) {
    const M68kRenderPlannedLabel *label = &plan->labels[index];
    if (label->source_section_index == row->source_section_index &&
        label->source_offset != row->source_offset && contains(row, label->source_offset)) return 0;
  }
  for (index = 0; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *other = &plan->rows[index];
    if (other != row && other->has_source_range && other->source_section_index == row->source_section_index &&
        overlaps(row->source_offset, row->source_size, other->source_offset, other->source_size)) return 0;
  }
  cursor = row->text;
  while (*cursor) {
    const char *end = strchr(cursor, '\n');
    const char *trim = cursor;
    size_t length;
    if (!end) return 0;
    length = (size_t)(end - cursor);
    while (trim < end && (*trim == ' ' || *trim == '\t' || *trim == '\r')) ++trim;
    if (line_index < 32U && (row->directive_line_mask & (1U << line_index))) {
      /* Moving an interior ORG past an INCBIN would change addresses. */
      if (saw_data) return 0;
    } else if (trim < end && *trim != ';') {
      if (!plain_data_line(cursor, length)) return 0;
      saw_data = 1;
    }
    ++line_index;
    cursor = end + 1;
  }
  return saw_data;
}

/* A coalesced asset needs its native role comment once. Keep every other
 * annotation, including comments containing the role plus additional text. */
static int role_comment(const char *comment, size_t length, uint32_t flags) {
  const char *role = flags == M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP ? "bitmap" : "sound_sample";
  if (!length || *comment != ';') return 0;
  ++comment; --length;
  while (length && (*comment == ' ' || *comment == '\t')) { ++comment; --length; }
  while (length && (comment[length - 1U] == ' ' || comment[length - 1U] == '\t' ||
      comment[length - 1U] == '\r' || comment[length - 1U] == '\n')) --length;
  return length == strlen(role) && !memcmp(comment, role, length);
}

static int append_asset_source(JsonBuilder *source, const M68kRenderPlanRow *row, const char *path, const char *alias,
    int *emitted, int *role_emitted) {
  const char *cursor = row->text;
  while (*cursor) {
    const char *end = strchr(cursor, '\n');
    size_t length = (size_t)(end - cursor) + 1U;
    if (data_line(cursor, length)) {
      const char *comment = memchr(cursor, ';', length);
      if (!*emitted && alias && json_builder_appendf(source, "%s:\n", alias) != 0) return -1;
      if (!*emitted && json_builder_appendf(source, "\tINCBIN \"%s\"\n", path) != 0) return -1;
      *emitted = 1;
      if (comment) {
        size_t comment_size = length - (size_t)(comment - cursor);
        int is_role = role_comment(comment, comment_size, row->data_class_flags);
        if ((!is_role || !*role_emitted) && json_builder_append_len(source, comment, comment_size) != 0) return -1;
        if (is_role) *role_emitted = 1;
      }
    } else if (json_builder_append_len(source, cursor, length) != 0) return -1;
    cursor = end + 1;
  }
  return 0;
}

static int joins_asset_run(const M68kRenderPlan *plan, const M68kRenderPlanRow *first,
    uint32_t size, const M68kRenderPlanRow *next) {
  size_t index;
  if (next->source_section_index != first->source_section_index ||
      next->data_class_flags != first->data_class_flags || next->region_id != first->region_id ||
      (uint64_t)first->source_offset + size != next->source_offset ||
      (uint64_t)size + next->source_size > UINT32_MAX || next->directive_line_mask != 0U) return 0;
  /* A label at the next row's start is not interior to that row, but would
   * become interior to the combined asset. Preserve this native boundary. */
  for (index = 0U; index < plan->label_count; ++index)
    if (plan->labels[index].source_section_index == next->source_section_index &&
        plan->labels[index].source_offset == next->source_offset) return 0;
  return 1;
}

/* Naming metadata only: classification and run bounds remain those of the
 * existing native eligibility/coalescing policy. Identity never uses a name. */
typedef struct PackageAssetName {
  size_t row_index;
  uint32_t size;
  char preferred[96];
  char name[192];
  uint8_t needs_alias;
  uint8_t assigned;
  uint8_t name_is_generated;
  uint8_t keep_inline;
} PackageAssetName;

static unsigned ascii_lower(unsigned ch) {
  return ch >= 'A' && ch <= 'Z' ? ch + ('a' - 'A') : ch;
}

static int folded_equal(const char *left, const char *right) {
  while (*left && *right && ascii_lower((unsigned char)*left) == ascii_lower((unsigned char)*right)) {
    ++left; ++right;
  }
  return *left == *right;
}

/* A common subset of global assembler symbols and portable file basenames.
 * Local labels need a global alias so their file identity is scope independent. */
static int portable_asset_name(const char *name) {
  size_t index;
  if (!name[0] || !((name[0] >= 'a' && name[0] <= 'z') ||
      (name[0] >= 'A' && name[0] <= 'Z') || name[0] == '_')) return 0;
  for (index = 1U; name[index]; ++index)
    if (!((name[index] >= 'a' && name[index] <= 'z') ||
        (name[index] >= 'A' && name[index] <= 'Z') ||
        (name[index] >= '0' && name[index] <= '9') || name[index] == '_')) return 0;
  if (folded_equal(name, "con") || folded_equal(name, "prn") || folded_equal(name, "aux") ||
      folded_equal(name, "nul")) return 0;
  if (index == 4U && ((ascii_lower(name[0]) == 'c' && ascii_lower(name[1]) == 'o' &&
      ascii_lower(name[2]) == 'm') || (ascii_lower(name[0]) == 'l' && ascii_lower(name[1]) == 'p' &&
      ascii_lower(name[2]) == 't')) && name[3] >= '1' && name[3] <= '9') return 0;
  return 1;
}

static int symbol_name_conflict(const M68kRenderPlan *plan, const char *name,
    const M68kRenderPlanRow *row, int allow_head) {
  size_t index;
  for (index = 0U; index < plan->label_count; ++index) {
    const M68kRenderPlannedLabel *label = &plan->labels[index];
    int same_head = allow_head && label->source_section_index == row->source_section_index &&
      label->source_offset == row->source_offset;
    if ((!same_head && folded_equal(name, label->name)) ||
        (label->has_storage_label && !same_head && folded_equal(name, label->storage_name))) return 1;
  }
  for (index = 0U; index < plan->declaration_count; ++index) {
    const M68kRenderPlannedDeclaration *decl = &plan->declarations[index];
    if (folded_equal(name, decl->name) && !(allow_head && decl->has_source_target &&
        decl->kind == M68K_RENDER_PLANNED_DECLARATION_LABEL &&
        decl->section_index == row->source_section_index && decl->offset == row->source_offset)) return 1;
  }
  for (index = 0U; index < plan->runtime_alias_count; ++index)
    if (folded_equal(name, plan->runtime_aliases[index].name)) return 1;
  return 0;
}

static int asset_name_conflict(const PackageAssetName *names, size_t count, size_t current,
    const char *name) {
  size_t index;
  for (index = 0U; index < count; ++index) {
    if (index == current) continue;
    if (folded_equal(name, names[index].preferred) ||
        (names[index].assigned && folded_equal(name, names[index].name))) return 1;
  }
  return 0;
}

/* A new global label can rebind assembler local-label scope. The plan's
 * structured symbol names, never rendered label text, conservatively block
 * new aliases whenever a local spelling occurs anywhere in the source. */
static int local_symbol_name(const char *name) {
  return strchr(name, '.') != NULL || strchr(name, '$') != NULL;
}

static int instruction_has_local_symbol(const M68kInstructionIR *instruction) {
  size_t index;
  for (index = 0U; index < instruction->operand_count && index < 4U; ++index)
    if (local_symbol_name(instruction->operands[index].symbol_ref.name) ||
        local_symbol_name(instruction->operands[index].symbol_ref.symbolic_addend_name)) return 1;
  return 0;
}

static int plan_has_local_symbol(const M68kRenderPlan *plan) {
  size_t index, access;
  for (index = 0U; index < plan->label_count; ++index)
    if (local_symbol_name(plan->labels[index].name) || local_symbol_name(plan->labels[index].storage_name)) return 1;
  for (index = 0U; index < plan->declaration_count; ++index)
    if (local_symbol_name(plan->declarations[index].name)) return 1;
  for (index = 0U; index < plan->runtime_alias_count; ++index)
    if (local_symbol_name(plan->runtime_aliases[index].name)) return 1;
  for (index = 0U; index < plan->expression_count; ++index)
    if (local_symbol_name(plan->expressions[index].target_symbol) ||
        local_symbol_name(plan->expressions[index].base_symbol)) return 1;
  for (index = 0U; index < plan->instruction_count; ++index) {
    const M68kRenderPlannedInstruction *instruction = &plan->instructions[index];
    if (instruction_has_local_symbol(&instruction->instruction) ||
        instruction_has_local_symbol(&instruction->render_instruction)) return 1;
    for (access = 0U; access < instruction->symbol_access_count && access < 4U; ++access)
      if (local_symbol_name(instruction->symbol_accesses[access].symbol_name)) return 1;
  }
  for (index = 0U; index < plan->row_count; ++index)
    if (instruction_has_local_symbol(&plan->rows[index].statement_instruction)) return 1;
  return 0;
}

static int assign_asset_names(const M68kRenderPlan *plan, PackageAssetName *names, size_t count) {
  size_t index, assigned;
  int has_local_symbol = plan_has_local_symbol(plan);
  for (index = 0U; index < count; ++index) {
    PackageAssetName *asset = &names[index];
    const M68kRenderPlanRow *row = &plan->rows[asset->row_index];
    const M68kRenderPlannedLabel *head = m68k_render_plan_find_label(plan,
      row->source_section_index, row->source_offset);
    if (head && portable_asset_name(head->name)) {
      asset->name_is_generated = head->name_is_generated;
      memcpy(asset->preferred, head->name, sizeof(asset->preferred));
    } else {
      snprintf(asset->preferred, sizeof(asset->preferred), "provisional_asset_s%04u_o%08x_n%08x",
        (unsigned)row->source_section_index, (unsigned)row->source_offset, (unsigned)asset->size);
      asset->needs_alias = 1U;
    }
  }
  /* Reserve every preferred spelling before selecting any alias. Canonical
   * coordinate order makes disambiguation independent of render row order. */
  for (assigned = 0U; assigned < count; ++assigned) {
    size_t chosen = count;
    PackageAssetName *asset;
    const M68kRenderPlanRow *row;
    size_t attempt;
    for (index = 0U; index < count; ++index) {
      const M68kRenderPlanRow *candidate = &plan->rows[names[index].row_index];
      const M68kRenderPlanRow *previous = chosen < count ? &plan->rows[names[chosen].row_index] : NULL;
      if (!names[index].assigned && (!previous || candidate->source_section_index < previous->source_section_index ||
          (candidate->source_section_index == previous->source_section_index && candidate->source_offset < previous->source_offset)))
        chosen = index;
    }
    asset = &names[chosen];
    row = &plan->rows[asset->row_index];
    if (symbol_name_conflict(plan, asset->preferred, row, !asset->needs_alias) ||
        asset_name_conflict(names, count, chosen, asset->preferred)) asset->needs_alias = 1U;
    strcpy(asset->name, asset->preferred);
    if (asset->needs_alias && (symbol_name_conflict(plan, asset->name, row, 0) ||
        asset_name_conflict(names, count, chosen, asset->name))) {
      /* Each failed attempt consumes a spelling reserved by a finite native
       * symbol or asset set; never silently truncate the full native name. */
      for (attempt = 0U; attempt <= plan->label_count * 2U + plan->declaration_count +
          plan->runtime_alias_count + count * 2U; ++attempt) {
        int length = snprintf(asset->name, sizeof(asset->name), "%s__asset_s%04u_o%08x_n%08x_%zu",
          asset->preferred, (unsigned)row->source_section_index, (unsigned)row->source_offset,
          (unsigned)asset->size, attempt);
        if (length < 0 || (size_t)length >= sizeof(asset->name)) return -1;
        if (!symbol_name_conflict(plan, asset->name, row, 0) &&
            !asset_name_conflict(names, count, chosen, asset->name)) break;
      }
      if (attempt > plan->label_count * 2U + plan->declaration_count + plan->runtime_alias_count + count * 2U)
        return -1;
    }
    if (asset->needs_alias) asset->name_is_generated = 1U;
    asset->keep_inline = asset->needs_alias && has_local_symbol;
    asset->assigned = 1U;
  }
  return 0;
}

int m68k_source_package_json_alloc(const M68kObject *object, const M68kRenderPlan *plan,
    uint32_t minimum_asset_size, char **out_json) {
  JsonBuilder source = {0}, assets = {0}, result = {0};
  char *source_text = NULL;
  uint8_t *eligible_rows = NULL;
  PackageAssetName *names = NULL;
  size_t name_count = 0U, name_index = 0U;
  size_t index, count = 0U;
  int status = -1;
  if (!out_json) return -1;
  *out_json = NULL;
  if (!object || !plan || minimum_asset_size == 0U) return -1;
  if (json_builder_create(&source) || json_builder_create(&assets) || json_builder_create(&result)) goto done;
  eligible_rows = (uint8_t *)calloc(plan->row_count ? plan->row_count : 1U, 1U);
  if (!eligible_rows) goto done;
  for (index = 0U; index < plan->row_count; ++index)
    eligible_rows[index] = (uint8_t)eligible(object, plan, &plan->rows[index], 1U);
  names = (PackageAssetName *)calloc(plan->row_count ? plan->row_count : 1U, sizeof(*names));
  if (!names) goto done;
  for (index = 0U; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *row = &plan->rows[index];
    size_t end = index + 1U;
    uint32_t size = row->source_size;
    if (eligible_rows[index]) {
      while (end < plan->row_count && eligible_rows[end] && joins_asset_run(plan, row, size, &plan->rows[end])) {
        size += plan->rows[end].source_size;
        ++end;
      }
      if (size >= minimum_asset_size) {
        names[name_count].row_index = index;
        names[name_count++].size = size;
      }
    }
    index = end - 1U;
  }
  if (assign_asset_names(plan, names, name_count) != 0) goto done;
  for (index = 0U; index < plan->row_count; ++index) {
    const M68kRenderPlanRow *row = &plan->rows[index];
    size_t end = index + 1U, run_index;
    uint32_t run_size = row->source_size;
    if (eligible_rows[index]) {
      while (end < plan->row_count && eligible_rows[end] &&
          joins_asset_run(plan, row, run_size, &plan->rows[end])) {
        run_size += plan->rows[end].source_size;
        ++end;
      }
    }
    if (eligible_rows[index] && run_size >= minimum_asset_size) {
      char path[224];
      const PackageAssetName *asset_name = &names[name_index++];
      uint32_t byte_index;
      if (asset_name->keep_inline) {
        for (run_index = index; run_index < end; ++run_index)
          if (json_builder_append(&source, plan->rows[run_index].text) != 0) goto done;
        index = end - 1U;
        continue;
      }
      int emitted = 0;
      int role_emitted = 0;
      const uint8_t *bytes = object->sections[row->source_section_index].data + row->source_offset;
      const char *classification = row->data_class_flags == M68K_ANALYSIS_STRUCTURED_DATA_ROLE_BITMAP
        ? "bitmap" : "sound_sample";
      snprintf(path, sizeof(path), "assets/%s.bin", asset_name->name);
      for (run_index = index; run_index < end; ++run_index)
        if (append_asset_source(&source, &plan->rows[run_index], path, asset_name->needs_alias ? asset_name->name : NULL, &emitted, &role_emitted) != 0) goto done;
      if ((count && json_builder_append(&assets, ",") != 0) ||
          json_builder_appendf(&assets, "{\"asset_id\":\"section-%04u-offset-%08x-size-%08x\",\"name\":\"%s\",\"name_is_generated\":%s,\"path\":\"%s\",\"source_section_index\":%u,\"source_offset\":%u,"
            "\"size\":%u,\"classification\":\"%s\",\"data_class_flags\":%u,\"source_row_id\":%u,\"source_row_count\":%u,\"data_hex\":\"",
            (unsigned)row->source_section_index, (unsigned)row->source_offset, (unsigned)run_size,
            asset_name->name, asset_name->name_is_generated ? "true" : "false", path, (unsigned)row->source_section_index, (unsigned)row->source_offset, (unsigned)run_size,
            classification, (unsigned)row->data_class_flags, (unsigned)row->id, (unsigned)(end - index)) != 0) goto done;
      for (byte_index = 0; byte_index < run_size; ++byte_index)
        if (json_builder_appendf(&assets, "%02x", bytes[byte_index]) != 0) goto done;
      if (json_builder_append(&assets, "\"}") != 0) goto done;
      ++count;
    } else {
      for (run_index = index; run_index < end; ++run_index)
        if (!plan->rows[run_index].text || json_builder_append(&source, plan->rows[run_index].text) != 0) goto done;
    }
    index = end - 1U;
  }
  source_text = json_builder_build(&source);
  if (!source_text || json_builder_append(&result, "{\"source_text\":") ||
      json_builder_append_json_string(&result, source_text) || json_builder_append(&result, ",\"assets\":[") ||
      json_builder_append_builder(&result, &assets) || json_builder_append(&result, "]}")) goto done;
  *out_json = json_builder_build(&result);
  status = *out_json ? 0 : -1;
done:
  free(names);
  free(eligible_rows);
  free(source_text);
  json_builder_destroy(&source);
  json_builder_destroy(&assets);
  json_builder_destroy(&result);
  return status;
}

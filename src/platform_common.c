#include "platform_common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#pragma comment(lib, "bcrypt.lib")
#endif

char *m68k_platform_dup_string(const char *text) {
  size_t length;
  char *copy;
  if (text == NULL) text = "";
  length = strlen(text);
  copy = (char *)malloc(length + 1U);
  if (copy == NULL) return NULL;
  memcpy(copy, text, length + 1U);
  return copy;
}

int m68k_platform_join_path(const char *base, const char *name, char **out_path) {
  size_t base_len = strlen(base);
  size_t name_len = strlen(name);
  size_t total = base_len + name_len + (base_len != 0U ? 2U : 1U);
  char *path = (char *)malloc(total);
  if (path == NULL) return -1;
  if (base_len != 0U) {
    memcpy(path, base, base_len);
    path[base_len] = '/';
    memcpy(path + base_len + 1U, name, name_len + 1U);
  } else {
    memcpy(path, name, name_len + 1U);
  }
  *out_path = path;
  return 0;
}

int m68k_platform_sha256_hex(const unsigned char *data, size_t size, char out_hex[65]) {
#ifdef _WIN32
  BCRYPT_ALG_HANDLE algorithm = NULL;
  BCRYPT_HASH_HANDLE hash = NULL;
  unsigned char digest[32];
  static const char hex[] = "0123456789abcdef";
  size_t offset = 0U;
  size_t i;
  if (data == NULL || out_hex == NULL) return -1;
  out_hex[0] = '\0';
  if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, NULL, 0) != 0) goto fail;
  if (BCryptCreateHash(algorithm, &hash, NULL, 0, NULL, 0, 0) != 0) goto fail;
  while (offset < size) {
    size_t chunk = size - offset;
    if (chunk > 0x40000000U) chunk = 0x40000000U;
    if (BCryptHashData(hash, (PUCHAR)(data + offset), (ULONG)chunk, 0) != 0) goto fail;
    offset += chunk;
  }
  if (BCryptFinishHash(hash, digest, sizeof(digest), 0) != 0) goto fail;
  for (i = 0U; i < sizeof(digest); ++i) {
    out_hex[i * 2U] = hex[digest[i] >> 4U];
    out_hex[i * 2U + 1U] = hex[digest[i] & 0x0FU];
  }
  out_hex[64] = '\0';
  BCryptDestroyHash(hash);
  BCryptCloseAlgorithmProvider(algorithm, 0);
  return 0;
fail:
  if (hash != NULL) BCryptDestroyHash(hash);
  if (algorithm != NULL) BCryptCloseAlgorithmProvider(algorithm, 0);
  if (out_hex != NULL) out_hex[0] = '\0';
  return -1;
#else
  (void)data;
  (void)size;
  if (out_hex != NULL) out_hex[0] = '\0';
  return -1;
#endif
}

int amiga_value_domain_symbolic_expr(const char *domain_name, uint32_t value, char *expr,
    size_t expr_size) {
  const AmigaOsValueDomainInfo *domain;
  const AmigaOsValueDomainMemberInfo *members;
  size_t member_count = 0U;
  uint32_t remaining;
  size_t index;
  int wrote = 0;
  if (expr == NULL || expr_size == 0U || domain_name == NULL || domain_name[0] == '\0') return 0;
  expr[0] = '\0';
  domain = amiga_os_find_value_domain(domain_name);
  if (domain == NULL) return 0;
  members = amiga_os_value_domain_members(domain, &member_count);
  if (members == NULL) return 0;
  for (index = 0U; index < member_count; ++index) {
    const char *name;
    if (!members[index].value_known || (uint32_t)members[index].value != value) continue;
    name = amiga_os_name(4U, members[index].name_id);
    if (name == NULL || name[0] == '\0') continue;
    snprintf(expr, expr_size, "%s", name);
    return 1;
  }
  if (value == 0U && domain->zero_name_id != AMIGA_OS_SYMBOL_ID_NONE) {
    const char *name = amiga_os_name(4U, domain->zero_name_id);
    if (name == NULL || name[0] == '\0') return 0;
    snprintf(expr, expr_size, "%s", name);
    return 1;
  }
  if (domain->kind != AMIGA_OS_VALUE_DOMAIN_KIND_FLAGS ||
      (domain->composition != AMIGA_OS_VALUE_DOMAIN_COMPOSITION_OR &&
       domain->composition != AMIGA_OS_VALUE_DOMAIN_COMPOSITION_BIT_OR)) {
    return 0;
  }
  remaining = value;
  while (remaining != 0U) {
    uint32_t best_value = 0U;
    const char *best_name = NULL;
    for (index = 0U; index < member_count; ++index) {
      uint32_t member_value;
      const char *name;
      if (!members[index].value_known || members[index].value <= 0) continue;
      member_value = (uint32_t)members[index].value;
      if ((remaining & member_value) != member_value) continue;
      name = amiga_os_name(4U, members[index].name_id);
      if (name == NULL || name[0] == '\0') continue;
      if (best_name == NULL || member_value > best_value) {
        best_value = member_value;
        best_name = name;
      }
    }
    if (best_name == NULL) return 0;
    if (wrote) {
      size_t used = strlen(expr);
      if (used + 2U > expr_size) return 0;
      expr[used] = '|';
      expr[used + 1U] = '\0';
    }
    if (strlen(expr) + strlen(best_name) + 1U > expr_size) return 0;
    strcat(expr, best_name);
    remaining &= ~best_value;
    wrote = 1;
  }
  return wrote;
}

int platform_amiga_format_global_base_slot_label(size_t section_index, char width_suffix, const char *base_name,
    char *buf, size_t buf_size) {
  const char *tail = base_name;
  size_t tail_index = 0U;
  char normalized[64];
  int written;
  if (buf == NULL || buf_size == 0U || base_name == NULL || base_name[0] == '\0') return 0;
  if (strcmp(base_name, "SysBase") == 0) tail = "ExecBase";
  while (tail[0] == '_' || tail[0] == '.') ++tail;
  while (tail[tail_index] != '\0' && tail_index + 1U < sizeof(normalized)) {
    char ch = tail[tail_index];
    normalized[tail_index] = (ch == '.' || ch == '-' || ch == ' ') ? '_' : ch;
    ++tail_index;
  }
  normalized[tail_index] = '\0';
  written = snprintf(buf, buf_size, "h%ud%c_%s", (unsigned)section_index, width_suffix, normalized);
  return written > 0 && (size_t)written < buf_size;
}

int platform_amiga_format_app_base_slot_name(const char *base_name, char *buf, size_t buf_size) {
  int written;
  if (buf == NULL || buf_size == 0U || base_name == NULL || base_name[0] == '\0') return 0;
  if (strcmp(base_name, "SysBase") == 0) {
    written = snprintf(buf, buf_size, "app_ExecBase");
  } else {
    written = snprintf(buf, buf_size, "app_%s", base_name);
  }
  return written > 0 && (size_t)written < buf_size;
}

static int platform_amiga_hardware_register_field_instance_delta(
    const AmigaOsHardwareRegisterFieldInfo *hardware_field, uint32_t *out_delta) {
  if (out_delta != NULL) *out_delta = 0U;
  if (hardware_field == NULL || hardware_field->base_symbol == NULL ||
      hardware_field->register_symbol == NULL || out_delta == NULL) {
    return 0;
  }
  return 1;
}

static int platform_amiga_format_hardware_register_field_instance_delta(
    const AmigaOsHardwareRegisterFieldInfo *hardware_field, uint32_t instance_delta, char *buf, size_t buf_size) {
  uint32_t multiplier;
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (instance_delta == 0U) return 1;
  if (hardware_field != NULL && hardware_field->repeat_stride_symbol != NULL &&
      hardware_field->repeat_stride_symbol[0] != '\0' && hardware_field->repeat_stride != 0U &&
      (instance_delta % hardware_field->repeat_stride) == 0U) {
    multiplier = instance_delta / hardware_field->repeat_stride;
    if (multiplier == 1U) {
      written = snprintf(buf, buf_size, "%s", hardware_field->repeat_stride_symbol);
    } else {
      written = snprintf(buf, buf_size, "%s*%u", hardware_field->repeat_stride_symbol, (unsigned)multiplier);
    }
    return written > 0 && (size_t)written < buf_size;
  }
  written = snprintf(buf, buf_size, instance_delta < 0x100U ? "$%02X" : "$%X", (unsigned)instance_delta);
  return written > 0 && (size_t)written < buf_size;
}

int platform_amiga_format_hardware_register_field_symbol(const AmigaOsHardwareRegisterFieldInfo *hardware_field,
    int include_hardware_base, char *buf, size_t buf_size) {
  uint32_t instance_delta = 0U;
  char delta_text[16];
  const char *instance_symbol;
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_field == NULL || hardware_field->register_symbol == NULL || hardware_field->field_symbol == NULL ||
      hardware_field->register_symbol[0] == '\0' || hardware_field->field_symbol[0] == '\0') {
    return 0;
  }
  instance_symbol = (hardware_field->instance_symbol != NULL && hardware_field->instance_symbol[0] != '\0')
    ? hardware_field->instance_symbol
    : NULL;
  if (instance_symbol != NULL) {
    if (include_hardware_base) {
      if (hardware_field->base_symbol == NULL || hardware_field->base_symbol[0] == '\0') return 0;
      written = snprintf(buf, buf_size, "%s+%s+%s", hardware_field->base_symbol, instance_symbol,
        hardware_field->field_symbol);
      return written > 0 && (size_t)written < buf_size;
    }
    written = snprintf(buf, buf_size, "%s+%s", instance_symbol, hardware_field->field_symbol);
    return written > 0 && (size_t)written < buf_size;
  }
  if (!platform_amiga_hardware_register_field_instance_delta(hardware_field, &instance_delta))
    instance_delta = 0U;
  if (!platform_amiga_format_hardware_register_field_instance_delta(hardware_field, instance_delta, delta_text,
      sizeof(delta_text))) {
    return 0;
  }
  if (include_hardware_base) {
    if (hardware_field->base_symbol == NULL || hardware_field->base_symbol[0] == '\0') return 0;
    if (instance_delta != 0U) {
      written = snprintf(buf, buf_size, "%s+%s+%s+%s", hardware_field->base_symbol,
        hardware_field->register_symbol, delta_text, hardware_field->field_symbol);
      return written > 0 && (size_t)written < buf_size;
    }
    written = snprintf(buf, buf_size, "%s+%s+%s", hardware_field->base_symbol, hardware_field->register_symbol,
      hardware_field->field_symbol);
    return written > 0 && (size_t)written < buf_size;
  }
  if (instance_delta != 0U) {
    written = snprintf(buf, buf_size, "%s+%s+%s", hardware_field->register_symbol, delta_text,
      hardware_field->field_symbol);
    return written > 0 && (size_t)written < buf_size;
  }
  written = snprintf(buf, buf_size, "%s+%s", hardware_field->register_symbol, hardware_field->field_symbol);
  return written > 0 && (size_t)written < buf_size;
}

int platform_amiga_format_hardware_register_range_symbol(const AmigaOsHardwareRegisterRangeInfo *hardware_range,
    uint32_t offset, int include_hardware_base, char *buf, size_t buf_size) {
  uint32_t delta;
  char delta_text[16];
  int written;
  if (buf == NULL || buf_size == 0U) return 0;
  buf[0] = '\0';
  if (hardware_range == NULL || hardware_range->symbol_name == NULL || hardware_range->symbol_name[0] == '\0' ||
      offset < hardware_range->offset || offset >= hardware_range->offset + hardware_range->size) {
    return 0;
  }
  delta = offset - hardware_range->offset;
  snprintf(delta_text, sizeof(delta_text), delta < 0x100U ? "$%02X" : "$%X", (unsigned)delta);
  if (include_hardware_base) {
    if (hardware_range->base_symbol == NULL || hardware_range->base_symbol[0] == '\0') return 0;
    if (delta == 0U)
      written = snprintf(buf, buf_size, "%s+%s", hardware_range->base_symbol, hardware_range->symbol_name);
    else
      written = snprintf(buf, buf_size, "%s+%s+%s", hardware_range->base_symbol,
        hardware_range->symbol_name, delta_text);
  } else {
    if (delta == 0U)
      written = snprintf(buf, buf_size, "%s", hardware_range->symbol_name);
    else
      written = snprintf(buf, buf_size, "%s+%s", hardware_range->symbol_name, delta_text);
  }
  return written > 0 && (size_t)written < buf_size;
}

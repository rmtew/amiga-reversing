#include "platform_common.h"
#include "util_arena.h"

#include <stdio.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#pragma comment(lib, "bcrypt.lib")
#endif

char *m68k_platform_dup_string(const char *text) {
  return m68k_allocator_strdup(m68k_allocator_heap(), text);
}

int m68k_platform_join_path(const char *base, const char *name, char **out_path) {
  size_t base_len = strlen(base);
  size_t name_len = strlen(name);
  size_t total = base_len + name_len + (base_len != 0U ? 2U : 1U);
  char *path = (char *)m68k_allocator_alloc(m68k_allocator_heap(), total);
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

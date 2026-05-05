#include "platform_file_decompression.h"
#include "json_builder.h"

#include <ctype.h>
#include <errno.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#pragma comment(lib, "bcrypt.lib")
#define PLATFORM_POPEN _popen
#define PLATFORM_PCLOSE _pclose
#else
#define PLATFORM_POPEN popen
#define PLATFORM_PCLOSE pclose
#endif

static void set_error_local(char *error, size_t error_size, const char *message) {
  if (error == NULL || error_size == 0U) return;
  if (message == NULL) message = "";
  snprintf(error, error_size, "%s", message);
}

void platform_decompression_identify_result_init(PlatformDecompressionIdentifyResult *result) {
  if (result == NULL) return;
  memset(result, 0, sizeof(*result));
}

static const char *default_ancient_path_local(void) {
  const char *env = getenv("AMIGA_ANCIENT_EXE");
#ifdef _WIN32
  static char resolved_path[MAX_PATH];
  HMODULE module = NULL;
  DWORD length;
  char *cursor;
  DWORD attrs;
#endif
  if (env != NULL && env[0] != '\0') return env;
#ifdef _WIN32
  if (resolved_path[0] != '\0') return resolved_path;
  if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        (LPCSTR)&default_ancient_path_local, &module) &&
      module != NULL) {
    length = GetModuleFileNameA(module, resolved_path, sizeof(resolved_path));
    if (length != 0U && length < sizeof(resolved_path)) {
      cursor = strrchr(resolved_path, '\\');
      if (cursor != NULL) {
        *cursor = '\0';
        cursor = strrchr(resolved_path, '\\');
      }
      if (cursor != NULL) {
        *cursor = '\0';
        cursor = strrchr(resolved_path, '\\');
      }
      if (cursor != NULL) {
        *cursor = '\0';
        if (strlen(resolved_path) + strlen("\\ext\\tools\\ancient\\Ancient.exe") < sizeof(resolved_path)) {
          strcat(resolved_path, "\\ext\\tools\\ancient\\Ancient.exe");
          attrs = GetFileAttributesA(resolved_path);
          if (attrs != INVALID_FILE_ATTRIBUTES && (attrs & FILE_ATTRIBUTE_DIRECTORY) == 0U)
            return resolved_path;
        }
      }
    }
  }
  resolved_path[0] = '\0';
#endif
  return "ext\\tools\\ancient\\Ancient.exe";
}

static int quote_arg_local(char *out, size_t out_size, const char *arg) {
  size_t used = 0U;
  const unsigned char *cursor;
  if (out == NULL || out_size < 3U || arg == NULL) return 0;
  out[used++] = '"';
  for (cursor = (const unsigned char *)arg; *cursor != 0U; ++cursor) {
    if (*cursor == '"') {
      if (used + 2U >= out_size) return 0;
      out[used++] = '\\';
      out[used++] = '"';
    } else {
      if (used + 1U >= out_size) return 0;
      out[used++] = (char)*cursor;
    }
  }
  if (used + 2U > out_size) return 0;
  out[used++] = '"';
  out[used] = '\0';
  return 1;
}

static int make_temp_path_local(char *out, size_t out_size) {
#ifdef _WIN32
  char temp_dir[MAX_PATH];
  char temp_file[MAX_PATH];
  DWORD dir_len;
#else
  const char *dir = getenv("TEMP");
  uint32_t pid = (uint32_t)_getpid();
  uint32_t tick = (uint32_t)clock();
#endif
  if (out == NULL || out_size == 0U) return 0;
#ifdef _WIN32
  dir_len = GetTempPathA(sizeof(temp_dir), temp_dir);
  if (dir_len == 0U || dir_len >= sizeof(temp_dir)) return 0;
  if (GetTempFileNameA(temp_dir, "agr", 0U, temp_file) == 0U) return 0;
  if (strlen(temp_file) + 1U > out_size) {
    DeleteFileA(temp_file);
    return 0;
  }
  strcpy(out, temp_file);
  return 1;
#else
  if (dir == NULL || dir[0] == '\0') dir = ".";
  return snprintf(out, out_size, "%s\\amiga_depack_%u_%u.bin", dir, (unsigned)pid, (unsigned)tick) > 0;
#endif
}

static int file_sha256_hex_local(const char *path, uint32_t *out_size, char out_hex[65]) {
#ifdef _WIN32
  BCRYPT_ALG_HANDLE algorithm = NULL;
  BCRYPT_HASH_HANDLE hash = NULL;
  FILE *file = NULL;
  unsigned char buffer[8192];
  unsigned char digest[32];
  static const char hex[] = "0123456789abcdef";
  uint32_t total = 0U;
  size_t read_count;
  size_t i;
  if (path == NULL || out_hex == NULL) return -1;
  out_hex[0] = '\0';
  if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, NULL, 0) != 0) goto fail;
  if (BCryptCreateHash(algorithm, &hash, NULL, 0, NULL, 0, 0) != 0) goto fail;
  file = fopen(path, "rb");
  if (file == NULL) goto fail;
  while ((read_count = fread(buffer, 1U, sizeof(buffer), file)) != 0U) {
    if (total > UINT32_MAX - (uint32_t)read_count) goto fail;
    total += (uint32_t)read_count;
    if (BCryptHashData(hash, (PUCHAR)buffer, (ULONG)read_count, 0) != 0) goto fail;
  }
  if (ferror(file)) goto fail;
  if (BCryptFinishHash(hash, digest, sizeof(digest), 0) != 0) goto fail;
  for (i = 0U; i < sizeof(digest); ++i) {
    out_hex[i * 2U] = hex[digest[i] >> 4U];
    out_hex[i * 2U + 1U] = hex[digest[i] & 0x0FU];
  }
  out_hex[64] = '\0';
  if (out_size != NULL) *out_size = total;
  fclose(file);
  BCryptDestroyHash(hash);
  BCryptCloseAlgorithmProvider(algorithm, 0);
  return 0;
fail:
  if (file != NULL) fclose(file);
  if (hash != NULL) BCryptDestroyHash(hash);
  if (algorithm != NULL) BCryptCloseAlgorithmProvider(algorithm, 0);
  return -1;
#else
  (void)path;
  (void)out_size;
  if (out_hex != NULL) out_hex[0] = '\0';
  return -1;
#endif
}

static int write_file_range_local(const char *path, uint32_t offset, uint32_t size, char *temp_path,
    size_t temp_path_size, char *error, size_t error_size) {
  FILE *input = NULL;
  FILE *output = NULL;
  unsigned char buffer[8192];
  uint32_t remaining = size;
  if (path == NULL || temp_path == NULL || !make_temp_path_local(temp_path, temp_path_size)) {
    set_error_local(error, error_size, "failed creating temporary path");
    return -1;
  }
  input = fopen(path, "rb");
  if (input == NULL) {
    set_error_local(error, error_size, "failed opening input file");
    return -1;
  }
#ifdef _WIN32
  if (_fseeki64(input, (int64_t)offset, SEEK_SET) != 0) {
#else
  if (fseek(input, (int32_t)offset, SEEK_SET) != 0) {
#endif
    fclose(input);
    set_error_local(error, error_size, "failed seeking input file");
    return -1;
  }
  output = fopen(temp_path, "wb");
  if (output == NULL) {
    fclose(input);
    set_error_local(error, error_size, "failed creating temporary range file");
    return -1;
  }
  while (remaining != 0U) {
    size_t chunk = remaining < sizeof(buffer) ? (size_t)remaining : sizeof(buffer);
    size_t read_count = fread(buffer, 1U, chunk, input);
    if (read_count != chunk || fwrite(buffer, 1U, chunk, output) != chunk) {
      fclose(output);
      fclose(input);
      remove(temp_path);
      set_error_local(error, error_size, "failed copying input range");
      return -1;
    }
    remaining -= (uint32_t)chunk;
  }
  if (fclose(output) != 0) {
    fclose(input);
    remove(temp_path);
    set_error_local(error, error_size, "failed closing temporary range file");
    return -1;
  }
  fclose(input);
  return 0;
}

static int write_buffer_range_local(const uint8_t *data, uint32_t data_size, uint32_t offset, uint32_t size,
    char *temp_path, size_t temp_path_size, char *error, size_t error_size) {
  FILE *output;
  if (data == NULL || temp_path == NULL || size == 0U || offset > data_size || size > data_size - offset ||
      !make_temp_path_local(temp_path, temp_path_size)) {
    set_error_local(error, error_size, "invalid decompression buffer range");
    return -1;
  }
  output = fopen(temp_path, "wb");
  if (output == NULL) {
    set_error_local(error, error_size, "failed creating temporary range file");
    return -1;
  }
  if (fwrite(data + offset, 1U, size, output) != size) {
    fclose(output);
    remove(temp_path);
    set_error_local(error, error_size, "failed writing temporary range file");
    return -1;
  }
  if (fclose(output) != 0) {
    remove(temp_path);
    set_error_local(error, error_size, "failed closing temporary range file");
    return -1;
  }
  return 0;
}

static uint32_t read_u32be_local(const uint8_t *data) {
  return ((uint32_t)data[0] << 24) | ((uint32_t)data[1] << 16) | ((uint32_t)data[2] << 8) | (uint32_t)data[3];
}

static int ancient_rnc_candidate_size_local(const uint8_t *data, uint32_t data_size, uint32_t offset,
    uint32_t *out_size, char *codec_hint, size_t codec_hint_size) {
  uint32_t packed_payload_size;
  if (out_size != NULL) *out_size = 0U;
  if (data == NULL || out_size == NULL || offset > data_size || data_size - offset < 18U) return 0;
  if (memcmp(data + offset, "RNC\001", 4U) == 0) {
    if (codec_hint != NULL && codec_hint_size != 0U) snprintf(codec_hint, codec_hint_size, "rnc1");
  } else if (memcmp(data + offset, "RNC\002", 4U) == 0) {
    if (codec_hint != NULL && codec_hint_size != 0U) snprintf(codec_hint, codec_hint_size, "rnc2");
  } else if (memcmp(data + offset, "...\001", 4U) == 0) {
    if (codec_hint != NULL && codec_hint_size != 0U) snprintf(codec_hint, codec_hint_size, "rnc1");
  } else {
    return 0;
  }
  packed_payload_size = read_u32be_local(data + offset + 8U);
  if (packed_payload_size > UINT32_MAX - 18U || packed_payload_size + 18U > data_size - offset) return 0;
  *out_size = packed_payload_size + 18U;
  return 1;
}

size_t platform_decompression_find_candidates_in_buffer(const char *provider_id, const uint8_t *data,
    uint32_t data_size, PlatformDecompressionCandidate *out_candidates, size_t candidate_capacity) {
  const char *actual_provider_id = (provider_id != NULL && provider_id[0] != '\0') ? provider_id : "ancient-cli";
  size_t count = 0U;
  uint32_t offset;
  if (strcmp(actual_provider_id, "ancient-cli") != 0 || data == NULL) return 0U;
  for (offset = 0U; offset < data_size; ++offset) {
    uint32_t packed_size;
    PlatformDecompressionCandidate candidate;
    if (!ancient_rnc_candidate_size_local(data, data_size, offset, &packed_size, NULL, 0U)) continue;
    memset(&candidate, 0, sizeof(candidate));
    candidate.offset = offset;
    candidate.packed_size = packed_size;
    (void)ancient_rnc_candidate_size_local(data, data_size, offset, &packed_size, candidate.codec_hint,
      sizeof(candidate.codec_hint));
    if (count < candidate_capacity && out_candidates != NULL) out_candidates[count] = candidate;
    ++count;
  }
  return count;
}

static void trim_line_local(char *text) {
  size_t length;
  char *start = text;
  if (text == NULL) return;
  while (*start != '\0' && isspace((unsigned char)*start)) ++start;
  if (start != text) memmove(text, start, strlen(start) + 1U);
  length = strlen(text);
  while (length != 0U && isspace((unsigned char)text[length - 1U])) text[--length] = '\0';
}

static int ancient_parse_identify_output_local(const char *line, PlatformDecompressionIdentifyResult *result) {
  const char *prefix = "Compression of ";
  const char *marker = " is ";
  const char *codec;
  const char *colon;
  size_t id_len;
  if (line == NULL || result == NULL || strncmp(line, prefix, strlen(prefix)) != 0) return 0;
  codec = strstr(line, marker);
  if (codec == NULL) return 0;
  codec += strlen(marker);
  if (strncmp(codec, "RNC1: Rob Northen RNC1 Compressor (old)", 39U) == 0) {
    snprintf(result->codec_id, sizeof(result->codec_id), "rnc1-old");
  } else {
    colon = strchr(codec, ':');
    id_len = colon != NULL ? (size_t)(colon - codec) : strlen(codec);
    if (id_len >= sizeof(result->codec_id)) id_len = sizeof(result->codec_id) - 1U;
    memcpy(result->codec_id, codec, id_len);
    result->codec_id[id_len] = '\0';
    for (id_len = 0U; result->codec_id[id_len] != '\0'; ++id_len) {
      result->codec_id[id_len] = (char)tolower((unsigned char)result->codec_id[id_len]);
      if (!isalnum((unsigned char)result->codec_id[id_len])) result->codec_id[id_len] = '-';
    }
  }
  snprintf(result->codec_name, sizeof(result->codec_name), "%s", codec);
  snprintf(result->confidence, sizeof(result->confidence), "provider-identified");
  result->found = 1;
  return 1;
}

static int ancient_identify_temp_file_local(const char *ancient_path, const char *temp_path,
    PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size) {
  char quoted_exe[640];
  char quoted_input[640];
  char command[1400];
  char line[512];
#ifdef _WIN32
  char quoted_output[640];
  char output_path[512];
  FILE *output;
  STARTUPINFOA startup;
  PROCESS_INFORMATION process;
  DWORD wait_result;
#else
  FILE *pipe;
  int status;
#endif
  if (!quote_arg_local(quoted_exe, sizeof(quoted_exe), ancient_path) ||
      !quote_arg_local(quoted_input, sizeof(quoted_input), temp_path)) {
    set_error_local(error, error_size, "failed quoting Ancient command");
    return -1;
  }
#ifdef _WIN32
  if (!make_temp_path_local(output_path, sizeof(output_path))) {
    set_error_local(error, error_size, "failed creating Ancient identify output path");
    return -1;
  }
  if (!quote_arg_local(quoted_output, sizeof(quoted_output), output_path)) {
    remove(output_path);
    set_error_local(error, error_size, "failed quoting Ancient identify output path");
    return -1;
  }
  snprintf(command, sizeof(command), "cmd.exe /d /c \"%s identify %s > %s 2>NUL\"", quoted_exe, quoted_input,
    quoted_output);
  memset(&startup, 0, sizeof(startup));
  memset(&process, 0, sizeof(process));
  startup.cb = sizeof(startup);
  if (!CreateProcessA(NULL, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &startup, &process)) {
    remove(output_path);
    set_error_local(error, error_size, "failed running Ancient identify");
    return -1;
  }
  wait_result = WaitForSingleObject(process.hProcess, 30000U);
  if (wait_result != WAIT_OBJECT_0) (void)TerminateProcess(process.hProcess, 1U);
  CloseHandle(process.hThread);
  CloseHandle(process.hProcess);
  if (wait_result != WAIT_OBJECT_0) {
    remove(output_path);
    set_error_local(error, error_size, "Ancient identify timed out");
    return -1;
  }
  output = fopen(output_path, "rb");
  if (output == NULL) {
    remove(output_path);
    set_error_local(error, error_size, "failed reading Ancient identify output");
    return -1;
  }
  while (fgets(line, sizeof(line), output) != NULL) {
    trim_line_local(line);
    (void)ancient_parse_identify_output_local(line, out_result);
  }
  fclose(output);
  remove(output_path);
#else
  snprintf(command, sizeof(command), "%s identify %s 2>/dev/null", quoted_exe, quoted_input);
  pipe = PLATFORM_POPEN(command, "r");
  if (pipe == NULL) {
    set_error_local(error, error_size, "failed running Ancient identify");
    return -1;
  }
  while (fgets(line, sizeof(line), pipe) != NULL) {
    trim_line_local(line);
    (void)ancient_parse_identify_output_local(line, out_result);
  }
  status = PLATFORM_PCLOSE(pipe);
  (void)status;
#endif
  return 0;
}

static int ancient_decompress_temp_file_local(const char *ancient_path, const char *temp_path,
    const char *output_path, char *error, size_t error_size) {
  char quoted_exe[640];
  char quoted_input[640];
  char quoted_output[640];
  char command[2050];
#ifdef _WIN32
  STARTUPINFOA startup;
  PROCESS_INFORMATION process;
  DWORD wait_result;
  DWORD exit_code = 1U;
#else
  int status;
#endif
  if (!quote_arg_local(quoted_exe, sizeof(quoted_exe), ancient_path) ||
      !quote_arg_local(quoted_input, sizeof(quoted_input), temp_path) ||
      !quote_arg_local(quoted_output, sizeof(quoted_output), output_path)) {
    set_error_local(error, error_size, "failed quoting Ancient decompress command");
    return -1;
  }
#ifdef _WIN32
  snprintf(command, sizeof(command), "cmd.exe /d /c \"%s decompress %s %s >NUL 2>NUL\"", quoted_exe, quoted_input,
    quoted_output);
  memset(&startup, 0, sizeof(startup));
  memset(&process, 0, sizeof(process));
  startup.cb = sizeof(startup);
  if (!CreateProcessA(NULL, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &startup, &process)) {
    set_error_local(error, error_size, "failed running Ancient decompression");
    return -1;
  }
  wait_result = WaitForSingleObject(process.hProcess, 30000U);
  if (wait_result == WAIT_OBJECT_0) (void)GetExitCodeProcess(process.hProcess, &exit_code);
  else (void)TerminateProcess(process.hProcess, 1U);
  CloseHandle(process.hThread);
  CloseHandle(process.hProcess);
  if (wait_result != WAIT_OBJECT_0) {
    set_error_local(error, error_size, "Ancient decompression timed out");
    return -1;
  }
  if (exit_code != 0U) {
    set_error_local(error, error_size, "Ancient decompression failed");
    return -1;
  }
#else
  snprintf(command, sizeof(command), "%s decompress %s %s >/dev/null 2>/dev/null", quoted_exe, quoted_input,
    quoted_output);
  status = system(command);
  if (status != 0) {
    set_error_local(error, error_size, "Ancient decompression failed");
    return -1;
  }
#endif
  return 0;
}

int platform_decompression_identify_path_range(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, PlatformDecompressionIdentifyResult *out_result,
    char *error, size_t error_size) {
  char temp_path[512];
  const char *actual_provider_id;
  const char *actual_provider_path;
  int result;
  if (out_result == NULL) return -1;
  platform_decompression_identify_result_init(out_result);
  if (path == NULL || size == 0U) {
    set_error_local(error, error_size, "invalid decompression identify range");
    return -1;
  }
  actual_provider_id = (provider_id != NULL && provider_id[0] != '\0') ? provider_id : "ancient-cli";
  actual_provider_path = (provider_path != NULL && provider_path[0] != '\0') ? provider_path : default_ancient_path_local();
  if (strcmp(actual_provider_id, "ancient-cli") != 0) {
    set_error_local(error, error_size, "unsupported decompression provider");
    return -1;
  }
  snprintf(out_result->provider_id, sizeof(out_result->provider_id), "%s", actual_provider_id);
  snprintf(out_result->provider_path, sizeof(out_result->provider_path), "%s", actual_provider_path);
  out_result->source_offset = offset;
  out_result->packed_size = size;
  temp_path[0] = '\0';
  if (write_file_range_local(path, offset, size, temp_path, sizeof(temp_path), error, error_size) != 0) return -1;
  (void)file_sha256_hex_local(temp_path, NULL, out_result->source_sha256);
  result = ancient_identify_temp_file_local(actual_provider_path, temp_path, out_result, error, error_size);
  remove(temp_path);
  return result;
}

int platform_decompression_identify_buffer_range(const char *provider_id, const char *provider_path,
    const uint8_t *data, uint32_t data_size, uint32_t offset, uint32_t size,
    PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size) {
  char temp_path[512];
  const char *actual_provider_id;
  const char *actual_provider_path;
  int result;
  uint32_t candidate_size = 0U;
  if (out_result == NULL) return -1;
  platform_decompression_identify_result_init(out_result);
  actual_provider_id = (provider_id != NULL && provider_id[0] != '\0') ? provider_id : "ancient-cli";
  actual_provider_path = (provider_path != NULL && provider_path[0] != '\0') ? provider_path : default_ancient_path_local();
  if (strcmp(actual_provider_id, "ancient-cli") != 0) {
    set_error_local(error, error_size, "unsupported decompression provider");
    return -1;
  }
  snprintf(out_result->provider_id, sizeof(out_result->provider_id), "%s", actual_provider_id);
  snprintf(out_result->provider_path, sizeof(out_result->provider_path), "%s", actual_provider_path);
  out_result->source_offset = offset;
  out_result->packed_size = size;
  temp_path[0] = '\0';
  if (write_buffer_range_local(data, data_size, offset, size, temp_path, sizeof(temp_path), error, error_size) != 0)
    return -1;
  (void)file_sha256_hex_local(temp_path, NULL, out_result->source_sha256);
  result = ancient_identify_temp_file_local(actual_provider_path, temp_path, out_result, error, error_size);
  if (result == 0 && !out_result->found &&
      ancient_rnc_candidate_size_local(data, data_size, offset, &candidate_size, NULL, 0U) &&
      candidate_size == size) {
    result = ancient_identify_temp_file_local(actual_provider_path, temp_path, out_result, error, error_size);
  }
  remove(temp_path);
  return result;
}

int platform_decompression_decompress_path_range(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, const char *output_path,
    PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size) {
  char temp_path[512];
  const char *actual_provider_id;
  const char *actual_provider_path;
  int result;
  if (out_result == NULL) return -1;
  platform_decompression_identify_result_init(out_result);
  if (path == NULL || output_path == NULL || output_path[0] == '\0' || size == 0U) {
    set_error_local(error, error_size, "invalid decompression range");
    return -1;
  }
  actual_provider_id = (provider_id != NULL && provider_id[0] != '\0') ? provider_id : "ancient-cli";
  actual_provider_path = (provider_path != NULL && provider_path[0] != '\0') ? provider_path : default_ancient_path_local();
  if (strcmp(actual_provider_id, "ancient-cli") != 0) {
    set_error_local(error, error_size, "unsupported decompression provider");
    return -1;
  }
  snprintf(out_result->provider_id, sizeof(out_result->provider_id), "%s", actual_provider_id);
  snprintf(out_result->provider_path, sizeof(out_result->provider_path), "%s", actual_provider_path);
  snprintf(out_result->decompressed_path, sizeof(out_result->decompressed_path), "%s", output_path);
  out_result->source_offset = offset;
  out_result->packed_size = size;
  temp_path[0] = '\0';
  if (write_file_range_local(path, offset, size, temp_path, sizeof(temp_path), error, error_size) != 0) return -1;
  (void)file_sha256_hex_local(temp_path, NULL, out_result->source_sha256);
  result = ancient_identify_temp_file_local(actual_provider_path, temp_path, out_result, error, error_size);
  if (result == 0 && !out_result->found) {
    remove(temp_path);
    return 0;
  }
  if (result == 0) result = ancient_decompress_temp_file_local(actual_provider_path, temp_path, output_path,
    error, error_size);
  remove(temp_path);
  if (result != 0) return result;
  if (file_sha256_hex_local(output_path, &out_result->decompressed_size, out_result->decompressed_sha256) != 0) {
    set_error_local(error, error_size, "failed hashing decompressed output");
    return -1;
  }
  out_result->decompressed = 1;
  return 0;
}

int platform_decompression_decompress_buffer_range(const char *provider_id, const char *provider_path,
    const uint8_t *data, uint32_t data_size, uint32_t offset, uint32_t size, const char *output_path,
    PlatformDecompressionIdentifyResult *out_result, char *error, size_t error_size) {
  char temp_path[512];
  const char *actual_provider_id;
  const char *actual_provider_path;
  int result;
  uint32_t candidate_size = 0U;
  if (out_result == NULL) return -1;
  platform_decompression_identify_result_init(out_result);
  if (output_path == NULL || output_path[0] == '\0') {
    set_error_local(error, error_size, "invalid decompression output path");
    return -1;
  }
  actual_provider_id = (provider_id != NULL && provider_id[0] != '\0') ? provider_id : "ancient-cli";
  actual_provider_path = (provider_path != NULL && provider_path[0] != '\0') ? provider_path : default_ancient_path_local();
  if (strcmp(actual_provider_id, "ancient-cli") != 0) {
    set_error_local(error, error_size, "unsupported decompression provider");
    return -1;
  }
  snprintf(out_result->provider_id, sizeof(out_result->provider_id), "%s", actual_provider_id);
  snprintf(out_result->provider_path, sizeof(out_result->provider_path), "%s", actual_provider_path);
  snprintf(out_result->decompressed_path, sizeof(out_result->decompressed_path), "%s", output_path);
  out_result->source_offset = offset;
  out_result->packed_size = size;
  temp_path[0] = '\0';
  if (write_buffer_range_local(data, data_size, offset, size, temp_path, sizeof(temp_path), error, error_size) != 0)
    return -1;
  (void)file_sha256_hex_local(temp_path, NULL, out_result->source_sha256);
  result = ancient_identify_temp_file_local(actual_provider_path, temp_path, out_result, error, error_size);
  if (result == 0 && !out_result->found &&
      ancient_rnc_candidate_size_local(data, data_size, offset, &candidate_size, NULL, 0U) &&
      candidate_size == size) {
    result = ancient_identify_temp_file_local(actual_provider_path, temp_path, out_result, error, error_size);
  }
  if (result == 0 && !out_result->found) {
    remove(temp_path);
    return 0;
  }
  if (result == 0) result = ancient_decompress_temp_file_local(actual_provider_path, temp_path, output_path,
    error, error_size);
  remove(temp_path);
  if (result != 0) return result;
  if (file_sha256_hex_local(output_path, &out_result->decompressed_size, out_result->decompressed_sha256) != 0) {
    set_error_local(error, error_size, "failed hashing decompressed output");
    return -1;
  }
  out_result->decompressed = 1;
  return 0;
}

int platform_decompression_append_result_json(JsonBuilder *builder,
    const PlatformDecompressionIdentifyResult *result) {
  if (json_builder_append(builder, "{\"provider_id\":") != 0) return -1;
  if (json_builder_append_json_string(builder, result->provider_id) != 0) return -1;
  if (json_builder_append(builder, ",\"provider_path\":") != 0) return -1;
  if (json_builder_append_json_string(builder, result->provider_path) != 0) return -1;
  if (json_builder_appendf(builder, ",\"found\":%s", result->found ? "true" : "false") != 0) return -1;
  if (json_builder_appendf(builder, ",\"source_offset\":%u,\"packed_size\":%u",
      (unsigned)result->source_offset, (unsigned)result->packed_size) != 0) return -1;
  if (result->has_source_section) {
    if (json_builder_appendf(builder, ",\"source_section\":%u,\"source_section_offset\":%u",
        (unsigned)result->source_section_index, (unsigned)result->source_section_offset) != 0)
      return -1;
  }
  if (result->source_sha256[0] != '\0') {
    if (json_builder_append(builder, ",\"source_sha256\":") != 0) return -1;
    if (json_builder_append_json_string(builder, result->source_sha256) != 0) return -1;
  }
  if (result->found) {
    if (json_builder_append(builder, ",\"codec_id\":") != 0) return -1;
    if (json_builder_append_json_string(builder, result->codec_id) != 0) return -1;
    if (json_builder_append(builder, ",\"codec_name\":") != 0) return -1;
    if (json_builder_append_json_string(builder, result->codec_name) != 0) return -1;
    if (json_builder_append(builder, ",\"confidence\":") != 0) return -1;
    if (json_builder_append_json_string(builder, result->confidence) != 0) return -1;
    if (result->decompressed) {
      if (json_builder_appendf(builder, ",\"decompressed_size\":%u", (unsigned)result->decompressed_size) != 0)
        return -1;
      if (json_builder_append(builder, ",\"decompressed_sha256\":") != 0) return -1;
      if (json_builder_append_json_string(builder, result->decompressed_sha256) != 0) return -1;
      if (result->decompressed_path[0] != '\0') {
        if (json_builder_append(builder, ",\"decompressed_path\":") != 0) return -1;
        if (json_builder_append_json_string(builder, result->decompressed_path) != 0) return -1;
      }
    }
  }
  return json_builder_append(builder, "}");
}

int platform_decompression_identify_path_range_json_alloc(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, char **out_text) {
  PlatformDecompressionIdentifyResult result;
  JsonBuilder builder;
  char error[256];
  char *text;
  int identify_result;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  error[0] = '\0';
  identify_result = platform_decompression_identify_path_range(provider_id, provider_path, path, offset, size,
    &result, error, sizeof(error));
  if (json_builder_create(&builder) != 0) return -1;
  if (identify_result != 0) {
    if (json_builder_append(&builder, "{\"status\":\"error\",\"error\":") != 0 ||
        json_builder_append_json_string(&builder, error[0] != '\0' ? error : "decompression identify failed") != 0 ||
        json_builder_append(&builder, "}") != 0) {
      json_builder_destroy(&builder);
      return -1;
    }
  } else {
    if (json_builder_append(&builder, "{\"status\":\"ok\",\"packed_payloads\":[") != 0 ||
        platform_decompression_append_result_json(&builder, &result) != 0 ||
        json_builder_append(&builder, "]}") != 0) {
      json_builder_destroy(&builder);
      return -1;
    }
  }
  text = json_builder_build(&builder);
  json_builder_destroy(&builder);
  if (text == NULL) return -1;
  *out_text = text;
  return identify_result;
}

int platform_decompression_decompress_path_range_json_alloc(const char *provider_id, const char *provider_path,
    const char *path, uint32_t offset, uint32_t size, const char *output_path, char **out_text) {
  PlatformDecompressionIdentifyResult result;
  JsonBuilder builder;
  char error[256];
  char *text;
  int decompress_result;
  if (out_text == NULL) return -1;
  *out_text = NULL;
  error[0] = '\0';
  decompress_result = platform_decompression_decompress_path_range(provider_id, provider_path, path, offset, size,
    output_path, &result, error, sizeof(error));
  if (json_builder_create(&builder) != 0) return -1;
  if (decompress_result != 0) {
    if (json_builder_append(&builder, "{\"status\":\"error\",\"error\":") != 0 ||
        json_builder_append_json_string(&builder, error[0] != '\0' ? error : "decompression failed") != 0 ||
        json_builder_append(&builder, "}") != 0) {
      json_builder_destroy(&builder);
      return -1;
    }
  } else {
    if (json_builder_append(&builder, "{\"status\":\"ok\",\"packed_payloads\":[") != 0 ||
        platform_decompression_append_result_json(&builder, &result) != 0 ||
        json_builder_append(&builder, "]}") != 0) {
      json_builder_destroy(&builder);
      return -1;
    }
  }
  text = json_builder_build(&builder);
  json_builder_destroy(&builder);
  if (text == NULL) return -1;
  *out_text = text;
  return decompress_result;
}

void platform_decompression_free_text(char *text) {
  free(text);
}

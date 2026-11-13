#include "platform_disk_lib.h"

#include <stdio.h>
#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

static int inspect_disk_to_stdout(const char *platform_name, const char *path) {
    PlatformDiskTextResult result = platform_disk_inspect_path_json(platform_name, path);
    if (m68k_diag_has_errors(&result.diagnostics)) {
        fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
        return 1;
    }
    puts(result.text);
    platform_disk_free_text(result.text);
    return 0;
}

static int write_bytes_to_stdout(PlatformDiskBufferResult result) {
    if (m68k_diag_has_errors(&result.diagnostics)) {
        fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
        platform_disk_free_bytes(result.data);
        return 1;
    }
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (result.size != 0U && fwrite(result.data, 1, result.size, stdout) != result.size) {
        platform_disk_free_bytes(result.data);
        fprintf(stderr, "failed writing extracted bytes\n");
        return 1;
    }
    platform_disk_free_bytes(result.data);
    return 0;
}

static int parse_index(const char *text, size_t *out) {
    unsigned long long value;
    char *end;
    if (*text < '0' || *text > '9') return -1;
    errno = 0; value = strtoull(text, &end, 10);
    if (errno || *end || value > SIZE_MAX) return -1;
    *out = (size_t)value;
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "inspect-disk") == 0) return inspect_disk_to_stdout(argv[2], argv[3]);
    if (argc == 5 && strcmp(argv[1], "extract-entry") == 0) return write_bytes_to_stdout(platform_disk_extract_entry_path(argv[2], argv[3], argv[4]));
    if (argc == 5 && strcmp(argv[1], "extract-stx-sector") == 0) {
        size_t track_index, sector_index;
        if (parse_index(argv[3], &track_index) == 0 && parse_index(argv[4], &sector_index) == 0)
            return write_bytes_to_stdout(platform_disk_extract_stx_sector_path(argv[2], track_index, sector_index));
        fprintf(stderr, "STX indexes must be non-negative decimal integers\n");
        return 2;
    }
    fprintf(stderr, "usage: %s inspect-disk <amiga-disk|atari-st-disk> <image>\n", argv[0]);
    fprintf(stderr, "   or: %s extract-entry <amiga-disk|atari-st-disk> <image> <entry-path>\n", argv[0]);
    fprintf(stderr, "   or: %s extract-stx-sector <image> <track-index> <sector-index>\n", argv[0]);
    return 2;
}

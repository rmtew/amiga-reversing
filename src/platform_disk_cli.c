#include "platform_disk_lib.h"

#include <stdio.h>
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

static int extract_entry_to_stdout(const char *platform_name, const char *path, const char *entry_path) {
    PlatformDiskBufferResult result = platform_disk_extract_entry_path(platform_name, path, entry_path);
    if (m68k_diag_has_errors(&result.diagnostics)) {
        fprintf(stderr, "%s\n", m68k_diag_first_message(&result.diagnostics));
        return 1;
    }
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (result.size != 0U && fwrite(result.data, 1, result.size, stdout) != result.size) {
        platform_disk_free_bytes(result.data);
        fprintf(stderr, "failed writing extracted entry\n");
        return 1;
    }
    platform_disk_free_bytes(result.data);
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "inspect-disk") == 0) return inspect_disk_to_stdout(argv[2], argv[3]);
    if (argc == 5 && strcmp(argv[1], "extract-entry") == 0) return extract_entry_to_stdout(argv[2], argv[3], argv[4]);
    fprintf(stderr, "usage: %s inspect-disk <amiga-disk|atari-st-disk> <image>\n", argv[0]);
    fprintf(stderr, "   or: %s extract-entry <amiga-disk|atari-st-disk> <image> <entry-path>\n", argv[0]);
    return 2;
}

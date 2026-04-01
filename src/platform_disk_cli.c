#include "platform_disk_lib.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int inspect_disk_to_stdout(const char *platform_name, const char *path) {
    char *json = NULL;
    char error[256];
    if (platform_disk_inspect_path_json(platform_name, path, &json, error, sizeof(error)) != 0) {
        fprintf(stderr, "%s\n", error);
        return 1;
    }
    puts(json);
    platform_disk_free_json(json);
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "inspect-disk") == 0) return inspect_disk_to_stdout(argv[2], argv[3]);
    fprintf(stderr, "usage: %s inspect-disk <amiga-disk|atari-st-disk> <image>\n", argv[0]);
    return 2;
}

/*
 * resourcefork.c
 * author: Matt Jacobson
 * date: September 2024
 */

#include "resourcefork.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef NDIF2RAW_HAS_CORESERVICES
#include <CoreServices/CoreServices.h>

uint8_t *read_resource_fork(const char *const filename, const ResType type, const ResID id, size_t *const size_out) {
    OSStatus err;
    FSRef ref;

    err = FSPathMakeRef((UInt8 *)filename, &ref, NULL);
    assert(err == noErr);

    const ResFileRefNum rsrc = FSOpenResFile(&ref, fsRdPerm);
    UseResFile(rsrc);
    const Handle handle = GetResource(type, id);
    assert(handle);
    const Size size = GetHandleSize(handle);

    uint8_t *const buffer = malloc(size);
    assert(buffer);
    memcpy(buffer, *handle, size);

    ReleaseResource(handle);
    CloseResFile(rsrc);

    if (size_out) *size_out = size;
    return buffer;
}

#else /* NDIF2RAW_HAS_CORESERVICES */

uint8_t *read_resource_fork(const char *const filename, const ResType type, const ResID id, size_t *const size_out) {
    (void)filename;
    (void)type;
    (void)id;
    (void)size_out;
    fprintf(stderr, "ERROR: reading a Macintosh resource fork is not supported on this machine\n");
    return NULL;
}

#endif /* NDIF2RAW_HAS_CORESERVICES */

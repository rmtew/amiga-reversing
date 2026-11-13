#ifndef PLATFORM_ATARI_STX_H
#define PLATFORM_ATARI_STX_H

#include "m68k_diagnostics.h"
#include <stddef.h>
#include <stdint.h>

/* All ranges use original STX file coordinates. Bytes remain caller-owned and
 * immutable for the lifetime of the analysis. Physical array indexes are the
 * identities; CHRN alone need not identify a track or sector instance. */
#define ATARI_STX_NO_OFFSET UINT32_MAX
#ifdef _WIN32
#define ATARI_STX_API __declspec(dllexport)
#else
#define ATARI_STX_API
#endif

typedef struct AtariStxSector {
    uint32_t header_offset, data_relative_offset, offset, size, fuzzy_offset;
    uint32_t timing_offset, timing_bytes;
    uint16_t bit_position, read_time, id_crc;
    uint8_t id_track, id_head, id_sector, id_size, status, reserved;
    uint8_t implicit_timing; /* revision 0 Speedlock/Macrodos, no stored table */
} AtariStxSector;

typedef struct AtariStxTrack {
    uint32_t offset, size, fuzzy_offset, fuzzy_size, data_offset;
    uint32_t image_offset, image_size, timing_offset, tail_offset, tail_size;
    uint16_t flags, mfm_size, sync, timing_flags, timing_size, sector_count;
    uint8_t track, side, record_type;
    AtariStxSector *sectors;
} AtariStxTrack;

typedef struct AtariStxAnalysis {
    const unsigned char *data;
    size_t size;
    uint16_t version, imaging_tool, reserved1;
    uint32_t reserved2;
    uint8_t revision, track_count;
    AtariStxTrack *tracks;
} AtariStxAnalysis;

typedef enum AtariStxReadResult {
    ATARI_STX_READ_OK = 0,
    ATARI_STX_READ_NOT_FOUND,
    ATARI_STX_READ_AMBIGUOUS,
    ATARI_STX_READ_NO_DATA,
    ATARI_STX_READ_FUZZY,
    ATARI_STX_READ_STATUS,
    ATARI_STX_READ_UNSUPPORTED
} AtariStxReadResult;

ATARI_STX_API int atari_stx_is_image(const unsigned char *data, size_t size);
/* Pass an empty or destroyed output. On failure it is empty and destroy
 * remains safe. Version 3 revisions 0/2. */
ATARI_STX_API int atari_stx_analyze(const unsigned char *data, size_t size, AtariStxAnalysis *out,
    M68kDiagSink diagnostics);
ATARI_STX_API void atari_stx_destroy(AtariStxAnalysis *analysis);
/* Returns stored stable bytes, not an emulated FDC transaction. It refuses
 * duplicate matches, missing/fuzzy data, nonzero status and unknown flags.
 * Outputs are cleared on every failure. Explicit raw ranges remain available
 * to loader/protection analysis, without being claimed as deterministic reads. */
ATARI_STX_API AtariStxReadResult atari_stx_read_chrn(const AtariStxAnalysis *analysis,
    unsigned track, unsigned side, unsigned c, unsigned h, unsigned r, unsigned n,
    const unsigned char **out_data, size_t *out_size);
ATARI_STX_API AtariStxReadResult atari_stx_read_instance(const AtariStxAnalysis *analysis,
    size_t track_index, size_t sector_index, const unsigned char **out_data, size_t *out_size);
#endif

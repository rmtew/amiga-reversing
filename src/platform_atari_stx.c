#include "platform_atari_stx.h"
#include "generated/atari_st_disk_file_runtime.h"
#include <stdlib.h>
#include <string.h>

#define LIMIT(name) ATARI_ST_DISK_FILE_STX_LIMITS_##name
#define TF(name) ATARI_ST_DISK_FILE_STX_TRACK_FLAGS_##name
#define SF(name) ATARI_ST_DISK_FILE_STX_SECTOR_FLAGS_##name
#define FIELD(type, name) ATARI_ST_DISK_FILE_STX_##type##_FIELD_##name##_OFFSET

static uint16_t le16(const unsigned char *p) {
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static int fits(size_t offset, size_t length, size_t end) {
    return offset <= end && length <= end - offset;
}
int atari_stx_is_image(const unsigned char *data, size_t size) {
    return data != NULL && size >= 4 && memcmp(data, "RSY\0", 4) == 0;
}
void atari_stx_destroy(AtariStxAnalysis *a) {
    size_t i;
    if (a == NULL) return;
    if (a->tracks != NULL) for (i = 0; i < a->track_count; ++i) free(a->tracks[i].sectors);
    free(a->tracks);
    memset(a, 0, sizeof(*a));
}

int atari_stx_analyze(const unsigned char *data, size_t size, AtariStxAnalysis *out,
    M68kDiagSink diagnostics) {
    AtariStxAnalysis a = {0};
    size_t pos = LIMIT(HEADER_BYTES), ti;
    const char *error = "invalid STX header";
    if (out == NULL) goto fail;
    memset(out, 0, sizeof(*out));
    if (!atari_stx_is_image(data, size) || size < LIMIT(HEADER_BYTES) || size >= UINT32_MAX) goto fail;
    a.version = le16(data + FIELD(HEADER, VERSION));
    a.imaging_tool = le16(data + FIELD(HEADER, TOOL));
    a.reserved1 = le16(data + FIELD(HEADER, RESERVED1));
    a.reserved2 = le32(data + FIELD(HEADER, RESERVED2));
    a.track_count = data[FIELD(HEADER, TRACK_COUNT)];
    a.revision = data[FIELD(HEADER, REVISION)];
    error = "unsupported STX version or revision";
    if (a.version != LIMIT(VERSION) || (a.revision != 0 && a.revision != 2)) goto fail;
    error = "truncated STX track headers";
    if (a.track_count > (size - pos) / LIMIT(TRACK_HEADER_BYTES)) goto fail;
    a.data = data; a.size = size;
    a.tracks = calloc(a.track_count ? a.track_count : 1, sizeof(*a.tracks));
    error = "out of memory reading STX";
    if (a.tracks == NULL) goto fail;
    for (ti = 0; ti < a.track_count; ++ti) {
        AtariStxTrack *t = &a.tracks[ti];
        const unsigned char *p;
        size_t end, cursor, si, fuzzy_used = 0, timing_bytes = 0, used_end;
        error = "invalid STX track bounds";
        if (!fits(pos, LIMIT(TRACK_HEADER_BYTES), size)) goto fail;
        p = data + pos;
        t->offset = (uint32_t)pos;
        t->size = le32(p + FIELD(TRACK, RECORD_SIZE));
        t->fuzzy_size = le32(p + FIELD(TRACK, FUZZY_SIZE));
        t->sector_count = le16(p + FIELD(TRACK, SECTOR_COUNT));
        t->flags = le16(p + FIELD(TRACK, FLAGS));
        t->mfm_size = le16(p + FIELD(TRACK, MFM_SIZE));
        t->track = p[FIELD(TRACK, NUMBER)] & 127;
        t->side = p[FIELD(TRACK, NUMBER)] >> 7;
        t->record_type = p[FIELD(TRACK, RECORD_TYPE)];
        t->image_offset = t->timing_offset = ATARI_STX_NO_OFFSET;
        if (t->size < LIMIT(TRACK_HEADER_BYTES) || !fits(pos, t->size, size)) goto fail;
        end = pos + t->size; cursor = pos + LIMIT(TRACK_HEADER_BYTES);
        error = "STX sync flag requires a track image";
        if ((t->flags & TF(IMAGE_SYNC)) && !(t->flags & TF(IMAGE))) goto fail;
        error = "invalid STX sector descriptor count";
        if (t->flags & TF(SECTOR_DESCRIPTORS)) {
            if (t->sector_count > (end - cursor) / LIMIT(SECTOR_HEADER_BYTES)) goto fail;
            cursor += (size_t)t->sector_count * LIMIT(SECTOR_HEADER_BYTES);
        } else {
            /* Implicit sectors have no recorded CRC, position or time. Do not
             * fabricate the FDC defaults an emulator would supply. */
            error = "invalid STX simple track layout";
            if (t->sector_count > 255 || t->fuzzy_size || (t->flags & (TF(IMAGE) | TF(IMAGE_SYNC))) ||
                (size_t)t->sector_count * LIMIT(SIMPLE_SECTOR_BYTES) != end - cursor) goto fail;
        }
        error = "invalid STX fuzzy range";
        if (!fits(cursor, t->fuzzy_size, end)) goto fail;
        t->fuzzy_offset = (uint32_t)cursor;
        cursor += t->fuzzy_size; t->data_offset = (uint32_t)cursor;
        if (t->flags & TF(IMAGE)) {
            size_t header_size = (t->flags & TF(IMAGE_SYNC)) ? 4 : 2;
            error = "truncated STX track image";
            if (!fits(cursor, header_size, end)) goto fail;
            if (header_size == 4) t->sync = le16(data + cursor);
            t->image_size = le16(data + cursor + header_size - 2);
            cursor += header_size; t->image_offset = (uint32_t)cursor;
            if (!fits(cursor, t->image_size, end)) goto fail;
            cursor += t->image_size;
        }
        used_end = cursor;
        if (t->sector_count) {
            error = "out of memory reading STX sectors";
            t->sectors = calloc(t->sector_count, sizeof(*t->sectors));
            if (t->sectors == NULL) goto fail;
        }
        for (si = 0; si < t->sector_count; ++si) {
            AtariStxSector *s = &t->sectors[si];
            size_t sector_end;
            s->header_offset = s->offset = s->fuzzy_offset = s->timing_offset = ATARI_STX_NO_OFFSET;
            if (t->flags & TF(SECTOR_DESCRIPTORS)) {
                s->header_offset = (uint32_t)(pos + LIMIT(TRACK_HEADER_BYTES) + si * LIMIT(SECTOR_HEADER_BYTES));
                p = data + s->header_offset;
                s->data_relative_offset = le32(p + FIELD(SECTOR, DATA_OFFSET));
                s->bit_position = le16(p + FIELD(SECTOR, BIT_POSITION));
                s->read_time = le16(p + FIELD(SECTOR, READ_TIME));
                s->id_track = p[FIELD(SECTOR, ID_TRACK)]; s->id_head = p[FIELD(SECTOR, ID_HEAD)];
                s->id_sector = p[FIELD(SECTOR, ID_SECTOR)]; s->id_size = p[FIELD(SECTOR, ID_SIZE)];
                s->id_crc = (uint16_t)((p[FIELD(SECTOR, ID_CRC_BE)] << 8) | p[FIELD(SECTOR, ID_CRC_BE) + 1]);
                s->status = p[FIELD(SECTOR, STATUS)]; s->reserved = p[FIELD(SECTOR, RESERVED)];
            } else {
                s->data_relative_offset = (uint32_t)(si * LIMIT(SIMPLE_SECTOR_BYTES));
                s->id_track = t->track; s->id_head = t->side; s->id_sector = (uint8_t)(si + 1); s->id_size = 2;
            }
            if (s->status & SF(NO_DATA)) continue;
            s->size = 128U << (s->id_size & LIMIT(SIZE_CODE_MASK));
            error = "STX sector data outside its track";
            if (!fits(t->data_offset, s->data_relative_offset, end)) goto fail;
            s->offset = t->data_offset + s->data_relative_offset;
            if (!fits(s->offset, s->size, end)) goto fail;
            sector_end = (size_t)s->offset + s->size;
            if (sector_end > used_end) used_end = sector_end;
            if (s->status & SF(FUZZY)) {
                error = "STX fuzzy mask shorter than sector masks";
                if (!fits(fuzzy_used, s->size, t->fuzzy_size)) goto fail;
                s->fuzzy_offset = t->fuzzy_offset + (uint32_t)fuzzy_used;
                fuzzy_used += s->size;
            }
            if (s->status & SF(VARIABLE_TIME)) {
                s->timing_bytes = s->size / LIMIT(TIMING_CHUNK_BYTES) * LIMIT(TIMING_ENTRY_BYTES);
                if (a.revision == 0) s->implicit_timing = 1;
                else timing_bytes += s->timing_bytes;
            }
        }
        error = "STX fuzzy mask size does not match sector masks";
        if (fuzzy_used != t->fuzzy_size) goto fail;
        if (timing_bytes) {
            size_t timing_cursor;
            error = "truncated STX timing record";
            if (!fits(used_end, LIMIT(TIMING_HEADER_BYTES), end)) goto fail;
            t->timing_offset = (uint32_t)used_end;
            t->timing_flags = le16(data + used_end + FIELD(TIMING, FLAGS));
            t->timing_size = le16(data + used_end + FIELD(TIMING, SIZE));
            if (t->timing_size < LIMIT(TIMING_HEADER_BYTES) ||
                !fits(used_end, t->timing_size, end) ||
                timing_bytes != t->timing_size - LIMIT(TIMING_HEADER_BYTES)) goto fail;
            timing_cursor = used_end + LIMIT(TIMING_HEADER_BYTES);
            for (si = 0; si < t->sector_count; ++si) {
                AtariStxSector *s = &t->sectors[si];
                if (s->timing_bytes) { s->timing_offset = (uint32_t)timing_cursor; timing_cursor += s->timing_bytes; }
            }
            used_end += t->timing_size;
        }
        /* Preserve padding/unknown tail as a source range, never discard it. */
        t->tail_offset = (uint32_t)used_end; t->tail_size = (uint32_t)(end - used_end);
        pos = end;
    }
    error = "STX track count leaves trailing file bytes";
    if (pos != size) goto fail;
    *out = a;
    return 0;
fail:
    atari_stx_destroy(&a);
    m68k_diag_add(diagnostics, M68K_DIAG_SEVERITY_ERROR, M68K_DIAG_CODE_PLATFORM_DISK_FAILED, error);
    return -1;
}

static AtariStxReadResult read_sector(const AtariStxAnalysis *a, const AtariStxTrack *t,
    const AtariStxSector *s, const unsigned char **out_data, size_t *out_size) {
    if (s->status & SF(NO_DATA)) return ATARI_STX_READ_NO_DATA;
    if (s->status & SF(FUZZY)) return ATARI_STX_READ_FUZZY;
    /* Bit 5 is a preserved legacy track marker, used by the supplied image. */
    if ((t->flags & ~(TF(SECTOR_DESCRIPTORS) | TF(IMAGE) | TF(IMAGE_SYNC) | TF(LEGACY_MARKER))) ||
        (t->record_type != 0 && t->record_type != 0xcc) || s->reserved) return ATARI_STX_READ_UNSUPPORTED;
    /* Upper size-ID bits are intentional on some media. Storage uses the
     * documented low two bits; exact CHRN matching still retains all bits. */
    if (s->status) return ATARI_STX_READ_STATUS;
    if (out_data) *out_data = a->data + s->offset;
    if (out_size) *out_size = s->size;
    return ATARI_STX_READ_OK;
}
AtariStxReadResult atari_stx_read_instance(const AtariStxAnalysis *a,
    size_t ti, size_t si, const unsigned char **out_data, size_t *out_size) {
    if (out_data) *out_data = NULL;
    if (out_size) *out_size = 0;
    if (a == NULL || ti >= a->track_count || si >= a->tracks[ti].sector_count) return ATARI_STX_READ_NOT_FOUND;
    return read_sector(a, &a->tracks[ti], &a->tracks[ti].sectors[si], out_data, out_size);
}
AtariStxReadResult atari_stx_read_chrn(const AtariStxAnalysis *a,
    unsigned track, unsigned side, unsigned c, unsigned h, unsigned r, unsigned n,
    const unsigned char **out_data, size_t *out_size) {
    size_t ti, si, found_t = 0, found_s = 0, count = 0;
    if (out_data) *out_data = NULL;
    if (out_size) *out_size = 0;
    if (a == NULL) return ATARI_STX_READ_NOT_FOUND;
    for (ti = 0; ti < a->track_count; ++ti) {
        const AtariStxTrack *t = &a->tracks[ti];
        if (t->track != track || t->side != side) continue;
        for (si = 0; si < t->sector_count; ++si) {
            const AtariStxSector *s = &t->sectors[si];
            if (s->id_track == c && s->id_head == h && s->id_sector == r && s->id_size == n) {
                ++count; found_t = ti; found_s = si;
            }
        }
    }
    if (count == 0) return ATARI_STX_READ_NOT_FOUND;
    if (count != 1) return ATARI_STX_READ_AMBIGUOUS;
    return atari_stx_read_instance(a, found_t, found_s, out_data, out_size);
}

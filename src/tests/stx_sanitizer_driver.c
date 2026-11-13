/* Parser boundary/mutation runner. Built separately with ASan/UBSan by the
 * Python test; it is not linked into product tools. Inputs are synthetic. */
#include "platform_atari_stx.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int check(const unsigned char *bytes, size_t size) {
    AtariStxAnalysis a = {0};
    M68kDiagList diagnostics = {0};
    int result = atari_stx_analyze(bytes, size, &a, m68k_diag_sink(&diagnostics));
    if (result == 0) {
        size_t ti, si;
        for (ti = 0; ti < a.track_count; ++ti) {
            const AtariStxTrack *t = &a.tracks[ti];
            assert(t->offset <= size && t->size <= size - t->offset);
            for (si = 0; si < t->sector_count; ++si) {
                const unsigned char *p = NULL;
                size_t n = 0;
                const AtariStxSector *s = &t->sectors[si];
                if (s->offset != ATARI_STX_NO_OFFSET) {
                    assert(s->offset >= t->offset);
                    assert(s->offset <= t->offset + t->size);
                    assert(s->size <= t->offset + t->size - s->offset);
                }
                if (atari_stx_read_instance(&a, ti, si, &p, &n) == ATARI_STX_READ_OK) {
                    assert(p >= bytes && p <= bytes + size);
                    assert(n <= (size_t)(bytes + size - p));
                    if (n) { volatile unsigned char last = p[n-1]; (void)last; }
                } else assert(p == NULL && n == 0);
            }
        }
    } else assert(a.tracks == NULL && a.track_count == 0);
    atari_stx_destroy(&a);
    atari_stx_destroy(&a);
    return result;
}

int main(int argc, char **argv) {
    int arg;
    check(NULL, 0); check(NULL, 100);
    for (arg = 1; arg < argc; ++arg) {
        FILE *f = fopen(argv[arg], "rb");
        unsigned char *data;
        long length;
        size_t i;
        unsigned bit;
        assert(f && fseek(f, 0, SEEK_END) == 0);
        length = ftell(f); assert(length >= 0 && length <= 65536);
        rewind(f); data = malloc((size_t)length + 1); assert(data);
        assert(fread(data, 1, (size_t)length, f) == (size_t)length); fclose(f);
        assert(check(data, (size_t)length) == 0);
        for (i = 0; i <= (size_t)length; ++i) check(data, i);
        for (i = 0; i < (size_t)length; ++i) {
            for (bit = 0; bit < 8; ++bit) {
                data[i] ^= 1U << bit;
                check(data, (size_t)length);
                data[i] ^= 1U << bit;
            }
        }
        free(data);
    }
    return 0;
}

#!/usr/bin/env python3
"""Read an STX through pinned, external Hatari parser functions. No emulator boot.

Upstream code is compiled in a temporary directory, not vendored. This is an
oracle adapter, not our native parser or a safe validator for arbitrary images.
Address/undefined-behaviour sanitizers remain enabled. Output contains metadata
and byte identities, never disk bytes. Use private paths for original media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

HATARI_REVISION = 'b18511507bcf48dcf11f32b555774ea2f5e93fd0'
MAX_IMAGE = 32 * 1024 * 1024


def function(source: str, name: str) -> str:
    # Hatari places these function definitions and closing braces at column 0.
    matches = list(re.finditer(r'^([^\n;]+\b' + re.escape(name)
                              + r'\s*\([^;]*?\)\s*\{.*?^\})', source, re.M | re.S))
    if len(matches) != 1:
        raise ValueError(f'expected one upstream definition for {name}')
    return matches[0].group(1)


def read_image(path: Path, member: str | None) -> tuple[bytes, str]:
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            candidates = [x for x in archive.infolist()
                          if not x.is_dir() and x.filename.lower().endswith('.stx')]
            if member is not None:
                candidates = [x for x in candidates if x.filename == member]
            if len(candidates) != 1:
                raise ValueError('select exactly one STX member with --member')
            info = candidates[0]
            if info.file_size > MAX_IMAGE:
                raise ValueError('image exceeds probe size limit')
            data, identity = archive.read(info), info.filename
    else:
        if path.stat().st_size > MAX_IMAGE:
            raise ValueError('image exceeds probe size limit')
        data, identity = path.read_bytes(), path.name
    if len(data) < 16 or data[:6] != b'RSY\0\x03\0':
        raise ValueError('expected an STX version-3 header')
    # Bound track records before entering the external parser. This is only a
    # container preflight; sanitizer failures are still hard failures.
    offset = 16
    for _ in range(data[10]):
        if offset + 16 > len(data):
            raise ValueError('truncated track header')
        size = int.from_bytes(data[offset:offset+4], 'little')
        if size < 16 or size > len(data) - offset:
            raise ValueError('invalid track block size')
        offset += size
    if offset != len(data):
        raise ValueError('track records do not account for the entire image')
    return data, identity


DRIVER = r'''
static void Str_Dump_Hex_Ascii(char *p, int n, int w, const char *s, FILE *f)
{ (void)p;(void)n;(void)w;(void)s;(void)f; abort(); }
static long pos(uint8_t *p, uint8_t *b) { return p ? (long)((uintptr_t)p-(uintptr_t)b) : -1; }
int main(int argc, char **argv) {
 if (argc != 2) return 2;
 FILE *f=fopen(argv[1],"rb"); if (!f) return 3;
 if (fseek(f,0,SEEK_END)) return 4;
 long n=ftell(f); if (n<16 || fseek(f,0,SEEK_SET)) return 4;
 uint8_t *b=malloc((size_t)n); if(!b) return 5;
 if(fread(b,1,(size_t)n,f)!=(size_t)n) return 6; fclose(f);
 STX_MAIN_STRUCT *m=STX_BuildStruct(b,0); if (!m) return 7;
 printf("{\"version\":%u,\"revision\":%u,\"imaging_tool\":%u,\"tracks\":[",m->Version,m->Revision,m->ImagingTool);
 long off=16;
 for (unsigned i=0;i<m->TracksCount;i++) {
  STX_TRACK_STRUCT *t=&m->pTracksStruct[i];
  printf("%s{\"offset\":%ld,\"size\":%u,\"track\":%u,\"side\":%u,\"flags\":%u,\"fuzzy_size\":%u,\"mfm_size\":%u,\"record_type\":%u,\"image_offset\":%ld,\"image_size\":%u,\"sync\":%u,\"timing_size\":%u,\"timing_flags\":%u,\"sectors\":[",i?",":"",off,t->BlockSize,t->TrackNumber&127,t->TrackNumber>>7,t->Flags,t->FuzzySize,t->MFMSize,t->RecordType,pos(t->pTrackImageData,b),t->TrackImageSize,t->TrackImageSyncPosition,t->TimingSize,t->TimingFlags);
  for(unsigned j=0;j<t->SectorsCount;j++) {
   STX_SECTOR_STRUCT *s=&t->pSectorsStruct[j];
   printf("%s{\"index\":%u,\"id_track\":%u,\"id_head\":%u,\"id_sector\":%u,\"id_size\":%u,\"id_crc\":%u,\"status\":%u,\"reserved\":%u,\"bit_position\":%u,\"read_time\":%u,\"offset\":%ld,\"size\":%u,\"fuzzy_offset\":%ld,\"timing_offset\":%ld}",j?",":"",j,s->ID_Track,s->ID_Head,s->ID_Sector,s->ID_Size,s->ID_CRC,s->FDC_Status,s->Reserved,s->BitPosition,s->ReadTime,pos(s->pData,b),s->SectorSize,pos(s->pFuzzyData,b),(m->Revision == 0 ? -1 : pos(s->pTimingData,b)));
  }
  printf("]}");off+=t->BlockSize;
 }
 printf("]}\n"); STX_FreeStruct(m); free(b); return 0;
}
'''


def probe(checkout: Path, data: bytes) -> dict:
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != HATARI_REVISION:
        raise ValueError(f'expected Hatari {HATARI_REVISION}, got {revision}')
    paths = ['src/floppies/stx.c', 'src/includes/floppies/stx.h',
             'src/includes/fdc.h', 'src/utils.c', 'src/includes/utils.h']
    for path in paths:
        original = subprocess.check_output(['git', '-C', str(checkout), 'show', 'HEAD:'+path])
        if (checkout/path).read_bytes() != original:
            raise ValueError(f'upstream source modified: {path}')
    source = (checkout/paths[0]).read_text()
    names = ['STX_FreeStruct', 'STX_BuildSectorID_CRC', 'STX_BuildSectorsSimple', 'STX_BuildStruct']
    bodies = {name: function(source, name) for name in names}
    timing = re.search(r'static uint8_t\s+TimingDataDefault\[\]\s*=\s*\{.*?\};', source, re.S).group()
    defines = '\n'.join(line for line in source.splitlines()
                        if line.startswith('#define') and 'STX_DEBUG_FLAG' in line)
    fdc = (checkout/'src/includes/fdc.h').read_text().split('#define\tFDC_IRQ_SOURCE_COMPLETE')[0]
    # Retain only the upstream constants, not the open header guard.
    fdc = fdc[fdc.index('/* Values'):]
    preamble = '#include <stdint.h>\n#include <stdbool.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include "utils.h"\n#include "floppies/stx.h"\n'
    declarations = '\n'.join(body[:body.index('{')].rstrip()+';' for body in bodies.values())
    dump_decl = 'static void Str_Dump_Hex_Ascii(char*,int,int,const char*,FILE*);\n'
    code = preamble+fdc+'\n'+defines+'\n'+timing+'\n'+declarations+'\n'+dump_decl+'\n'+'\n'.join(bodies.values())+'\n'+DRIVER
    with tempfile.TemporaryDirectory(prefix='hatari-stx-') as temp:
        root = Path(temp)
        (root/'probe.c').write_text(code)
        (root/'image.stx').write_bytes(data)
        subprocess.run(['cc', '-std=c11', '-g', '-fsanitize=address,undefined',
                        '-I'+str(checkout/'src/includes'), str(root/'probe.c'),
                        str(checkout/'src/utils.c'), '-o', str(root/'probe')], check=True)
        result = subprocess.run([str(root/'probe'), str(root/'image.stx')], check=True,
                                stdout=subprocess.PIPE, text=True, timeout=30)
    report = json.loads(result.stdout)
    for track in report['tracks']:
        ranges = [(track, 'image_offset', 'image_size')]
        for sector in track['sectors']:
            ranges += [(sector, 'offset', 'size')]
            if sector['fuzzy_offset'] >= 0:
                ranges += [(sector, 'fuzzy_offset', 'size')]
            if sector['timing_offset'] >= 0 and report['revision'] == 2:
                sector['timing_bytes'] = sector['size']//16*2
                ranges += [(sector, 'timing_offset', 'timing_bytes')]
        for record, offset_key, size_key in ranges:
            offset, size = record[offset_key], record[size_key]
            if offset < 0:
                continue
            if not (track['offset'] <= offset <= track['offset']+track['size'] and
                    size <= track['offset']+track['size']-offset):
                raise ValueError('reference returned a range outside its track')
            record[offset_key+'_sha256'] = hashlib.sha256(data[offset:offset+size]).hexdigest()
    report['reference_revision'] = revision
    report['image_sha256'] = hashlib.sha256(data).hexdigest()
    report['image_size'] = len(data)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hatari', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--member')
    args = parser.parse_args()
    before = hashlib.sha256(args.image.read_bytes()).hexdigest()
    data, member = read_image(args.image, args.member)
    report = probe(args.hatari.resolve(), data)
    report['member'] = member
    report['container_sha256'] = before
    if hashlib.sha256(args.image.read_bytes()).hexdigest() != before:
        raise ValueError('input changed during probe')
    print(json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    main()

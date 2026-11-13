"""Synthetic, redistributable STX coverage. No original game bytes needed.

Optional differential checks use external Hatari and private media via env vars.
"""
from __future__ import annotations
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import unittest
import zipfile

from src.tests._platform_disk_test_utils import (
    PlatformDiskTestCaseMixin, M68kDiagList, _diag_has_errors, _diag_message,
)
ROOT = Path(__file__).resolve().parents[2]
NONE = 0xffffffff


def image(*tracks, revision=2):
    return struct.pack('<4sHHHBBI', b'RSY\0', 3, 1, 0, len(tracks), revision, 0) + b''.join(tracks)


def simple(data=bytes(range(256))*2, number=0):
    return struct.pack('<IIHHHBB', 16+len(data), 0, len(data)//512, 0, 6250, number, 0) + data


def detailed(sectors=(), *, number=0, flags=1, track_data=b'', fuzzy=b'',
             track_image=None, sync=0, timing=None, tail=b'', record_type=0):
    """sectors: (relative offset, CHRN, status, reserved, position, read time, CRC)."""
    descriptors = b''.join(struct.pack('<IHH4B', offset, position, read_time, *chrn)
                          + struct.pack('>H', crc) + bytes([status, reserved])
                          for offset, chrn, status, reserved, position, read_time, crc in sectors)
    raw = b''
    if track_image is not None:
        flags |= 64
        if flags & 128:
            raw += struct.pack('<H', sync)
        raw += struct.pack('<H', len(track_image)) + track_image
    raw += track_data
    if timing is not None:
        raw += struct.pack('<HH', 5, len(timing)+4) + timing
    raw += tail
    length = 16 + len(descriptors) + len(fuzzy) + len(raw)
    return struct.pack('<IIHHHBB', length, len(fuzzy), len(sectors), flags, 6250, number, record_type) + descriptors + fuzzy + raw


def sector(offset=0, chrn=(0,0,1,0), status=0, reserved=0, position=123, read_time=456, crc=0xabcd):
    return offset, chrn, status, reserved, position, read_time, crc


class Sector(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint32) for n in ('header_offset','data_relative_offset','offset','size','fuzzy_offset','timing_offset','timing_bytes')] + [(n,ctypes.c_uint16) for n in ('bit_position','read_time','id_crc')] + [(n,ctypes.c_uint8) for n in ('id_track','id_head','id_sector','id_size','status','reserved','implicit_timing')]


class Track(ctypes.Structure):
    _fields_ = [(n,ctypes.c_uint32) for n in ('offset','size','fuzzy_offset','fuzzy_size','data_offset','image_offset','image_size','timing_offset','tail_offset','tail_size')] + [(n,ctypes.c_uint16) for n in ('flags','mfm_size','sync','timing_flags','timing_size','sector_count')] + [(n,ctypes.c_uint8) for n in ('track','side','record_type')] + [('sectors',ctypes.POINTER(Sector))]


class Analysis(ctypes.Structure):
    _fields_ = [('data',ctypes.c_void_p),('size',ctypes.c_size_t),('version',ctypes.c_uint16),('imaging_tool',ctypes.c_uint16),('reserved1',ctypes.c_uint16),('reserved2',ctypes.c_uint32),('revision',ctypes.c_uint8),('track_count',ctypes.c_uint8),('tracks',ctypes.POINTER(Track))]


class Sink(ctypes.Structure):
    _fields_ = [('list',ctypes.POINTER(M68kDiagList))]


class StxTests(PlatformDiskTestCaseMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.library.atari_stx_analyze.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(Analysis),Sink]
        cls.library.atari_stx_analyze.restype = ctypes.c_int
        cls.library.atari_stx_destroy.argtypes = [ctypes.POINTER(Analysis)]
        cls.library.atari_stx_read_chrn.argtypes = [ctypes.POINTER(Analysis)] + [ctypes.c_uint]*6 + [ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_size_t)]
        cls.library.atari_stx_read_chrn.restype = ctypes.c_int
        cls.library.atari_stx_read_instance.argtypes = [ctypes.POINTER(Analysis),ctypes.c_size_t,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_size_t)]
        cls.library.atari_stx_read_instance.restype = ctypes.c_int

    def parse(self, data):
        a, diag = Analysis(), M68kDiagList()
        raw = ctypes.create_string_buffer(data)
        result = self.library.atari_stx_analyze(raw, len(data), ctypes.byref(a), Sink(ctypes.pointer(diag)))
        return result, a, diag, raw

    def reject(self, data):
        rc,a,diag,raw = self.parse(data)
        try:
            self.assertNotEqual(rc,0)
            self.assertTrue(_diag_has_errors(diag), _diag_message(diag))
            self.assertFalse(a.tracks)
            self.assertEqual(a.track_count,0)
        finally:
            self.library.atari_stx_destroy(ctypes.byref(a))

    def read(self, data, chrn=(0,0,0,0,1,0), instance=None):
        rc,a,diag,raw = self.parse(data)
        self.assertEqual(rc,0,_diag_message(diag))
        output, length = ctypes.c_void_p(123), ctypes.c_size_t(987)
        try:
            if instance is None:
                result = self.library.atari_stx_read_chrn(ctypes.byref(a),*chrn,ctypes.byref(output),ctypes.byref(length))
            else:
                result = self.library.atari_stx_read_instance(ctypes.byref(a),*instance,ctypes.byref(output),ctypes.byref(length))
            if result:
                self.assertIsNone(output.value)
                self.assertEqual(length.value,0)
                return result, None
            return result, ctypes.string_at(output,length.value)
        finally:
            self.library.atari_stx_destroy(ctypes.byref(a))

    def test_simple_track_and_stable_read(self):
        data=bytes(range(256))*2
        report=self.inspect_disk_buffer('atari-st-disk',image(simple(data)))
        s=report['tracks'][0]['sectors'][0]
        self.assertEqual((s['offset'],s['size'],s['header_offset']),(32,512,-1))
        self.assertEqual(s['offset_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(self.read(image(simple(data)),chrn=(0,0,0,0,1,2)),(0,data))

    def test_empty_disk_and_track_image_without_sectors(self):
        self.assertEqual(self.inspect_disk_buffer('atari-st-disk',image())['tracks'],[])
        t=self.inspect_disk_buffer('atari-st-disk',image(detailed(track_image=b'raw track', flags=129,sync=7)))['tracks'][0]
        self.assertEqual((t['sync'],t['image_size'],t['sectors']),(7,9,[]))
        self.assertEqual(self.read(image(detailed()))[0],1)

    def test_embedded_and_external_sector_ranges(self):
        data=image(detailed([sector(4),sector(132,chrn=(0,0,2,0))],flags=193,track_image=b'A'*128,sync=5,track_data=b'B'*128))
        report=self.inspect_disk_buffer('atari-st-disk',data)
        t=report['tracks'][0]
        self.assertEqual(t['sectors'][0]['offset'],t['image_offset'])
        self.assertEqual(self.read(data),(0,b'A'*128))
        self.assertEqual(self.read(data,chrn=(0,0,0,0,2,0)),(0,b'B'*128))

    def test_fuzzy_and_crc_are_retained_not_read_as_stable(self):
        data=image(detailed([sector(status=0x88)],track_data=b'X'*128,fuzzy=b'\xf0'*128))
        t=self.inspect_disk_buffer('atari-st-disk',data)['tracks'][0]
        s=t['sectors'][0]
        self.assertEqual(s['status'],0x88)
        self.assertEqual(s['fuzzy_offset'],t['fuzzy_offset'])
        self.assertEqual(s['fuzzy_offset_sha256'],hashlib.sha256(b'\xf0'*128).hexdigest())
        self.assertEqual(self.read(data)[0],4)
        self.assertEqual(self.read(image(detailed([sector(status=8)],track_data=b'X'*128)))[0],5)

    def test_missing_data_retains_id_and_ignores_unmeaningful_offset(self):
        data=image(detailed([sector(offset=0xffffffff,status=0x98)]))
        s=self.inspect_disk_buffer('atari-st-disk',data)['tracks'][0]['sectors'][0]
        self.assertEqual((s['offset'],s['size'],s['status']),(-1,0,0x98))
        self.assertEqual(self.read(data)[0],3)

    def test_duplicate_ids_and_duplicate_track_instances(self):
        track=detailed([sector(),sector(128)],track_data=b'A'*128+b'B'*128)
        data=image(track)
        self.assertEqual(self.read(data)[0],2)
        self.assertEqual(self.read(data,instance=(0,1)),(0,b'B'*128))
        self.assertEqual(self.read(image(track,track))[0],2)
        self.assertEqual(self.read(data,instance=(2,0))[0],1)

    def test_id_bytes_do_not_override_physical_track_identity(self):
        data=image(detailed([sector(chrn=(77,9,12,0))],number=0x84,track_data=b'C'*128))
        self.assertEqual(self.read(data,chrn=(4,1,77,9,12,0)),(0,b'C'*128))
        self.assertEqual(self.read(data,chrn=(77,9,77,9,12,0))[0],1)

    def test_unknown_flags_and_reserved_bytes_are_preserved_but_not_safe_reads(self):
        for flags,reserved in [(0x201,0),(1,6)]:
            with self.subTest(flags=flags,reserved=reserved):
                data=image(detailed([sector(reserved=reserved)],flags=flags,track_data=b'A'*128,tail=b'opaque'))
                t=self.inspect_disk_buffer('atari-st-disk',data)['tracks'][0]
                self.assertEqual((t['flags'],t['tail_size']),(flags,6))
                self.assertEqual(self.read(data)[0],6)

    def test_all_size_codes_preserved_low_bits_determine_storage(self):
        for n in [0,1,2,3,0x83]:
            data=image(detailed([sector(chrn=(0,0,1,n))],track_data=b'X'*(128<<(n&3))))
            s=self.inspect_disk_buffer('atari-st-disk',data)['tracks'][0]['sectors'][0]
            self.assertEqual(s['id_size'],n)
            self.assertEqual(s['size'],128<<(n&3))
            self.assertEqual(s['read_result'],0)

    def test_variable_timing_revision_two_and_zero(self):
        for rev in [0,2]:
            timing=b'\x00\x7f'*16
            data=image(detailed([sector(status=1),sector(128,chrn=(0,0,2,0),status=1)],track_data=b'A'*256,timing=timing if rev==2 else None),revision=rev)
            t=self.inspect_disk_buffer('atari-st-disk',data)['tracks'][0]
            for i,s in enumerate(t['sectors']):
                self.assertEqual(s['implicit_timing'],int(rev==0))
                self.assertEqual(s['timing_bytes'],16)
                self.assertEqual(s['timing_offset'],-1 if rev==0 else t['timing_offset']+4+i*16)
            self.assertEqual(self.read(data)[0],5)

    def test_little_endian_metadata_big_endian_crc(self):
        data=image(detailed([sector()],track_data=b'A'*128,record_type=0xcc))
        s=self.inspect_disk_buffer('atari-st-disk',data)['tracks'][0]['sectors'][0]
        self.assertEqual((s['bit_position'],s['read_time'],s['id_crc']),(123,456,0xabcd))

    def test_every_truncation_and_trailing_bytes(self):
        data=image(detailed([sector(status=0x81)],fuzzy=b'\xff'*128,track_data=b'A'*128,timing=b'\x00\x80'*8))
        for length in range(len(data)):
            self.reject(data[:length])
        self.reject(data+b'extra')

    def test_invalid_version_revision_track_lengths_counts_and_offsets(self):
        base=image(detailed([sector()],track_data=b'A'*128))
        for offset,fmt,value in [(4,'H',4),(11,'B',1),(10,'B',2),(16,'I',15),(16,'I',0xffffffff),(20,'I',0xffffffff),(24,'H',0xffff),(26,'H',0x81),(32,'I',0xffffffff)]:
            with self.subTest(offset=offset,value=value):
                bad=bytearray(base);struct.pack_into('<'+fmt,bad,offset,value);self.reject(bytes(bad))
        self.reject(b'BAD!'+base[4:])
        self.reject(image(simple(b'x'*512)+b'x'))

    def test_fuzzy_and_timing_length_mismatches(self):
        self.reject(image(detailed([sector(status=0x80)],track_data=b'A'*128)))
        self.reject(image(detailed([sector()],track_data=b'A'*128,fuzzy=b'X'*128)))
        for timing in [b'',b'x'*15,b'x'*18]:
            self.reject(image(detailed([sector(status=1)],track_data=b'A'*128,timing=timing)))
        self.reject(image(detailed([sector(status=1)],track_data=b'A'*128)))

    def test_failed_output_can_be_destroyed_twice(self):
        rc,a,diag,raw=self.parse(b'bad')
        self.assertNotEqual(rc,0)
        self.library.atari_stx_destroy(ctypes.byref(a))
        self.library.atari_stx_destroy(ctypes.byref(a))

    def test_python_archive_inspection_uses_original_stx_bytes(self):
        from amiga_reversing.disasm.c_backend import inspect_disk_with_c_backend
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'media.zip'
            data=image(simple())
            with zipfile.ZipFile(path,'w') as archive: archive.writestr('nested/disk.stx',data)
            report=inspect_disk_with_c_backend(path)
            self.assertEqual(report['format_kind'],'stx')
            self.assertEqual(report['image_sha256'],hashlib.sha256(data).hexdigest())
            self.assertEqual(report['filesystem_status'],'not_analyzed')

    def test_mutations_do_not_escape_bounds_or_leave_partial_state(self):
        rng=random.Random(0x535458)
        base=image(detailed([sector(status=0x81)],fuzzy=b'\xff'*128,track_data=b'A'*128,timing=b'\x00\x80'*8))
        for _ in range(1000):
            bad=bytearray(base)
            for _ in range(rng.randrange(1,5)):
                i=rng.randrange(len(bad));bad[i]^=rng.randrange(1,256)
            rc,a,diag,raw=self.parse(bytes(bad))
            try:
                if rc:
                    self.assertFalse(a.tracks)
                else:
                    for ti in range(a.track_count):
                        t=a.tracks[ti]
                        for si in range(t.sector_count):
                            s=t.sectors[si]
                            if s.offset!=NONE:
                                self.assertGreaterEqual(s.offset,t.offset)
                                self.assertLessEqual(s.offset+s.size,t.offset+t.size)
            finally:
                self.library.atari_stx_destroy(ctypes.byref(a))

    def test_native_cli_and_stable_sector_extraction(self):
        cli=ROOT/'src/build/platform_disk_cli.exe'
        data=image(detailed([sector(),sector(128,status=0x88,chrn=(0,0,2,0))],track_data=b'A'*256,fuzzy=b'\xf0'*128))
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.stx';path.write_bytes(data)
            good=subprocess.run([str(cli),'extract-stx-sector',str(path),'0','0'],capture_output=True)
            self.assertEqual((good.returncode,good.stdout),(0,b'A'*128),good.stderr)
            for ti,si in [('0','1'),('999','0'),('-1','0'),('0','18446744073709551616'),('0','x')]:
                failed=subprocess.run([str(cli),'extract-stx-sector',str(path),ti,si],capture_output=True)
                self.assertNotEqual(failed.returncode,0)
                self.assertEqual(failed.stdout,b'')
            filesystem=subprocess.run([str(cli),'extract-entry','atari-st-disk',str(path),'anything'],capture_output=True)
            self.assertNotEqual(filesystem.returncode,0)
            self.assertIn(b'filesystem not analyzed',filesystem.stderr)

    @unittest.skipUnless(os.getenv('STX_SANITIZERS'),'set STX_SANITIZERS=1 for ASan/UBSan mutation runner')
    def test_native_sanitizer_mutations(self):
        cases=[image(simple()),image(detailed()),
               image(detailed([sector(status=0x81)],fuzzy=b'\xff'*128,track_data=b'A'*128,timing=b'\x00\x80'*8)),
               image(detailed([sector(4)],flags=193,track_image=b'A'*128,sync=3)),
               image(detailed([sector(status=0x98)])),
               image(detailed([sector(status=1)],track_data=b'A'*128),revision=0)]
        with tempfile.TemporaryDirectory() as temp:
            executable=Path(temp)/'stx-sanitize'
            subprocess.run(['cc','-std=c11','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                            '-Isrc','src/platform_atari_stx.c','src/m68k_diagnostics.c',
                            'src/tests/stx_sanitizer_driver.c','-o',str(executable)],cwd=ROOT,check=True)
            paths=[]
            for i,data in enumerate(cases):
                path=Path(temp)/f'{i}.stx';path.write_bytes(data);paths.append(str(path))
            subprocess.run([str(executable),*paths],check=True,timeout=30)

    @unittest.skipUnless(os.getenv('HATARI_STX_REFERENCE'),'set HATARI_STX_REFERENCE to pinned checkout')
    def test_differential_synthetic_and_optional_original(self):
        spec=importlib.util.spec_from_file_location('stx_reference_probe',ROOT/'tools/stx_reference_probe.py')
        oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
        cases=[image(simple(),detailed(),detailed(track_image=b'raw',flags=193,sync=1),
                     detailed([sector(2)],track_image=b'A'*128),
                     detailed([sector(status=0x88)],track_data=b'B'*128,fuzzy=b'\xf0'*128),
                     detailed([sector(status=0x10)]),
                     detailed([sector(),sector(128)],track_data=b'C'*256),
                     detailed([sector(status=1)],track_data=b'D'*128,timing=b'\x00\x80'*8)),
               image(detailed([sector(status=1)],track_data=b'E'*128),revision=0)]
        if os.getenv('SGII_STX_IMAGE'):
            cases.append(oracle.read_image(Path(os.environ['SGII_STX_IMAGE']),None)[0])
        for data in cases:
            actual=self.inspect_disk_buffer('atari-st-disk',data)
            expected=oracle.probe(Path(os.environ['HATARI_STX_REFERENCE']),data)
            self.assertEqual(actual['image_sha256'],expected['image_sha256'])
            self.assertEqual(len(actual['tracks']),len(expected['tracks']))
            for t,ref in zip(actual['tracks'],expected['tracks']):
                for key,value in ref.items():
                    if key=='sectors': continue
                    self.assertEqual(t[key],value,(t['index'],key))
                self.assertEqual(len(t['sectors']),len(ref['sectors']))
                for s,rs in zip(t['sectors'],ref['sectors']):
                    for key,value in rs.items():
                        # Hatari fabricates FDC layout/CRC for implicit sectors;
                        # ours reports only what the container actually stores.
                        if not(t['flags']&1) and key in {'bit_position','id_crc'}: continue
                        self.assertEqual(s[key],value,(t['index'],s['index'],key))


if __name__=='__main__': unittest.main()

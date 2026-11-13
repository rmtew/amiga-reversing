"""Oracle-adapter checks; these are not a native STX reader test suite."""
import importlib.util
import os
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location('stx_reference_probe', Path(__file__).parents[1]/'tools/stx_reference_probe.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def simple_image():
    return (struct.pack('<4sHHHBBI', b'RSY\0', 3, 1, 0, 1, 2, 0)
            + struct.pack('<IIHHHBB', 528, 0, 1, 0, 6250, 0, 0)
            + bytes(range(256))*2)


class StxReferenceProbeTests(unittest.TestCase):
    def read(self, data):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'disk.stx'
            p.write_bytes(data)
            return probe.read_image(p, None)

    def test_valid_track_container(self):
        self.assertEqual(self.read(simple_image())[0], simple_image())

    def test_bad_signature(self):
        with self.assertRaisesRegex(ValueError, 'header'):
            self.read(b'bad!'+simple_image()[4:])

    def test_bad_version(self):
        with self.assertRaisesRegex(ValueError, 'header'):
            self.read(simple_image()[:4]+b'\x04\0'+simple_image()[6:])

    def test_truncated_header(self):
        with self.assertRaises(ValueError):
            self.read(simple_image()[:15])

    def test_truncated_track(self):
        with self.assertRaisesRegex(ValueError, 'block size'):
            self.read(simple_image()[:-1])

    def test_small_track(self):
        b=bytearray(simple_image());struct.pack_into('<I',b,16,15)
        with self.assertRaisesRegex(ValueError,'block size'):
            self.read(b)

    def test_trailing_data_is_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError,'entire image'):
            self.read(simple_image()+b'x')

    def test_zip_member_is_read_without_extracting_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'disk.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('../../disk.stx',simple_image())
            self.assertEqual(probe.read_image(p,None),(simple_image(),'../../disk.stx'))
            self.assertEqual(list(Path(temp).iterdir()),[p])

    def test_multiple_members_require_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'disks.zip'
            with zipfile.ZipFile(p,'w') as z:
                for name in ['a.stx','b.stx']: z.writestr(name,simple_image())
            with self.assertRaisesRegex(ValueError,'exactly one'):
                probe.read_image(p,None)
            self.assertEqual(probe.read_image(p,'b.stx')[1],'b.stx')

    def test_external_function_extraction_rejects_missing_definition(self):
        with self.assertRaisesRegex(ValueError,'one upstream'):
            probe.function('static void Missing(void);','Missing')

    @unittest.skipUnless(os.getenv('HATARI_STX_REFERENCE'), 'set HATARI_STX_REFERENCE to pinned checkout')
    def test_actual_hatari_simple_sector(self):
        report=probe.probe(Path(os.environ['HATARI_STX_REFERENCE']),simple_image())
        self.assertEqual(len(report['tracks']),1)
        sector=report['tracks'][0]['sectors'][0]
        self.assertEqual((sector['id_sector'],sector['size'],sector['offset']),(1,512,32))
        self.assertEqual(sector['status'],0)


if __name__=='__main__': unittest.main()

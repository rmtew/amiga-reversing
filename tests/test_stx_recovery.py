"""Source-bound STX recovery and refusal of invented state or media choices."""
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
import zipfile
from amiga_reversing.disasm.mapped_execution import MappedExecution, assemble_stx_sectors
from amiga_reversing.disasm.stx_recovery import read_stx, recover
from src.tests.test_platform_atari_stx import detailed, image, sector, simple

ROOT=Path(__file__).resolve().parents[1]


def fixture(code=bytes.fromhex('23fc11223344000020004ef900003000')):
    data=image(simple(code.ljust(512,b'\0')))
    plan=dict(schema_version=1,kind='stx_cpu_recovery',image_sha256=hashlib.sha256(data).hexdigest(),
              memory_size=0x4000,evidence='synthetic immediate-store and jump',
              inputs=[dict(id='program',track_start=0,track_count=1,side=0,sector_ids=[1],id_track=0,id_head=0,id_sizes=[2])],
              actions=[dict(op='load',input='program',address=0x1000),
                       dict(op='run',purpose='original instructions',start=0x1000,stop=0x3000,max_steps=8,expected_stop='pc',writes=[[0x2000,4]]),
                       dict(op='capture',file='result.bin',address=0x2000,size=4,sha256=hashlib.sha256(bytes.fromhex('11223344')).hexdigest())])
    return data,plan


class StxRecoveryTests(unittest.TestCase):
    def test_original_instructions_produce_exact_output_and_source_map(self):
        data,plan=fixture()
        report,outputs=recover(data,plan)
        self.assertEqual(outputs['result.bin'],bytes.fromhex('11223344'))
        self.assertEqual(report['runs'][0]['steps'],2)
        self.assertEqual(report['inputs']['program']['source_ranges'][0]['image_offset'],32)
        self.assertEqual(report['captures'][0]['load_address'],0x2000)
        for seed in [0xffffffff,0xdeadbeef]:
            self.assertEqual(recover(data,plan,register_seed=seed)[1],outputs)

    def test_unknown_read_refuses_instead_of_using_zero_filled_memory(self):
        data,plan=fixture(bytes.fromhex('2039000025004ef900003000'))
        with self.assertRaisesRegex(ValueError,'unknown read'):
            recover(data,plan)

    def test_failed_execution_cannot_be_captured_or_reused(self):
        cpu=MappedExecution(0x4000)
        cpu.seed(0x1000,bytes.fromhex('203900002500'))
        with self.assertRaises(ValueError): cpu.run(0x1000,0x2000,8)
        for operation in [lambda:cpu.read(0x1000,2),lambda:cpu.seed(0,b'x'),lambda:cpu.run(0x1000,0x2000,8)]:
            with self.assertRaisesRegex(ValueError,'cannot be reused'): operation()

    def test_forbidden_write_and_unknown_extension_fetch_refuse(self):
        data,plan=fixture();plan['actions'][1]['writes']=[]
        with self.assertRaisesRegex(ValueError,'forbidden write'):recover(data,plan)
        cpu=MappedExecution(0x4000);cpu.seed(0x1000,bytes.fromhex('23fc'));cpu.allow_write(0,0x4000)
        with self.assertRaisesRegex(ValueError,'unknown read/fetch'):cpu.run(0x1000,0x3000,8)

    def test_instruction_budget_is_a_real_bound(self):
        data,plan=fixture(bytes.fromhex('60fe'))
        with self.assertRaisesRegex(ValueError,'stop 3'):recover(data,plan)
        cpu=MappedExecution(0x4000);cpu.seed(0x1000,bytes.fromhex('60fe'))
        self.assertEqual(cpu.run(0x1000,0x3000,5,expected_stop='limit')['steps'],5)

    def test_source_identity_ambiguity_and_missing_identity_refuse(self):
        data,plan=fixture()
        with self.assertRaisesRegex(ValueError,'identity mismatch'):recover(data+b'x',plan)
        for field,value in [('sector_ids',[2]),('id_track',1),('track_count',0),('side',True)]:
            changed=copy.deepcopy(plan);changed['inputs'][0][field]=value
            with self.assertRaises(ValueError):recover(data,changed)
        duplicate=image(simple(),simple());plan['image_sha256']=hashlib.sha256(duplicate).hexdigest()
        with self.assertRaisesRegex(ValueError,'ambiguous physical track'):recover(duplicate,plan)

    def test_output_identity_names_and_unknown_fields_are_not_silently_accepted(self):
        data,plan=fixture()
        for field,value in [('file','../bad.bin'),('file','..\\bad.bin'),('sha256','0'*64),('size',True)]:
            changed=copy.deepcopy(plan);changed['actions'][-1][field]=value
            with self.assertRaises(ValueError):recover(data,changed)
        changed=copy.deepcopy(plan);changed['actions'][1]['patch']='anything'
        with self.assertRaisesRegex(ValueError,'recipe fields'):recover(data,changed)

    def test_native_assembly_rejects_fuzzy_missing_and_oversized_outputs_atomically(self):
        data=image(detailed([sector(chrn=(247,247,245,247)),sector(1024,chrn=(247,247,246,0),status=0x80)],track_data=b'A'*1024+b'B'*128,fuzzy=b'\xf0'*128))
        self.assertEqual(assemble_stx_sectors(data,[(0,0)],1024),b'A'*1024)
        for malformed in [[],[1],[(0,)],[(True,0)],[(-1,0)]]:
            with self.assertRaises(ValueError):assemble_stx_sectors(data,malformed,1024)
        for indexes,maximum in [([(0,0),(0,1)],2048), ([(0,2)],1024), ([(0,0)],1023), ([(0,0),(0,0)],1024)]:
            with self.assertRaises(ValueError):assemble_stx_sectors(data,indexes,maximum)

    def test_zip_selection_reads_without_extracting_member_paths(self):
        data,_=fixture()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'disk.zip'
            with zipfile.ZipFile(path,'w') as z:z.writestr('../../game.stx',data)
            raw,origin=read_stx(path)
            self.assertEqual(raw,data);self.assertEqual(origin['member'],'../../game.stx')
            self.assertEqual(list(Path(temp).iterdir()),[path])
            with zipfile.ZipFile(path,'a') as z:z.writestr('other.stx',data)
            with self.assertRaises(ValueError):read_stx(path)
            self.assertEqual(read_stx(path,'other.stx')[0],data)

    @unittest.skipUnless(os.getenv('SGII_STX_IMAGE'),'set SGII_STX_IMAGE for original-media recovery')
    def test_original_sgii_recipe_repeats_with_different_register_seeds(self):
        data,_=read_stx(Path(os.environ['SGII_STX_IMAGE']))
        plan=json.loads((ROOT/'targets/atari_st_starglider2_stx/recovery_plan.json').read_text())
        report,first=recover(data,plan)
        self.assertEqual(report['inputs']['main_dma']['size'],422400)
        self.assertEqual(len(report['inputs']['main_dma']['source_ranges']),450)
        self.assertEqual(len(first['main_decoded.bin']),419308)
        self.assertEqual(first['main_decoded.bin'][2:4],b'\x80\0')
        self.assertEqual(first['main_at_st_handoff.bin'][2:4],b'\0\1')
        self.assertEqual(first['main_decoded.bin'][:2],first['main_at_st_handoff.bin'][:2])
        self.assertEqual(first['main_decoded.bin'][4:],first['main_at_st_handoff.bin'][4:])
        self.assertIn(b'Ver 1.05 1st September 1988.',first['main_at_st_handoff.bin'][:128])
        self.assertEqual(recover(data,plan,register_seed=0xdeadbeef)[1],first)
        # Source verification uses the full platform-source assembler, with an
        # independent vasm oracle when supplied. No source/binary is retained.
        from amiga_reversing.disasm.c_backend import assemble_platform_source_path_with_c_backend
        boot_map=report['inputs']['boot_sector']['source_ranges'][0]
        boot=data[boot_map['image_offset']:boot_map['image_offset']+512]
        with tempfile.TemporaryDirectory() as temp:
            for name,value,entry in [('boot',boot,0),('helper',first['main_loader_helper.bin'],0x60)]:
                raw=Path(temp)/(name+'.bin');source=Path(temp)/(name+'.s')
                raw.write_bytes(value)
                rendered=subprocess.check_output([str(ROOT/'src/build/platform_file_cli.exe'),'disassemble-raw','atari-st-raw',str(raw),str(entry)])
                source.write_bytes(rendered)
                rebuilt,_=assemble_platform_source_path_with_c_backend('atari-st-raw',source,target_cpu='68000')
                self.assertEqual(rebuilt,value)
                if os.getenv('VASM_PATH'):
                    oracle=Path(temp)/(name+'-vasm.bin')
                    subprocess.run([os.environ['VASM_PATH'],'-quiet','-m68000','-no-opt','-Fbin','-o',str(oracle),str(source)],check=True)
                    self.assertEqual(oracle.read_bytes(),value)


if __name__=='__main__':unittest.main()

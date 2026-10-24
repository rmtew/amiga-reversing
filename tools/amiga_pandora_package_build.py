"""Standalone source-package build: Python standard library plus vasm only.

Run from the extracted application package. No repository, native backend,
emulator, ROM or disk-image builder is needed to produce the two DOS files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vasm',default='vasmm68k_mot')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=Path(__file__).resolve().parent
    manifest=json.loads((root/'manifest.json').read_text());application=manifest['application']
    if application['profile']!='pandora-dos-owned-prefix-v1':raise ValueError('Unsupported application profile')
    for record in manifest['files']:
        path=(root/record['path']).resolve()
        if not path.is_relative_to(root) or path.stat().st_size!=record['size'] or sha(path)!=record['sha256']:
            raise ValueError('Stale or changed package source: '+record['path'])
    output=(args.output or root/'bin').resolve();output.mkdir(parents=True,exist_ok=False)
    vasm=shutil.which(args.vasm) or str(Path(args.vasm).resolve())
    payload=output/'Pandora.payload';program=output/'Pandora'
    vasm_sha256=sha(Path(vasm))
    commands=[ [vasm,'-Fbin','-m68000','-no-opt','-I'+str(root),'-o',str(payload),str(root/application['game_source'])],
        [vasm,'-Fhunkexe','-m68000','-no-opt','-I'+str(root),'-L',str(output/'Pandora.list'),'-o',str(program),str(root/application['entry_source'])] ]
    for i,command in enumerate(commands):
        result=subprocess.run(command,cwd=root,capture_output=True,text=True)
        (output/f'assemble-{i}.log').write_text(result.stdout+result.stderr)
        result.check_returncode()
        if sha(Path(vasm))!=vasm_sha256:raise ValueError('Assembler changed during build')
        if i==0 and sha(payload)!=application['expected_payload_sha256']:
            raise ValueError('vasm game output differs from the native source assembly; runtime fields are stale')
    # knowledge/amiga_hunk_format.json: HUNKB_FAST=31 (CHIP is30).
    words=struct.unpack('>8I',program.read_bytes()[:32])
    if words[:5]!=(1011,0,1,0,0) or words[6]!=1001 or not words[5]&(1<<31):
        raise ValueError('Expected a single Fast/Slow-RAM CODE HUNK')
    for record in manifest['files']:
        if sha(root/record['path'])!=record['sha256']:raise ValueError('Package source changed during build')
    receipt=dict(schema='pandora-standalone-application-build/v1',status='game_C_expected_bytes_and_vasm_match_loader_HUNK_assembled_not_runtime_qualification',
        package_manifest_sha256=sha(root/'manifest.json'),vasm_sha256=vasm_sha256,
        files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in (payload,program)},
        original_binary_sha256=manifest['target_identity_sha256'],
        original_binary_exact=sha(payload)==manifest['target_identity_sha256'])
    (output/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Built Pandora and Pandora.payload. Copy both together; cd into that directory before running Pandora.')
    print('Runtime qualification is separate; see the package README and evidence links.')

if __name__=='__main__':main()

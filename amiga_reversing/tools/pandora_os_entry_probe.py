"""Build a plain OFS/DOS host-entry prerequisite, not an OS-hosted Pandora game.

Uses external amitools xdftool and the existing strictly headless Copperline
process. Both HUNK files are our own small DOS-output/CloseLibrary/RTS probes.
Captured console output requires explicit review; capture alone is not a pass.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build(out,xdftool):
    out.mkdir(parents=True,exist_ok=False)
    source=PROJECT_ROOT/'tools/amiga_os_entry_probe.s'
    for index in (1,2):
        result=subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-Fhunkexe','-m68000',
            '-I'+str(PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'),'-DPROBE_INDEX='+str(index),
            '-o',str(out/f'probe{index}'),str(source)],check=True,capture_output=True,text=True)
        (out/f'assemble{index}.log').write_text(result.stdout+result.stderr)
    startup=out/'startup-sequence';startup.write_bytes(b'probe1\nprobe2\n')
    disk=out/'host.adf'
    result=subprocess.run([str(xdftool),str(disk),'format','PandoraHost','ofs','+','boot','install','boot1x',
        '+','makedir','S','+','write',str(startup),'S/Startup-Sequence',
        '+','write',str(out/'probe1'),'probe1','+','write',str(out/'probe2'),'probe2','+','list'],
        check=True,capture_output=True,text=True)
    (out/'disk-build.log').write_text(result.stdout+result.stderr)
    return dict(status='plain_DOS_host_probe_built',source_sha256=sha(source),
        HUNK_sha256=[sha(out/f'probe{index}') for index in (1,2)],ADF_sha256=sha(disk),
        filesystem_tool='amitools xdftool 0.8.1; external build dependency',
        scope='Plain OFS boot and two normal DOS programs. No game bootstrap or guest-state forcing.',
        frames=[])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--xdftool',type=Path,required=True)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--rom',type=Path)
    parser.add_argument('--copperline',type=Path)
    a=parser.parse_args()
    if a.run and (a.rom is None or a.copperline is None):parser.error('--run requires explicit ROM and Copperline')
    out=a.output.resolve();r=build(out,a.xdftool.resolve())
    if a.run:
        from amiga_reversing.tools.copperline_control import CopperlineProcess,MACHINE_PROFILES
        r.update(profile=MACHINE_PROFILES['a500ecs_1m'],rom_sha256=sha(a.rom),emulator_sha256=sha(a.copperline))
        with CopperlineProcess(a.copperline,rom=a.rom,floppy=out/'host.adf',machine_profile='a500ecs_1m') as process:
            client=process.client
            for frame in (500,1500):
                stop=client.run_until({'frame':frame},timeout=30)
                if stop.get('reason')!='target':raise ValueError('Host boot did not complete bounded frame window')
                shot=out/f'DOS-{frame}.png';client.request('capture.screenshot',{'path':str(shot),'native':True})
                r['frames'].append(dict(stop=stop,registers=client.registers(),screenshot=shot.name,sha256=sha(shot)))
                print('FRAME',frame,flush=True)
        r['status']='DOS_host_capture_complete_output_review_required'
    (out/'report.json').write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()

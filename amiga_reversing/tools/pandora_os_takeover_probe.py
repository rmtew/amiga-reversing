"""Own HUNK display/SSP round-trip probe; no Pandora payload or OS-game claim.

Tests a temporary owned stack then restored Supervisor frame, view, blitter
ownership and observable CLI keyboard input. This is not a general game-exit
implementation: callback is idle; audio/CIA/game clobbers remain unqualified.
"""
import argparse
import json
import subprocess
from pathlib import Path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.tools.pandora_os_entry_probe import build,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--xdftool',type=Path,required=True)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--copperline',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();r=build(out,a.xdftool.resolve())
    source=PROJECT_ROOT/'tools/amiga_os_takeover_probe.s'
    assembled=subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-Fhunkexe','-m68000',
        '-I'+str(PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'),'-o',str(out/'takeover'),str(source)],
        capture_output=True,text=True,check=True)
    (out/'takeover-assemble.log').write_text(assembled.stdout+assembled.stderr)
    startup=out/'startup-sequence';startup.write_text('takeover\nprobe2\n')
    subprocess.run([str(a.xdftool.resolve()),str(out/'host.adf'),'delete','S/Startup-Sequence',
        '+','write',str(startup),'S/Startup-Sequence','+','write',str(out/'takeover'),'takeover'],
        check=True,capture_output=True)
    from amiga_reversing.tools.copperline_control import CopperlineProcess
    with CopperlineProcess(a.copperline,rom=a.rom,floppy=out/'host.adf',machine_profile='a500ecs_1m') as process:
        c=process.client;before=c.run_until({'frame':1500},timeout=30)
        if before.get('reason')!='target':raise ValueError('Finite host boot window did not finish')
        c.request('capture.screenshot',{'path':str(out/'before-return-key.png'),'native':True})
        try:
            c.key(0x44,pressed=True)
            c.run_until({'frame':1503},timeout=5)
        finally:c.key(0x44,pressed=False)
        after=c.run_until({'frame':1530},timeout=5)
        if after.get('reason')!='target':raise ValueError('Finite post-key window did not finish')
        c.request('capture.screenshot',{'path':str(out/'after-return-key.png'),'native':True})
    r.update(status='lifecycle_probe_capture_complete_console_review_required',
        source_sha256=sha(source),takeover_HUNK_sha256=sha(out/'takeover'),ADF_sha256=sha(out/'host.adf'),
        rom_sha256=sha(a.rom),emulator_sha256=sha(a.copperline),before=before,after=after,
        keys=[{'rawkey':0x44,'pressed':True,'frame':1500},{'rawkey':0x44,'pressed':False,'frame':1503}],
        screenshot_sha256={n:sha(out/n) for n in ('before-return-key.png','after-return-key.png')},
        scope=__doc__)
    (out/'report.json').write_text(json.dumps(r,indent=2)+'\n')
    print(r['status'],flush=True)


if __name__=='__main__':main()

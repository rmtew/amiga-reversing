"""Probe four current native-layout claims through normal DOS entry and return.

This does not load Pandora or certify all its storage. Successful claims stay
owned until every claim has been attempted, then are freed before DOS output.
A second normal executable witnesses return; console results require review.
"""
import argparse
import json
import subprocess
from pathlib import Path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.tools.pandora_layout_runtime import runtime_context
from amiga_reversing.tools.pandora_os_entry_probe import build,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--xdftool',type=Path,required=True)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--copperline',type=Path,required=True)
    a=p.parse_args();c=json.loads(a.config.read_text());image,bootstrap=runtime_context(c)
    regions={r['region_id']:r for r in c['layout_plan']['regions']}
    claims=[('input',bootstrap['load_address'],bootstrap['file_size']),
        ('image',image['runtime_address'],bootstrap['file_size'])]
    for name in ('pandora_display_storage','keyboard_state'):
        r=regions[name];claims.append((name,r['runtime_address'],r['size']))
    for _,address,size in claims:
        if type(address) is not int or type(size) is not int or address%8 or size%8 or size<=0:
            raise ValueError('Exact aligned ownership extents required')
    out=a.output.resolve();report=build(out,a.xdftool.resolve())
    lines=['CLAIM_COUNT EQU '+str(len(claims)),'claims:']+[
        f' dc.l ${address:X},${size:X},0' for _,address,size in claims]
    lines+=['message: dc.b "PANDORA OS LEASES (O=owned,F=busy): "',
        'result_marks: dc.b "????",10',' dc.b "Order: input,image,display,keyboard",10','message_end:']
    include=out/'claims.i';include.write_text('\n'.join(lines)+'\n')
    source=PROJECT_ROOT/'tools/amiga_os_lease_probe.s'
    assembled=subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-Fhunkexe','-m68000',
        '-I'+str(PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'),'-I'+str(out),
        '-o',str(out/'lease'),str(source)],capture_output=True,text=True,check=True)
    (out/'lease-assemble.log').write_text(assembled.stdout+assembled.stderr)
    startup=out/'startup-sequence';startup.write_text('lease\nprobe2\n')
    subprocess.run([str(a.xdftool.resolve()),str(out/'host.adf'),'delete','S/Startup-Sequence',
        '+','write',str(startup),'S/Startup-Sequence','+','write',str(out/'lease'),'lease'],
        check=True,capture_output=True,text=True)
    from amiga_reversing.tools.copperline_control import CopperlineProcess
    with CopperlineProcess(a.copperline,rom=a.rom,floppy=out/'host.adf',machine_profile='a500ecs_1m') as process:
        stop=process.client.run_until({'frame':1500},timeout=30)
        if stop.get('reason')!='target':raise ValueError('Finite host capture did not finish')
        process.client.request('capture.screenshot',{'path':str(out/'console.png'),'native':True})
    report.update(status='DOS_lease_capture_complete_console_review_required',claims=claims,
        config_sha256=sha(a.config),lease_source_sha256=sha(source),claims_include_sha256=sha(include),
        lease_HUNK_sha256=sha(out/'lease'),ADF_sha256=sha(out/'host.adf'),stop=stop,
        screenshot_sha256=sha(out/'console.png'),rom_sha256=sha(a.rom),emulator_sha256=sha(a.copperline),
        scope='Four explicit claims only, no game launch, no takeover or inferred all-storage coverage.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],flush=True)


if __name__=='__main__':main()

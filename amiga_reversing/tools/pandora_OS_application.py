"""Build the normal-DOS Pandora application's bounded pre-entry resource stage.

No hardware takeover, game launch or successful game exit is claimed here. The
native six-owner contract supplies lease sizes and fixed acquisition intents;
this stage measures real Exec returns and verifies whole-file loading, then
unwinds. It must not be mistaken for a fixed-base placement or a playthrough.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.tools.pandora_os_entry_probe import build as build_host,sha

OWNERS=('pandora_prng_state','keyboard_state','pandora_ui_snapshot_body',
        'pandora_title_stars','pandora_cpu_workspace','pandora_low_generated_masks')


def build(out,xdftool,payload,contract):
    data=payload.read_bytes();plans=contract['candidates'];batch=contract['template_geometry']
    if (len(data)!=376832 or hashlib.sha256(data).hexdigest()!=
            '9b0bf6e9747fdaf008983f3c0f9e77910ec9b30f777b0ace95594a41d8833f8b'
            or set(plans)!=set(OWNERS) or batch.get('status')!='actual_placements_valid'
            or batch.get('owner_count')!=6 or batch.get('uncovered_runtime_extents')!=[]):
        raise ValueError('Complete native hosted template and exact preserved payload required')
    if any(plans[n].get('status')!='bounded_allocation_candidate' for n in OWNERS):
        raise ValueError('Refused owner cannot become an Exec request')
    fixed=batch['fixed_leases_requiring_OS_acquisition']
    if any(r['address']<0x10000 or r['address']%8 or r['size']%8 for r in fixed):
        raise ValueError('Hosted source-helper profile with aligned fixed leases required')
    build_host(out,xdftool)
    constants={'OWNER_COUNT':len(OWNERS),'FIXED_COUNT':len(fixed),'INPUT_ADDRESS':0x20000,
               'PAYLOAD_SIZE':len(data),'PAYLOAD_CRC32':zlib.crc32(data)}
    (out/'pandora_OS_plan.i').write_text('\n'.join(f'{n} EQU ${v:X}' for n,v in constants.items())+'\n')
    table=['fixed_table:']+[f"    dc.l ${r['address']:X},${r['size']:X}" for r in fixed]
    table+=['owner_sizes:']+[f"    dc.l ${(plans[n]['size']+7)&~7:X}" for n in OWNERS]
    table+=['crc_table:']
    for i in range(256):
        crc=i
        for _ in range(8):crc=(crc>>1)^(0xedb88320 if crc&1 else 0)
        table.append(f'    dc.l ${crc:08X}')
    (out/'pandora_OS_tables.i').write_text('\n'.join(table)+'\n')
    source=PROJECT_ROOT/'tools/amiga_pandora_OS.s'
    assembled=subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-Fhunkexe','-m68000','-no-opt',
        '-L',str(out/'Pandora.list'),'-I'+str(out),'-I'+str(PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'),
        '-o',str(out/'Pandora'),str(source)],capture_output=True,text=True)
    (out/'assemble.log').write_text(assembled.stdout+assembled.stderr)
    assembled.check_returncode()
    labels={m[2]:int(m[1],16) for m in re.finditer(r'^([0-9A-F]{8}) (\w+)$',(out/'Pandora.list').read_text(),re.M)}
    if labels['state_leases_end']-labels['state_leases']!=8*(len(OWNERS)+len(fixed)):
        raise ValueError('Owned lease ledger must hold every exact address/size pair')
    (out/'Pandora.payload').write_bytes(data)
    startup=out/'startup-sequence';startup.write_text('Pandora\nprobe2\n')
    subprocess.run([str(xdftool),str(out/'host.adf'),'delete','S/Startup-Sequence','+',
        'write',str(startup),'S/Startup-Sequence','+','write',str(out/'Pandora'),'Pandora','+',
        'write',str(out/'Pandora.payload'),'Pandora.payload'],check=True,capture_output=True)
    return dict(status='normal_HUNK_pre_entry_application_built_not_game_launch',owners=list(OWNERS),
        contract_sha256=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest(),
        payload_sha256=sha(payload),source_sha256=sha(source),HUNK_sha256=sha(out/'Pandora'),
        fixed_lease_intents=fixed,ADF_sha256=sha(out/'host.adf'))


def own_code(hunk):
    """Read only our assembler's single CODE HUNK, not an Amiga loader."""
    words=struct.unpack('>'+str(len(hunk)//4)+'I',hunk)
    if words[:5]!=(1011,0,1,0,0) or words[6]!=1001:
        raise ValueError('Expected the owned single CODE HUNK')
    count=words[7]*4
    return hunk[32:32+count]


def observe_pre_entry(out,rom,copperline):
    """Observe the owned HUNK without changing guest registers or memory."""
    from amiga_reversing.tools.copperline_control import CopperlineProcess
    labels={m[2]:int(m[1],16) for m in re.finditer(r'^([0-9A-F]{8}) (\w+)$',(out/'Pandora.list').read_text(),re.M)}
    code=own_code((out/'Pandora').read_bytes());result={}
    with CopperlineProcess(copperline,rom=rom,floppy=out/'host.adf',machine_profile='a500ecs_1m') as process:
        c=process.client;base=None
        for frame in range(50,551,25):
            stop=c.run_until({'frame':frame},timeout=15)
            if stop.get('reason')!='target':raise ValueError('Incomplete finite DOS boot window')
            ram=c.read_memory(0xc00000,0x80000);offset=ram.find(code[:32])
            if offset>=0:
                if ram.find(code[:32],offset+1)>=0:raise ValueError('Ambiguous owned HUNK prefix')
                base=0xc00000+offset;break
        if base is None:raise ValueError('Owned HUNK not observed in bounded Slow RAM window')
        if c.read_memory(base,labels['immutable_code_end'])!=code[:labels['immutable_code_end']]:
            raise ValueError('Loaded HUNK immutable bytes differ')
        breakpoint=c.add_breakpoint(base+labels['pre_entry_ready'])
        stop=c.run_until({'frame':2000},timeout=45);registers=c.registers()
        if registers['pc']!=base+labels['pre_entry_ready']:raise ValueError('Pre-entry not observed within bounds: '+str(stop))
        raw=c.read_memory(base+labels['host_state'],labels['eof_byte']-labels['host_state'])
        if int.from_bytes(raw[4:8],'big')!=2:raise ValueError('Payload identity stage not complete')
        count=int.from_bytes(raw[8:12],'big')
        if count!=10 or len(raw)<48+8*count:raise ValueError('Exact owned lease ledger is incomplete')
        leases=[dict(address=int.from_bytes(raw[48+8*i:52+8*i],'big'),size=int.from_bytes(raw[52+8*i:56+8*i],'big')) for i in range(count)]
        if any(not r['address'] or not r['size'] for r in leases):raise ValueError('NULL owned lease')
        for i,a in enumerate(leases):
            for b in leases[i+1:]:
                if a['address']<b['address']+b['size'] and b['address']<a['address']+a['size']:
                    raise ValueError('Actual leases overlap')
        data=c.read_memory(0x20000,376832)
        if data!=(out/'Pandora.payload').read_bytes():raise ValueError('Complete staged input differs')
        result.update(stop=stop,registers=registers,HUNK_base=base,leases=leases,
            owners={n:int.from_bytes(raw[24+4*i:28+4*i],'big') for i,n in enumerate(OWNERS)},
            staged_payload_sha256=hashlib.sha256(data).hexdigest())
        c.remove_breakpoint(breakpoint)
        result['after_return']=c.run_until({'frame':2200},timeout=45)
        if result['after_return'].get('reason')!='target':raise ValueError('Incomplete finite return window')
        result['count_after_unwind_at_retained_address']=int.from_bytes(c.read_memory(base+labels['state_count'],4),'big')
        c.request('capture.screenshot',{'path':str(out/'returned.png'),'native':True})
        try:
            c.key(0x44,pressed=True);c.run_until({'frame':2203},timeout=5)
        finally:c.key(0x44,pressed=False)
        c.run_until({'frame':2230},timeout=5)
        c.request('capture.screenshot',{'path':str(out/'after-key.png'),'native':True})
    result.update(status='pre_entry_capture_complete_console_review_required_not_game_launch',
        rom_sha256=sha(rom),emulator_sha256=sha(copperline),HUNK_sha256=sha(out/'Pandora'),
        ADF_sha256=sha(out/'host.adf'),screenshots={n:sha(out/n) for n in ('returned.png','after-key.png')},
        limits=['No host memory/register writes. No game entry or hardware takeover.',
                'Retained post-return memory is supporting evidence, not an Exec free-list proof.',
                'Native atomic admission of these actual returned bases remains a separate required check.'])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--xdftool',type=Path,required=True)
    p.add_argument('--payload',type=Path,required=True);p.add_argument('--native-contract',type=Path,required=True)
    p.add_argument('--run',action='store_true');p.add_argument('--rom',type=Path);p.add_argument('--copperline',type=Path)
    a=p.parse_args();out=a.output.resolve()
    if a.run and (a.rom is None or a.copperline is None):p.error('--run requires explicit ROM and Copperline')
    r=build(out,a.xdftool.resolve(),a.payload.resolve(),json.loads(a.native_contract.read_text()))
    (out/'build.json').write_text(json.dumps(r,indent=2)+'\n')
    if a.run:
        r=observe_pre_entry(out,a.rom.resolve(),a.copperline.resolve())
        (out/'live.json').write_text(json.dumps(r,indent=2)+'\n')
    print(r['status'],flush=True)

if __name__=='__main__':main()

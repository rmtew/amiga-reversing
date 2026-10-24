"""Build and observe Pandora's explicit normal-HUNK hosted profile.

The pre-entry mode checks resource/loading unwind. The game mode binds native
fields and a reviewed lifecycle import, acquires audio/blitter ownership and
returns through the saved host context. Its short fire/F7 observation is not a
saved-Earth playthrough or output-equivalence certification.
"""
import argparse
from contextlib import contextmanager
from amiga_reversing.disasm.behaviour_validation import LoadedSource
import hashlib
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.tools.pandora_os_entry_probe import build as build_host,sha

LOADED_SOURCE=LoadedSource(__file__)

OWNERS=('pandora_prng_state','keyboard_state','pandora_ui_snapshot_body',
        'pandora_title_stars','pandora_cpu_workspace','pandora_low_generated_masks')


def application_sources(data,contract,*,game=False,project_root=PROJECT_ROOT,layout_id='pandora_OS_hosted_ecs1m',expected_payload_sha256='9b0bf6e9747fdaf008983f3c0f9e77910ec9b30f777b0ace95594a41d8833f8b'):
    """Generate owned sources from native bindings; no assembly, disk or emulator."""
    LOADED_SOURCE.require_current()
    files={};plans=contract['candidates'];batch=contract['template_geometry']
    if (len(data)!=376832 or hashlib.sha256(data).hexdigest()!=expected_payload_sha256
            or set(plans)!=set(OWNERS) or batch.get('status')!='actual_placements_valid'
            or batch.get('owner_count')!=6 or batch.get('uncovered_runtime_extents')!=[]):
        raise ValueError('Complete native hosted template and exact preserved payload required')
    if any(plans[n].get('status')!='bounded_allocation_candidate' for n in OWNERS):
        raise ValueError('Refused owner cannot become an Exec request')
    layouts=batch.get('layout',{}).get('items',[])
    if (len(layouts)!=1 or layouts[0].get('status')!='placement_valid'
            or layouts[0].get('layout_id')!=layout_id
            or layouts[0].get('chip_bytes')!=0x100000):
        raise ValueError('Declared ECS hosted native profile required')
    bootstrap=layouts[0].get('bootstrap',{})
    if (bootstrap.get('load_address')!=0x20000 or bootstrap.get('file_size')!=len(data)
            or bootstrap.get('variant')!='forward_disjoint_source_helper'
            or bootstrap.get('helper_runtime_address')!=0x20028):
        raise ValueError('Declared fixed-input owned-helper lifecycle required')
    fixed=batch['fixed_leases_requiring_OS_acquisition']
    if any(r['address']<0x10000 or r['address']%8 or r['size']%8 for r in fixed):
        raise ValueError('Hosted source-helper profile with aligned fixed leases required')
    constants={'OWNER_COUNT':len(OWNERS),'FIXED_COUNT':len(fixed),'INPUT_ADDRESS':0x20000,
               'PAYLOAD_SIZE':len(data),'PAYLOAD_CRC32':zlib.crc32(data)}
    if game:
        constants['HOSTED_GAME']=1
        imported=batch['layout']['items'][0]['bootstrap']['exit_dispatch_import']
        if (imported['status']!='requires_runtime_code_binding' or imported['width']!=4
                or imported['role']!='host_mission_restart_dispatch'
                or int.from_bytes(data[imported['instruction_source_offset']:imported['instruction_source_offset']+2],'big')!=imported['opcode']):
            raise ValueError('Explicit native service import required')
        constants['EXIT_IMPORT_OFFSET']=imported['source_offset']
        constants['ORIGINAL_WORLD_INITIALIZER']=imported['staged_value']
        fixes=[]
        for index,name in enumerate(OWNERS):
            for f in plans[name]['fixups']:
                if (any(type(f[k]) is not int for k in ('source_section_index','source_offset','width','region_offset','staged_value'))
                        or f['source_offset']<0 or not 0<=f['region_offset']<plans[name]['size']
                        or f['staged_value']!=plans[name]['staged_address']+f['region_offset']
                        or f['source_section_index']!=0 or f['address_domain']!='runtime_only'
                        or f['width'] not in (2,4) or f['source_offset']%2
                        or f['source_offset']+f['width']>len(data)
                        or int.from_bytes(data[f['source_offset']:f['source_offset']+f['width']],'big')!=f['staged_value']):
                    raise ValueError('Stale or unsupported native field')
                fixes.append((f,index))
        fixes.sort(key=lambda pair:pair[0]['source_offset'])
        for (a,_),(b,_) in zip(fixes,fixes[1:]):
            if a['source_offset']+a['width']>b['source_offset']:raise ValueError('Duplicate typed field')
        if len(fixes)!=batch['fixup_count']:raise ValueError('Incomplete native field family')
        constants['FIXUP_COUNT']=len(fixes)
        for f,_ in fixes:
            if f['source_offset']<imported['source_offset']+4 and imported['source_offset']<f['source_offset']+f['width']:
                raise ValueError('Import and owner fields overlap')
        if int.from_bytes(data[imported['source_offset']:imported['source_offset']+4],'big')!=imported['staged_value']:
            raise ValueError('Stale original import')
    files['pandora_OS_plan.i']=('\n'.join(f'{n} EQU ${v:X}' for n,v in constants.items())+'\n').encode()
    table=['fixed_table:']+[f"    dc.l ${r['address']:X},${r['size']:X}" for r in fixed]
    table+=['owner_sizes:']+[f"    dc.l ${(plans[n]['size']+7)&~7:X}" for n in OWNERS]
    if game:
        table+=['runtime_fields:']
        for f,index in fixes:
            table.extend((f"    dc.l ${f['source_offset']:X},${f['staged_value']:X}",
                          f"    dc.w {index*4},{f['width']}",f"    dc.l ${f['region_offset']:X}"))
        seeds=[r['loader_seed'] for r in batch['layout']['items'][0]['regions'] if 'loader_seed' in r]
        # Seed initialization is represented by the same frozen native layout,
        # not inferred from allocation contents or zero-filled by this loader.
        if not seeds:
            raise ValueError('Hosted native profile must retain its explicit seed copies')
        seed_source=[]
        for seed in seeds:
            offset=seed['source_offset'];address=seed['runtime_address'];size=seed['size']
            if size not in (2,4) or offset+size>len(data):raise ValueError('Unsupported native seed copy')
            for f,_ in fixes:
                if offset<f['source_offset']+f['width'] and f['source_offset']<offset+size:raise ValueError('Seed source overlaps fixup')
            seed_source.append(f"    move.{'w' if size==2 else 'l'} INPUT_ADDRESS+${offset:X},${address:X}")
        files['pandora_OS_seeds.i']=('\n'.join(seed_source)+'\n').encode()
    table+=['crc_table:']
    for i in range(256):
        crc=i
        for _ in range(8):crc=(crc>>1)^(0xedb88320 if crc&1 else 0)
        table.append(f'    dc.l ${crc:08X}')
    files['pandora_OS_tables.i']=('\n'.join(table)+'\n').encode()
    for name in ('amiga_pandora_OS.s','amiga_pandora_OS_fields.i','amiga_pandora_OS_audio.i','amiga_pandora_OS_takeover.i'):
        files[name]=(project_root/'tools'/name).read_bytes()
    LOADED_SOURCE.require_current()
    return files,fixed


def build(out,xdftool,payload,contract,*,game=False):
    data=payload.read_bytes();files,fixed=application_sources(data,contract,game=game)
    build_host(out,xdftool)
    for name,content in files.items():(out/name).write_bytes(content)
    source=out/'amiga_pandora_OS.s'
    assembled=subprocess.run([str(PROJECT_ROOT/'tools/vasmm68k_mot.exe'),'-Fhunkexe','-m68000','-no-opt',
        '-L',str(out/'Pandora.list'),'-I'+str(out),'-I'+str(PROJECT_ROOT/'tools'),'-I'+str(PROJECT_ROOT/'ext/amiga_includes/ndk_2.0/include'),
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
    return dict(status='normal_HUNK_game_application_built_runtime_pending' if game else 'normal_HUNK_pre_entry_application_built_not_game_launch',owners=list(OWNERS),
        contract_sha256=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest(),
        payload_sha256=sha(payload),source_sha256=sha(source),HUNK_sha256=sha(out/'Pandora'),
        loader_sources_sha256={n:sha(out/n) for n in ('amiga_pandora_OS.s','amiga_pandora_OS_fields.i','amiga_pandora_OS_audio.i','amiga_pandora_OS_takeover.i')},
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


def observe_game(out,rom,copperline,actual_validator,*,route=None,audio_stems=None):
    """Cold DOS launch and ordinary fire/F7 exit with typed/native admission.

    No host guest-state writes; all controller operations are explicitly released.
    By default this is a short lifecycle route. A route adapter can instead
    supply normal inputs and a natural exit boundary; cleanup is shared.
    Breakpoint observations are synchronous CPU evidence, not DMA tracing.
    """
    from amiga_reversing.tools.copperline_control import CopperlineProcess
    labels={m[2]:int(m[1],16) for m in re.finditer(r'^([0-9A-F]{8}) (\w+)$',(out/'Pandora.list').read_text(),re.M)}
    code=own_code((out/'Pandora').read_bytes());report={'status':'incomplete'}
    def record(name,**data):
        report[name]=data;(out/'live.json').write_text(json.dumps(report,indent=2)+'\n')
        print(name,json.dumps(data),flush=True)
    with CopperlineProcess(copperline,rom=rom,floppy=out/'host.adf',machine_profile='a500ecs_1m',audio_stems=audio_stems) as process:
        c=process.client;base=None
        for frame in range(50,551,25):
            stop=c.run_until({'frame':frame},timeout=15)
            if stop.get('reason')!='target':raise ValueError('Incomplete finite host boot window')
            ram=c.read_memory(0xc00000,0x80000);offset=ram.find(code[:32])
            if offset>=0:
                if ram.find(code[:32],offset+1)>=0:raise ValueError('Ambiguous owned HUNK prefix')
                base=0xc00000+offset;break
        if base is None:raise ValueError('Owned HUNK absent in bounded Slow RAM window')
        if c.read_memory(base,labels['immutable_code_end'])!=code[:labels['immutable_code_end']]:
            raise ValueError('Loaded HUNK immutable code differs')
        ready=c.add_breakpoint(base+labels['pre_entry_ready'])
        stop=c.run_until({'frame':2000},timeout=45)
        if c.registers()['pc']!=base+labels['pre_entry_ready']:raise ValueError('Pre-entry not observed within bounds')
        owners={n:int.from_bytes(c.read_memory(base+labels['state_owners']+4*i,4),'big') for i,n in enumerate(OWNERS)}
        native=actual_validator(owners)
        record('actual_admission',HUNK_base=base,stop=stop,owners=owners,native=native)
        if native.get('status')!='actual_placements_valid' or native.get('uncovered_runtime_extents')!=[]:
            raise ValueError('Actual native placement refused; stopped guest will not be released')
        raw=c.read_memory(base+labels['state_leases'],80)
        leases=[dict(address=int.from_bytes(raw[8*i:8*i+4],'big'),size=int.from_bytes(raw[8*i+4:8*i+8],'big')) for i in range(10)]
        expected_leases=[dict(address=r['address'],size=r['size']) for r in native['leases']]+native['fixed_leases_requiring_OS_acquisition']
        if sorted(leases,key=lambda r:r['address'])!=sorted(expected_leases,key=lambda r:r['address']):
            raise ValueError('Actual guest acquisition ledger differs from native backing')
        expected=bytearray((out/'Pandora.payload').read_bytes())
        if c.read_memory(0x20000,len(expected))!=expected:raise ValueError('Complete unbound payload differs')
        for member in native['members']:
            for f in member['fixups']:
                value=owners[member['region_id']]+f['region_offset']
                expected[f['source_offset']:f['source_offset']+f['width']]=value.to_bytes(f['width'],'big')
        imported=native['layout']['items'][0]['bootstrap']['exit_dispatch_import']
        expected[imported['source_offset']:imported['source_offset']+4]=(base+labels['mission_restart_dispatch']).to_bytes(4,'big')
        c.remove_breakpoint(ready)
        failed=c.add_breakpoint(base+labels['failed']);audio_failed=c.add_breakpoint(base+labels['audio_failed']);entry=c.add_breakpoint(0x20000)
        stop=c.run_until({'frame':2200},timeout=45);registers=c.registers()
        record('payload_entry',stop=stop,registers=registers)
        if registers['pc']!=0x20000:raise ValueError('Game entry not observed; failure boundary retained')
        if c.read_memory(0x20000,len(expected))!=expected:raise ValueError('Applied payload differs from native field/import expectation')
        record('field_application',bytes=len(expected),fields=native['fixup_count'],sha256=hashlib.sha256(expected).hexdigest(),whole_input_verified=True)
        for breakpoint in (failed,audio_failed,entry):c.remove_breakpoint(breakpoint)
        dispatched=c.add_breakpoint(base+labels['mission_restart_dispatch'])
        stop=c.run_until({'frame':2600},timeout=45);before=c.registers()
        if before['pc']!=base+labels['mission_restart_dispatch']:raise ValueError('First initialization import missing')
        c.remove_breakpoint(dispatched);original=c.add_breakpoint(imported['staged_value'])
        original_stop=c.run_until({'frame':2600},timeout=30);after=c.registers()
        if after['pc']!=imported['staged_value'] or {k:v for k,v in before.items() if k!='pc'}!={k:v for k,v in after.items() if k!='pc'}:
            raise ValueError('Original initializer state/stack/CCR differs across first import')
        record('first_dispatch',before_stop=stop,before=before,after_stop=original_stop,after=after)
        record('initial_state',PRNG_bytes=c.read_memory(owners['pandora_prng_state'],8).hex())
        c.remove_breakpoint(original)
        if route is None:
            deadline=3400
            stop=c.run_until({'frame':2700},timeout=45)
            if stop.get('reason')!='target':raise ValueError('Incomplete title window')
            c.request('capture.screenshot',{'path':str(out/'title.png'),'native':True})
            record('settled_title',stop=stop,registers=c.registers(),
                PRNG_bytes=c.read_memory(owners['pandora_prng_state'],8).hex(),
                title_stars_sha256=hashlib.sha256(c.read_memory(owners['pandora_title_stars'],1000)).hexdigest())
            try:
                c.joystick(port=2,red=True);c.run_until({'frame':2710},timeout=5)
            finally:c.joystick(port=2,red=False)
            stop=c.run_until({'frame':2900},timeout=15)
            if stop.get('reason')!='target':raise ValueError('Incomplete gameplay window')
            c.request('capture.screenshot',{'path':str(out/'gameplay.png'),'native':True})
            record('gameplay_window',stop=stop,registers=c.registers())
            quiescent=c.add_breakpoint(base+labels['game_DMA_quiescent'])
            try:
                c.key(0x56,pressed=True);stop=c.run_until({'frame':2950},timeout=10)
            finally:c.key(0x56,pressed=False)
            if c.registers()['pc']!=base+labels['game_DMA_quiescent']:
                stop=c.run_until({'frame':deadline},timeout=15)
        else:
            stop,deadline=route(c,base,labels,native,out,record)
        custom=c.request('custom.read',{'reg':2})
        record('quiescence_raw_observation',stop=stop,registers=c.registers(),custom_read=custom)
        dma=custom['value']
        if type(dma) is not int:raise ValueError('Unsupported live DMACONR response')
        if c.registers()['pc']!=base+labels['game_DMA_quiescent'] or dma&0x47ff:
            raise ValueError('Game blitter/DMA quiescence not observed')
        record('game_DMA_quiescent',stop=stop,DMACONR=dma,all_game_leases_still_owned=int.from_bytes(c.read_memory(base+labels['state_count'],4),'big'))
        if report['game_DMA_quiescent']['all_game_leases_still_owned']!=10:raise ValueError('Lease freed before DMA stopped')
        if route is None:c.remove_breakpoint(quiescent)
        user_return=c.add_breakpoint(base+labels['host_user_return'])
        stop=c.run_until({'frame':deadline},timeout=15)
        if c.registers()['pc']!=base+labels['host_user_return']:raise ValueError('Supervisor return not observed')
        record('host_user_return',stop=stop,registers=c.registers())
        c.remove_breakpoint(user_return)
        free=c.add_breakpoint(base+labels['free_owned_lease_call']);freed=[]
        for expected_lease in reversed(leases):
            stop=c.run_until({'frame':deadline},timeout=20);registers=c.registers()
            value=dict(address=registers['a1'],size=registers['d0'])
            if registers['pc']!=base+labels['free_owned_lease_call'] or value!=expected_lease:
                raise ValueError('Unexpected owned FreeMem argument or exit boundary')
            freed.append(value);c.remove_breakpoint(free)
            returned=c.add_breakpoint(base+labels['free_owned_lease_return'])
            stop=c.run_until({'frame':deadline},timeout=20)
            if c.registers()['pc']!=base+labels['free_owned_lease_return']:raise ValueError('Owned FreeMem did not return')
            c.remove_breakpoint(returned);free=c.add_breakpoint(base+labels['free_owned_lease_call'])
        c.remove_breakpoint(free)
        finish_frame=3400 if route is None else stop['frame']+300
        stop=c.run_until({'frame':finish_frame},timeout=20)
        if stop.get('reason')!='target':raise ValueError('Incomplete DOS return window')
        c.request('capture.screenshot',{'path':str(out/'returned.png'),'native':True})
        try:
            c.key(0x44,pressed=True);c.run_until({'frame':finish_frame+3},timeout=5)
        finally:c.key(0x44,pressed=False)
        c.run_until({'frame':finish_frame+30},timeout=5)
        c.request('capture.screenshot',{'path':str(out/'after-key.png'),'native':True})
        record('owned_exit',freed=freed,retained_count=int.from_bytes(c.read_memory(base+labels['state_count'],4),'big'),
            audio_open=int.from_bytes(c.read_memory(base+labels['state_audio_open'],4),'big'),
            audio_lock=int.from_bytes(c.read_memory(base+labels['state_audio_lock'],4),'big'),
            signal=int.from_bytes(c.read_memory(base+labels['state_signal'],4),'big'))
        state=report['owned_exit']
        if (state['retained_count'],state['audio_open'],state['audio_lock'],state['signal'])!=(0,0,0,0xffffffff):
            raise ValueError('Exit ownership state is incomplete')
    report.update(status=('short_OS_game_entry_exit_capture_complete_console_review_required' if route is None else 'hosted_saved_earth_natural_exit_cold_route_complete'),
        rom_sha256=sha(rom),emulator_sha256=sha(copperline),HUNK_sha256=sha(out/'Pandora'),ADF_sha256=sha(out/'host.adf'),
        screenshots={n:sha(out/n) for n in (('title.png','gameplay.png','returned.png','after-key.png') if route is None else ('returned.png','after-key.png'))},
        limits=['Short fire/F7 route unless the explicit completion adapter is supplied; captures alone are not pixel/PCM equivalence.',
            'Synchronous CPU/DMACONR observations only; no bus-wide DMA or all-path coverage.',
            'Caller-owned HUNK remains owned by DOS LoadSeg; game leases are retained through hardware return and then freed exactly once.',
            'Declared exclusive 68000/ECS profile; not universal multitasking, RTG or original pre-entry timing identity.'])
    (out/'live.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


@contextmanager
def native_hosted_context():
    from amiga_reversing.disasm.c_backend import build_listing_artifact_profile_from_binary_source
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from amiga_reversing.disasm.effective_metadata import effective_metadata_file
    from amiga_reversing.disasm.restoration import revisions
    from amiga_reversing.tools.pandora_layout_walkthrough import TARGET
    paths=resolve_project_paths(TARGET);layout_id='pandora_OS_hosted_ecs1m';before=revisions(TARGET)
    print('Building one native hosted context for template and actual returns',flush=True)
    with effective_metadata_file(paths.target_dir,layout_id=layout_id) as metadata:
        artifact=build_listing_artifact_profile_from_binary_source(paths.binary_source,metadata_path=metadata,project_root=PROJECT_ROOT)[2]
        try:
            def stable():
                if revisions(TARGET)!=before:raise ValueError('Canonical target changed; hosted admission is stale')
                artifact.loaded_backend_identity()
            stable();plans={n:artifact.runtime_allocation_plan(n,layout_id) for n in OWNERS}
            if any(v.get('status')!='bounded_allocation_candidate' for v in plans.values()):
                raise ValueError('Native owner template refuses')
            def validate(owners):
                stable()
                return artifact.runtime_allocation_batch_plan(layout_id,dict(schema_version=1,layout_id=layout_id,
                    chip_bytes=0x100000,placements=[dict(region_id=n,runtime_address=owners[n]) for n in OWNERS]))
            batch=validate({n:v['staged_address'] for n,v in plans.items()})
            yield dict(backend=artifact.loaded_backend_identity(),candidates=plans,template_geometry=batch),validate
            stable()
        finally:artifact.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--xdftool',type=Path,required=True)
    p.add_argument('--payload',type=Path,required=True);p.add_argument('--native-contract',type=Path)
    p.add_argument('--game',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--rom',type=Path);p.add_argument('--copperline',type=Path)
    p.add_argument('--route-scenario',type=Path,help='Existing compiled 576-phase completion route; otherwise short fire/F7 observation')
    p.add_argument('--title-capture',action='store_true',help='Bounded original-helper settled title capture; emulator stop is not an OS-return test')
    p.add_argument('--audio-stems',type=Path,help='Private master/Paula/drive WAV capture directory')
    a=p.parse_args();out=a.output.resolve()
    if a.run and (a.rom is None or a.copperline is None):p.error('--run requires explicit ROM and Copperline')
    if (a.route_scenario or a.title_capture or a.audio_stems) and not (a.game and a.run):p.error('Route/title/audio capture requires --game --run')
    if a.route_scenario and a.title_capture:p.error('Choose the completion route or title prefix')
    if a.game and a.run:
        with native_hosted_context() as (contract,validate):
            r=build(out,a.xdftool.resolve(),a.payload.resolve(),contract,game=True)
            (out/'native-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
            (out/'build.json').write_text(json.dumps(r,indent=2)+'\n')
            route=None
            if a.route_scenario:
                from amiga_reversing.tools.pandora_hosted_route import HostedRoute
                route=HostedRoute(json.loads(a.route_scenario.read_text()))
            observer=observe_game
            options=dict(route=route)
            if a.title_capture:
                from amiga_reversing.tools.pandora_hosted_title import observe_title
                observer=observe_title;options={}
            r=observer(out,a.rom.resolve(),a.copperline.resolve(),validate,**options,
                audio_stems=a.audio_stems.resolve() if a.audio_stems else None)
        print(r['status'],flush=True)
        return
    if a.native_contract is None:p.error('Build-only/pre-entry mode requires --native-contract')
    r=build(out,a.xdftool.resolve(),a.payload.resolve(),json.loads(a.native_contract.read_text()),game=a.game)
    (out/'build.json').write_text(json.dumps(r,indent=2)+'\n')
    if a.run:
        r=observe_pre_entry(out,a.rom.resolve(),a.copperline.resolve())
        (out/'live.json').write_text(json.dumps(r,indent=2)+'\n')
    print(r['status'],flush=True)

if __name__=='__main__':main()

"""Explicit Pandora ORG/copy-bypass experiment; NOT general rebase admission.

Run this file by pathname with an explicit qualified checkout and private output
directory. It preserves canonical source/binary and uses normal controller input.
The diagnostic profile expands Chip RAM/ECS so the FULL image is disjoint from
old game storage and fixed buffers. It is not an original-profile equivalence test.
"""
import argparse,copy,hashlib,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch

BASE=0x80000
ORIGINAL=0x10000
TARGET='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def require(condition,message):
    if not condition:raise ValueError(message)
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def symbolic_repairs(text):
    """Only reviewed pointer families; no address-shaped-word scanning."""
    edits=[]
    start=text.index('scene_restart_receptacle_state_ptrs:\n')
    end=text.index('item_receptacle_lifecycle_records:\n',start)
    before=text[start:end]
    targets=['item_receptacle_lifecycle_records']+[f'item_receptacle_{i}_primary_state' for i in range(1,6)]
    after='scene_restart_receptacle_state_ptrs:\n'+''.join(f'\tdc.l {name}\n' for name in targets)
    edits.append((before,after))
    # The six primary-state +$1A fields feed the same restart consumer.
    pointers=[0x588FE,0x58940,0x58982,0x589C4,0x58A06,0x58A66]
    for i,address in enumerate(pointers):
        owner=f'item_receptacle_{i}_primary_interaction_data_ptr'
        before=f'{owner}:\n\tdc.l ${address:08X}'
        after=f'{owner}:\n\tdc.l item_receptacle_{i}_interaction_data'
        edits.append((before,after))
    # Copper high/low words derive from this alias; CPU/blitter references
    # already use the actual blank_sprite_data label.
    edits.append(('sprite_0005D5DE\tEQU\t$5D5DE','sprite_0005D5DE\tEQU\tblank_sprite_data'))
    edits.append(('blank_graphics_mask_data\tEQU\t$5D5DE','blank_graphics_mask_data\tEQU\tblank_sprite_data'))
    # The player's typed CALL_FUNCTION and JUMP_ABSOLUTE loop commands.
    for alias,address,target in [
        ('dblk_ref_h0_000095E2_runtime_000195E2',0x195E2,'update_player_world_movement'),
        ('dblk_ref_h0_0004C312_runtime_0005C312',0x5C312,'player_movement_script_loop'),
    ]:
        edits.append((f'{alias}\tEQU\t${address:X}',f'{alias}\tEQU\t{target}'))
    # Eight 18-byte collision/graphics records, selected by combat feedback.
    for i in range(8):
        offset=0x484F8+18*i;address=ORIGINAL+offset
        alias=f'dblk_ref_h0_{offset:08X}_runtime_{address:08X}'
        edits.append((f'{alias}\tEQU\t${address:X}',
                      f'{alias}\tEQU\tcombat_hit_feedback_geometry_records+{18*i}'))
    for offset,target in [(0x4859A,'ranged_hit_visual_descriptor'),(0x485A6,'opponent_combat_hit_visual_descriptor')]:
        address=ORIGINAL+offset;alias=f'dblk_ref_h0_{offset:08X}_runtime_{address:08X}'
        edits.append((f'{alias}\tEQU\t${address:X}',f'{alias}\tEQU\t{target}'))
    for before,after in edits:
        require(text.count(before)==1,'Reviewed pointer repair anchor differs')
        text=text.replace(before,after)
    return text,edits


def build(root,out,original_control=False,matched_startup=False):
    qualification=load(root/'runtime/observations/pandora-saved-earth-walkthrough.json')
    target=root/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
    original=target/'binary.bin';source=next(target.glob('*.s'))
    require(sha(original)==qualification['input_identities']['original_payload_sha256'],'Original binary differs')
    require(sha(source)==qualification['input_identities']['original_rendered_source_sha256'],'Original source differs')
    exact=load(root/'.runtime-state/pandora-app-usage-closure/exact.json')
    package=root/'bin/rebuilt'/TARGET/'source-packages'/exact['source_package_sha256']
    require(sha(package/source.name)==sha(source),'Source package differs')
    text,repairs=(source.read_text(),[]) if original_control else symbolic_repairs(source.read_text())
    reference_text=text
    edits=[] if original_control else [('    ORG $10000','    ORG $80000'),
        ('\tmove.l #$55370,d0\n\tcmpa.l a2,a1','\tmove.l #$55370,d0\n\tcmpa.l a1,a2') if matched_startup else
        ('\tlea.l fixed_base_image_copy_stub(pc),a0','\tbra.w initialize_runtime_workspace')]
    for before,after in edits:require(text.count(before)==1,'Experimental source anchor differs');text=text.replace(before,after)
    out.mkdir(parents=True,exist_ok=False);experimental=out/'experiment.s';experimental.write_text(text)
    assets={name:sha(package/name) for name in re_incbin(source.read_text())}
    payload=out/'experiment.bin';listing=out/'experiment.lst'
    command=[str(root/'tools/vasmm68k_mot.exe'),'-Fbin','-m68000','-no-opt','-I',str(root/'ext/amiga_includes/ndk_2.0/include'),'-I',str(package),'-L',str(listing),'-o',str(payload),str(experimental)]
    completed=subprocess.run(command,capture_output=True,text=True);(out/'assemble.log').write_text(completed.stdout+completed.stderr)
    require(completed.returncode==0,'Experimental assembly failed; inspect assemble.log')
    reference=out/'repairs-at-original-base.s';reference.write_text(reference_text)
    reference_bin=out/'repairs-at-original-base.bin'
    checked=subprocess.run(command[:command.index('-L')]+['-o',str(reference_bin),str(reference)],capture_output=True,text=True)
    require(checked.returncode==0 and reference_bin.read_bytes()==original.read_bytes(),
            'Symbolic reference repairs are not byte exact at original ORG')
    require(payload.stat().st_size==original.stat().st_size==376832,'Instruction/source extent changed')
    if original_control:require(payload.read_bytes()==original.read_bytes(),'Original control is not the canonical binary')
    else:require(BASE+payload.stat().st_size==0xDC000<=0x100000 and BASE>=0x80000,'New image overlaps original/fixed low Chip RAM')
    from amiga_reversing.disasm.app_access_audit import decode_retained_instruction
    rows=load(root/'.runtime-state/pandora-app-access-audit/instructions.json');data=payload.read_bytes()
    for row in rows:
        pc=row['source_offset'];fact=decode_retained_instruction(data[pc:pc+row['size']],project_root=root)
        require(fact['size']==row['size'],'Canonical observation offset changed')
    config={'experimental_only':True,'general_native_plan_admission':False,'original_source_sha256':sha(source),'original_binary_sha256':sha(original),
        'original_control':original_control,'matched_startup':matched_startup,'assembly_base':ORIGINAL if original_control else BASE,
        'load_address':0x20000 if original_control or matched_startup else BASE,'entrypoint':0x20000 if original_control or matched_startup else BASE,
        'full_image_interval':[0x20000,0x20000+len(data)] if original_control or matched_startup else [BASE,BASE+len(data)],'old_materialized_interval':[0x10000,0x65370],
        'profile':{'model':'A500','chipset':'ECS','video':'PAL','cpu':'68000','chip':'1M','slow':'512K','fast':'0'},
        'original_profile_unchanged':True,'original_profile_equivalence_claimed':False,
        'reference_repairs_original_base_exact':True,
        'source_edits':[{'before':a,'after':b} for a,b in repairs+edits],'assets_sha256':assets,'payload_sha256':sha(payload),'source_sha256':sha(experimental),
        'native_instruction_extents_checked':len(rows),'changed_instruction_extents':0,'tool_sha256':sha(Path(__file__))}
    write(out/'experiment-config.json',config)
    return payload,config


def re_incbin(text):
    import re
    return sorted(set(re.findall(r'^\s*INCBIN\s+"([^"]+)"',text,re.MULTILINE|re.IGNORECASE)))


def ending_outcome(scenario,runtime_base=BASE):
    phases=scenario['phases'];require(len(phases)==576 and all(p['status']=='hit' for p in phases),'Incomplete ending route')
    require(all(p['pc']==p['address'] and runtime_base<=int(p['pc'],0)<runtime_base+0x5C000 for p in phases),'Unmoved phase execution')
    selected=phases[-2];require(selected['name']=='es_saved_earth_outcome_selected' and int(selected['pc'],0)==runtime_base+0x4C9DC,'Wrong ending selection')
    require(phases[-1]['name']=='es_escape_commit_inhibited' and int(phases[-1]['pc'],0)==runtime_base+0x4C99C,'Escape not committed')
    capture=selected['capture'];require(int(capture['registers']['a0'],0)==runtime_base+0x4CAE5,'Wrong ending message')
    reads={int(r['address'],0):bytes.fromhex(r['bytes']) for r in capture['memory_reads']}
    require(reads[0x3D27]==b'\xff' and reads[0x3D38]==b'\x5c','Earth/escape state differs')
    require(reads[runtime_base+0x4C35E]==b'\x00\x31' and reads[runtime_base+0x4CAE5]==b'CONGRATU','Health or saved-Earth text differs')
    require(all(r['outcome']=='acknowledged' for r in scenario['input_trace']),'Uncertain controller input')
    return {'saved_earth':True,'escaped':True,'health':49,'message_pointer':runtime_base+0x4CAE5,
            'selection_pc':runtime_base+0x4C9DC,'final_frame':phases[-1]['stop_event']['frame']}


def summarize_dma(directory):
    """Two complete frames, using the existing fixed slot decoder and checks."""
    from collections import Counter
    from amiga_reversing.tools.copperline_bus_trace import read_bus_profile,SLOT,KINDS
    checked=read_bus_profile(directory,[],3);counts=Counter();old=[]
    complete=[frame for frame in checked['frames'] if not frame.get('partial')]
    require(len(complete)>=2,'Fewer than two complete DMA frames')
    selected={frame['frame'] for frame in complete[-2:]}
    metadata=[json.loads(line) for line in (directory/'profile.jsonl').read_text().splitlines() if line.strip()]
    for frame in metadata:
        if frame['frame'] not in selected:continue
        for reg,kind,subtype,size,ipl,flags,address,data,events in SLOT.iter_unpack((directory/frame['slots_file']).read_bytes()):
            if not 1<=size<=8:continue
            engine=KINDS.get(kind,'unknown')
            domain='old_image' if address<0x65370 and address+size>ORIGINAL else 'moved_image' if address<0xDC000 and address+size>BASE else 'fixed_or_other'
            counts[engine,domain]+=1
            if domain=='old_image' and len(old)<32:old.append({'frame':frame['frame'],'engine':engine,'address':address,'width':size})
    return {'frames':[frame for frame in complete if frame['frame'] in selected],
            'discarded_partial_frames':[frame['frame'] for frame in checked['frames'] if frame.get('partial')],
            'validated_slots':checked['scanned_slots'],
            'counts':[{'engine':k[0],'domain':k[1],'transfers':v} for k,v in sorted(counts.items())],
            'first_old_image_transfers':old,'scope':'Two sampled frames only, not whole-route DMA coverage.'}


def observe(root,out,payload,config,rom,binary,inspect_output=False,capture_pcm=False,stop_after=None,title_visits=0,pcm_stems=False,phase_locked_boot=False):
    from amiga_reversing.tools.direct_payload_adapter import DirectPayloadContract,build_boot_adf
    from amiga_reversing.tools.copperline_control import CopperlineProcess
    from amiga_reversing.tools.copperline_runtime import wait_for_marker,verify_handoff,release_handoff,wait_for_pc,run_scenario
    runtime_base=config['assembly_base'];load_base=config['load_address']
    contract=DirectPayloadContract('pandora-explicit-rebase','pandora-experimental',sha(payload),load_base,config['entrypoint'],{'a1':load_base},0x7FFF8,0x48414E44)
    adf=out/'experiment.adf';write(out/'boot-build.json',build_boot_adf(contract,payload,adf))
    old_popen=subprocess.Popen
    def launch(command,*args,**kwargs):
        command=list(command)
        if Path(command[0]).name=='copperline':
            for flag,value in [('--model','A500'),('--chipset','ECS'),('--chip','1M')]:command[command.index(flag)+1]=value
            if capture_pcm or pcm_stems:
                command=[part for part in command if part!='--noaudio']
                command+=(['--audio-stems',str(out/'audio-stems'),'--audio-stems-mode','master,source'] if pcm_stems else ['--audio-wav',str(out/'mixed-audio.wav')])
        return old_popen(command,*args,**kwargs)
    report={'experimental_only':True,'config':config,'payload_sha256':sha(payload),'adf_sha256':sha(adf),'rom_sha256':sha(rom),'emulator_sha256':sha(binary),'moved_pcs':[]}
    try:
        with patch('amiga_reversing.tools.copperline_control.subprocess.Popen',launch):
            with CopperlineProcess(binary,rom=rom,floppy=adf) as process:
                client=process.client;report['boot_marker']=wait_for_marker(client,0x7FFF8,contract.handoff_marker_value.to_bytes(4,'big'),90)
                require(report['boot_marker']['matched'],'Boot handoff missing')
                report['handoff']=verify_handoff(client,contract,payload)
                if phase_locked_boot:
                    stop=client.run_until({'cck':500*71051},timeout=30)
                    require(stop.get('reason')=='target' and client.read_memory(0x7FFF8,4)==b'HAND','Boot phase fixture did not remain in handoff')
                    report['boot_phase_fixture']={'target_cck':500*71051,'stop':stop,'registers':client.registers(),'method':'Natural execution of unchanged HAND wait loop before GO; no game state changed.'}
                release_handoff(client,contract)
                for offset in [0,0x46A,0x48C]:
                    address=load_base if offset==0 else runtime_base+offset
                    stop=wait_for_pc(client,address,30);require(stop['status']=='hit','Runtime entry was not observed')
                    require(client.read_memory(address,16)==payload.read_bytes()[offset:offset+16],'Experimental PC bytes differ')
                    report['moved_pcs'].append({'source_offset':offset,'runtime_pc':client.registers()['pc'],'frame':stop['stop_event']['frame'],'stop_event':stop['stop_event']})
                    print('MOVED_PC',hex(client.registers()['pc']),flush=True)
                    if offset==0x46A and config.get('matched_startup'):
                        require(client.read_memory(runtime_base,0x55370)==payload.read_bytes()[:0x55370],'Native moved copy differs')
                        report['native_materialization']={'address':runtime_base,'size':0x55370,'sha256':hashlib.sha256(payload.read_bytes()[:0x55370]).hexdigest(),'full_prefix_verified':True}
                if runtime_base!=ORIGINAL:
                    watch={'kind':'mmio','addr':0x10000,'len':0x55370,'access':'access'}
                    ident=client.request('break.add',watch)['id']
                    for address in [0x10000,0x1046A]:client.add_breakpoint(address)
                    report['guards']={'CPU_data':watch,'fallback_PC_sentinels':[0x10000,0x1046A],'all_instruction_fetches_covered':False,'DMA_covered':False,'readback':client.request('break.list')}
                    require(any(r.get('id')==ident and all(r.get(k)==v for k,v in watch.items()) for r in report['guards']['readback']['breaks']),'Old data guard readback differs')
                else:report['guards']={'original_control':True,'reason':'Original materialized range is intentionally live.'}
                scenario=copy.deepcopy(load(root/'.runtime-state/pandora-player/finale-cold-b/compiled.json'))
                if stop_after is not None:
                    names=[phase['name'] for phase in scenario['phases']];require(stop_after in names,'Unknown bounded prefix end')
                    last=names.index(stop_after);scenario['phases']=scenario['phases'][:last+1]
                    events=[]
                    for event in scenario['input_events']:
                        if names.index(event['after_phase'])>=last:continue
                        if names.index(event['release_after_phase'])>last:event['release_after_phase']=stop_after
                        events.append(event)
                    scenario['input_events']=events
                if title_visits:
                    require(stop_after=='title_menu_loop' and type(title_visits) is int and 1<=title_visits<=240,'Title-only frame bound required')
                view={'base_addr':runtime_base,'source_start':0,'source_end':0x55370,'runtime_base':runtime_base,'execution_view_id':'explicit-experiment-not-native-proof'}
                def moved(address):return runtime_base+address-ORIGINAL if ORIGINAL<=address<0x65370 else address
                def update_read(read):
                    address=read.get('address')
                    if address is not None:read['address']=moved(address)
                    # Only explicit pointer-typed field expectations. Never scan
                    # XY/item/table bytes for address-looking scalar values.
                    if 'expect_hex' in read and address in (0x3B9A,0x3B9E,0x3BBA):
                        data=bytearray.fromhex(read['expect_hex'])
                        if len(data)>=4:data[:4]=moved(int.from_bytes(data[:4],'big')).to_bytes(4,'big')
                        read['expect_hex']=data.hex()
                for phase in scenario['phases']:
                    phase.update(breakpoint_address=runtime_base+phase['source_offset'],runtime_view=view)
                    for read in phase.get('capture',{}).get('memory_reads',[]):update_read(read)
                    if 'until_memory' in phase:update_read(phase['until_memory'])
                scenario['symbols']['runtime_view']=view
                for function in scenario['symbols'].get('functions',[]):function.update(runtime_start=runtime_base+function['source_start'],runtime_end=runtime_base+function['source_end'])
                write(out/'runtime-scenario.json',scenario)
                # A narrow known live app write supplies global stream-loss
                # counters. Old-image accesses are stopped synchronously by
                # the guard above, independently of asynchronous notifications.
                loss={'events':0,'dropped_notifications':0,'dropped_events':0}
                queue=client.events
                class Sink:
                    def append(self,message):
                        if message.get('method')=='event.mmio':
                            data=message['params'];loss['events']+=1
                            for key in ('dropped_notifications','dropped_events'):
                                require(type(data.get(key)) is int and data[key]>=0,'Missing stream loss counter')
                                loss[key]=max(loss[key],data[key])
                        queue.append(message)
                    def __iter__(self):return iter(queue)
                client.events=Sink()
                heartbeat={'addr':0x3B9A,'len':4,'access':'write'}
                client.request('events.subscribe',{'events':['mmio'],'mmio':[heartbeat]})
                report['loss_monitor']={'filter':heartbeat,'readback':client.request('events.list'),'counters':loss}
                import amiga_reversing.tools.copperline_runtime as runtime
                phase_runner=runtime._run_scenario_phase
                media=[];active=None;dma=[]
                def finish_profile():
                    nonlocal active
                    if active is not None:
                        client.request('profile.stop');dma.append({'phase':active['name'],**summarize_dma(active['path'])});active=None
                def progress(*args,**kwargs):
                    nonlocal active
                    result=phase_runner(*args,**kwargs);event=result.get('stop_event') or {}
                    if stop_after=='title_menu_loop' and title_visits>0 and result['status']=='hit':
                        # No inputs: allow real title frames, then re-anchor at
                        # the same original helper. Visit counts alone only
                        # iterate stars within one frame.
                        stop=client.run_until({'frame':event['frame']+title_visits},timeout=30)
                        require(stop.get('reason')=='target','Title hold stopped unexpectedly')
                        options=dict(kwargs,depart_current=client.registers()['pc']==args[1]['breakpoint_address'],start_event=stop)
                        result=phase_runner(*args,**options);event=result.get('stop_event') or {}
                        report['title_no_input_hold_frames']=title_visits
                    row={'name':result['name'],'status':result['status'],'frame':event.get('frame'),'pc':result.get('pc')}
                    with (out/'progress.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
                    print('PHASE',json.dumps(row),flush=True)
                    if inspect_output and result['status']=='hit':
                        if active is not None and event.get('frame',0)>=active['frame']+4:finish_profile()
                        if result['name'] in ('title_menu_loop','ui_overlay_initialization','initial_proximity_context','entry_officer_card_transferred','ei_sonicdriver_hit_1','ac_console_ready'):
                            image=out/(result['name']+'.png')
                            media.append({'phase':result['name'],'frame':event['frame'],'capture':client.request('capture.screenshot',{'path':str(image),'native':True}),'sha256':sha(image)})
                        if result['name'] in ('initial_proximity_context','ei_sonicdriver_hit_1'):
                            require(active is None,'Overlapping output profiles')
                            directory=out/('dma-'+result['name'])
                            client.request('profile.start',{'path':str(directory),'frames':3,'slots':True,'memory':False,'screenshots':'none','pc_samples':True})
                            active={'name':result['name'],'path':directory,'frame':event['frame']}
                    return result
                with patch('amiga_reversing.tools.copperline_runtime._run_scenario_phase',progress):
                    report['scenario']=run_scenario(client,scenario,payload,trace_directory=out)
                client.request('events.unsubscribe',{'events':['mmio']});client.events=queue
                report['output_observations']={'screenshots':media,'dma':dma}
                report['registers_at_stop']=client.registers();pc=report['registers_at_stop']['pc'];report['pc_bytes_at_stop']=client.read_memory(pc,32).hex()
                report['stack_at_stop']=client.read_memory(report['registers_at_stop']['a7'],32).hex()
                report['status']='first_failure'
                if stop_after and all(p['status']=='hit' for p in report['scenario']['phases']):
                    finish_profile();report['status']='bounded_output_prefix_complete';report['prefix_end']=stop_after
                if len(report['scenario']['phases'])==576 and all(p['status']=='hit' for p in report['scenario']['phases']):
                    report['ending']=ending_outcome(report['scenario'],runtime_base)
                    require(loss['events']>0 and loss['dropped_events']==loss['dropped_notifications']==0,'Incomplete event loss accounting')
                    if inspect_output:
                        finish_profile();directory=out/'dma-ending'
                        client.request('profile.start',{'path':str(directory),'frames':3,'slots':True,'memory':False,'screenshots':'none','pc_samples':True})
                        stop=client.run_until({'frame':report['ending']['final_frame']+30},timeout=30)
                        require(stop.get('reason')=='target','Unexpected access during post-ending observation')
                        client.request('profile.stop');dma.append({'phase':'post_ending',**summarize_dma(directory)})
                        image=out/'saved-earth.png';media.append({'phase':'post_ending','frame':stop['frame'],'capture':client.request('capture.screenshot',{'path':str(image),'native':True}),'sha256':sha(image)})
                        report['post_ending_stop']=stop
                    report['status']='saved_earth_and_escaped_original_control' if config.get('original_control') else 'saved_earth_and_escaped_relocated_cold_boot'
    except BaseException as exc:
        report['status']='experiment_error';report['error']={'type':type(exc).__name__,'message':str(exc)};raise
    finally:
        if capture_pcm and (out/'mixed-audio.wav').exists():report['PCM']={'sha256':sha(out/'mixed-audio.wav'),'bytes':(out/'mixed-audio.wav').stat().st_size}
        if pcm_stems:report['PCM_stems']=[{'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted((out/'audio-stems').glob('*.wav'))]
        write(out/'report.json',report);print('RESULT',report['status'],flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qualified-checkout',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--run',action='store_true');p.add_argument('--inspect-output',action='store_true');p.add_argument('--original-control',action='store_true');p.add_argument('--matched-startup',action='store_true');p.add_argument('--phase-locked-boot',action='store_true');p.add_argument('--capture-pcm',action='store_true');p.add_argument('--pcm-stems',action='store_true');p.add_argument('--stop-after');p.add_argument('--title-frames',type=int,default=0);p.add_argument('--rom',type=Path);p.add_argument('--copperline',type=Path);args=p.parse_args();root=args.qualified_checkout.resolve()
    require(not args.run or (args.rom and args.copperline),'Run requires explicit legal ROM and Copperline paths')
    sys.path.insert(0,str(root));import amiga_reversing.tools.copperline_runtime as runtime
    require(Path(runtime.__file__).resolve().is_relative_to(root),'Invoke this experiment by file pathname to use the explicit qualified runtime')
    out=args.output.resolve();payload,config=build(root,out,args.original_control,args.matched_startup)
    if args.run:observe(root,out,payload,config,args.rom.resolve(),args.copperline.resolve(),args.inspect_output,args.capture_pcm,args.stop_after,args.title_frames,args.pcm_stems,args.phase_locked_boot)

if __name__=='__main__':main()

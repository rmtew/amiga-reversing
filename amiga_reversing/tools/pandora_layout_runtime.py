"""Bounded Pandora observations consuming a normal native layout export.

Builds belong to source_export and pandora_layout_walkthrough. This module only
runs the admitted payload/explicit normal-input route and records scoped evidence.
Historical experiment receipts remain readable by the offline comparator.
"""
import copy,hashlib,json
from pathlib import Path

TARGET='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def require(condition,message):
    if not condition:raise ValueError(message)
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def runtime_context(config):
    """Integrity checks on consumed native coordinates, never a placement model."""
    require(config.get('normal_layout_export') is True,'Normal native layout export required; legacy experiment admission is retired')
    plan=config.get('layout_plan')
    require(isinstance(plan,dict) and plan.get('status')=='placement_valid','Native layout plan required')
    require(hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()==config.get('layout_plan_sha256'),'Native layout plan identity differs')
    bootstrap=plan.get('bootstrap')
    require(isinstance(bootstrap,dict) and bootstrap.get('kind')=='retained_prefix_copy','Retained initialization contract required')
    image=next((r for r in plan['regions'] if r['region_id']==bootstrap['image_region_id']),None)
    require(image is not None and image['region_kind']=='image' and image['size']==bootstrap['copied_source_end'],'Native copied-image extent differs')
    require(config.get('assembly_base')==image['runtime_address'] and config.get('load_address')==bootstrap['load_address'] and config.get('entrypoint')==bootstrap['load_address'],'Runtime coordinates differ from native plan')
    require(config.get('copied_prefix_bytes')==image['size'] and config.get('old_materialized_interval')==[image['original_address'],image['original_address']+image['size']],'Runtime image bounds differ from native plan')
    return image,bootstrap


def ending_outcome(scenario,runtime_base,image_size):
    phases=scenario['phases'];require(len(phases)==576 and all(p['status']=='hit' for p in phases),'Incomplete ending route')
    require(all(p['pc']==p['address'] and runtime_base<=int(p['pc'],0)<runtime_base+image_size for p in phases),'Unmoved phase execution')
    selected=phases[-2];require(selected['name']=='es_saved_earth_outcome_selected' and int(selected['pc'],0)==runtime_base+0x4C9DC,'Wrong ending selection')
    require(phases[-1]['name']=='es_escape_commit_inhibited' and int(phases[-1]['pc'],0)==runtime_base+0x4C99C,'Escape not committed')
    capture=selected['capture'];require(int(capture['registers']['a0'],0)==runtime_base+0x4CAE5,'Wrong ending message')
    reads={int(r['address'],0):bytes.fromhex(r['bytes']) for r in capture['memory_reads']}
    require(reads[0x3D27]==b'\xff' and reads[0x3D38]==b'\x5c','Earth/escape state differs')
    require(reads[runtime_base+0x4C35E]==b'\x00\x31' and reads[runtime_base+0x4CAE5]==b'CONGRATU','Health or saved-Earth text differs')
    require(all(r['outcome']=='acknowledged' for r in scenario['input_trace']),'Uncertain controller input')
    return {'saved_earth':True,'escaped':True,'health':49,'message_pointer':runtime_base+0x4CAE5,
            'selection_pc':runtime_base+0x4C9DC,'final_frame':phases[-1]['stop_event']['frame']}


def summarize_dma(directory,context):
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
            old_start=context['original_address'];active=context['runtime_address'];size_of_image=context['size']
            domain=('active_image' if address<active+size_of_image and address+size>active else
                    'abandoned_image' if active!=old_start and address<old_start+size_of_image and address+size>old_start else 'fixed_or_other')
            counts[engine,domain]+=1
            if domain=='abandoned_image' and len(old)<32:old.append({'frame':frame['frame'],'engine':engine,'address':address,'width':size})
    return {'frames':[frame for frame in complete if frame['frame'] in selected],
            'discarded_partial_frames':[frame['frame'] for frame in checked['frames'] if frame.get('partial')],
            'validated_slots':checked['scanned_slots'],
            'counts':[{'engine':k[0],'domain':k[1],'transfers':v} for k,v in sorted(counts.items())],
            'first_abandoned_image_transfers':old,'scope':'Two sampled frames only, not whole-route DMA coverage.'}


def observe(out,payload,config,rom,binary,inspect_output=False,capture_pcm=False,stop_after=None,title_visits=0,pcm_stems=False,phase_locked_boot=False,*,scenario_path):
    from amiga_reversing.tools.direct_payload_adapter import DirectPayloadContract,build_boot_adf
    from amiga_reversing.tools.copperline_control import CopperlineProcess,MACHINE_PROFILES
    from amiga_reversing.tools.copperline_runtime import wait_for_marker,verify_handoff,release_handoff,wait_for_pc,run_scenario
    image,bootstrap=runtime_context(config)
    require(scenario_path is not None,'Explicit compiled normal-input route required')
    runtime_base=image['runtime_address'];load_base=bootstrap['load_address']
    old_start=image['original_address'];prefix_size=image['size'];old_end=old_start+prefix_size
    continuation=bootstrap['continuation_source_offset']
    contract=DirectPayloadContract('pandora-canonical-layout',TARGET,sha(payload),load_base,config['entrypoint'],{'a1':load_base},0x7FFF8,0x48414E44,
        reservations=tuple(tuple(span) for span in config.get('loader_shared_reservations',[])),
        seed_copies=tuple((seed['source_offset'],seed['runtime_address'],seed['size']) for seed in config.get('loader_seed_copies',[])))
    require(sha(payload)==config['payload_sha256'] and payload.stat().st_size==bootstrap['file_size'],'Canonical executable identity/extent differs')
    require(config['profile']==MACHINE_PROFILES['a500ecs_1m'],'Unsupported diagnostic machine profile')
    adf=out/'experiment.adf';write(out/'boot-build.json',build_boot_adf(contract,payload,adf))
    report={'normal_layout_export':True,'config':config,'payload_sha256':sha(payload),'adf_sha256':sha(adf),'rom_sha256':sha(rom),'emulator_sha256':sha(binary),'moved_pcs':[]}
    try:
        with CopperlineProcess(binary,rom=rom,floppy=adf,machine_profile='a500ecs_1m',
                audio_wav=out/'mixed-audio.wav' if capture_pcm and not pcm_stems else None,
                audio_stems=out/'audio-stems' if pcm_stems else None) as process:
            client=process.client;report['boot_marker']=wait_for_marker(client,0x7FFF8,contract.handoff_marker_value.to_bytes(4,'big'),90)
            require(report['boot_marker']['matched'],'Boot handoff missing')
            report['handoff']=verify_handoff(client,contract,payload)
            if phase_locked_boot:
                stop=client.run_until({'cck':500*71051},timeout=30)
                require(stop.get('reason')=='target' and client.read_memory(0x7FFF8,4)==b'HAND','Boot phase fixture did not remain in handoff')
                report['boot_phase_fixture']={'target_cck':500*71051,'stop':stop,'registers':client.registers(),'method':'Natural execution of generated HAND wait loop before host GO marker release; no gameplay state changed.'}
            release_handoff(client,contract)
            for offset in [0,continuation,0x48C]:
                address=load_base if offset==0 else runtime_base+offset
                stop=wait_for_pc(client,address,30);require(stop['status']=='hit','Runtime entry was not observed')
                require(client.read_memory(address,16)==payload.read_bytes()[offset:offset+16],'Canonical payload PC bytes differ')
                report['moved_pcs'].append({'source_offset':offset,'runtime_pc':client.registers()['pc'],'frame':stop['stop_event']['frame'],'stop_event':stop['stop_event']})
                print('MOVED_PC',hex(client.registers()['pc']),flush=True)
                if offset==continuation:
                    require(client.read_memory(runtime_base,prefix_size)==payload.read_bytes()[:prefix_size],'Native moved copy differs')
                    report['native_materialization']={'address':runtime_base,'size':prefix_size,'sha256':hashlib.sha256(payload.read_bytes()[:prefix_size]).hexdigest(),'full_prefix_verified':True}
            if runtime_base!=old_start:
                watch={'kind':'mmio','addr':old_start,'len':prefix_size,'access':'access'}
                ident=client.request('break.add',watch)['id']
                for address in [old_start,old_start+continuation]:client.add_breakpoint(address)
                report['guards']={'CPU_data':watch,'fallback_PC_sentinels':[old_start,old_start+continuation],'all_instruction_fetches_covered':False,'DMA_covered':False,'readback':client.request('break.list')}
                require(any(r.get('id')==ident and all(r.get(k)==v for k,v in watch.items()) for r in report['guards']['readback']['breaks']),'Old data guard readback differs')
            else:report['guards']={'original_control':True,'reason':'Original materialized range is intentionally live.'}
            report['resource_guards']=[]
            for region in config['layout_plan']['regions']:
                if(region.get('parent_region_id') or region.get('region_kind') not in ('workspace','display') or
                        region['runtime_address']==region['original_address']):continue
                watch={'kind':'mmio','addr':region['original_address'],'len':region['size'],'access':'access'}
                ident=client.request('break.add',watch)['id']
                readback=client.request('break.list')
                require(any(r.get('id')==ident and all(r.get(k)==v for k,v in watch.items()) for r in readback['breaks']),
                    'Abandoned resource CPU guard readback differs')
                report['resource_guards'].append({'region_id':region['region_id'],'CPU_data':watch,
                    'runtime_address':region['runtime_address'],'DMA_covered':False,'readback':readback})
            scenario=copy.deepcopy(load(scenario_path))
            report['input_scenario']={'sha256':sha(scenario_path),'phases':len(scenario['phases']),
                'scope':'Existing compiled normal-input route; runtime mapping is adapted below.'}
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
            view={'base_addr':runtime_base,'source_start':0,'source_end':prefix_size,'runtime_base':runtime_base,
                'execution_view_id':'normal-layout-'+config['layout_plan_sha256']}
            def moved(address):return runtime_base+address-old_start if old_start<=address<old_end else address
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
            media=[];active=None;dma=[];resource_dma=[];resource_snapshots=[]
            def finish_profile():
                nonlocal active
                if active is not None:
                    client.request('profile.stop')
                    record={'phase':active['name'],**summarize_dma(active['path'],image)}
                    if active.get('resource'):
                        record['directory']=active['path'].name;resource_dma.append(record)
                    else:dma.append(record)
                    active=None
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
                    if result['name'] in ('inventory_open','take_engineer_card_ready','take_sonicdriver_ready'):
                        cursor=next(r for r in config['layout_plan']['regions'] if r['region_id']=='pandora_cursor_sprites')
                        buffer=client.read_memory(cursor['runtime_address'],cursor['size'])
                        pointers=client.read_memory(0x3C08,8)
                        resource_snapshots.append({'phase':result['name'],'frame':event['frame'],'cck':event['cck'],
                            'pc':result['pc'],'registers':client.registers(),'buffer_address':cursor['runtime_address'],
                            'buffer_size':cursor['size'],'buffer_sha256':hashlib.sha256(buffer).hexdigest(),'buffer_hex':buffer.hex(),
                            'app_pointer_slot_address':0x3C08,'app_pointer_values':[int.from_bytes(pointers[i:i+4],'big') for i in (0,4)],
                            'scope':'Stopped phase snapshot, not a CPU memory-access event.'})
                        if result['name']=='inventory_open':
                            require(active is None,'Overlapping resource/output DMA profiles')
                            directory=out/'resource-dma-inventory_open'
                            client.request('profile.start',{'path':str(directory),'frames':3,'slots':True,'memory':False,'screenshots':'none','pc_samples':True})
                            active={'name':result['name'],'path':directory,'frame':event['frame'],'resource':True}
                return result
            report['scenario']=run_scenario(client,scenario,payload,trace_directory=out,phase_runner=progress)
            client.request('events.unsubscribe',{'events':['mmio']});client.events=queue
            report['output_observations']={'screenshots':media,'dma':dma}
            report['resource_observations']={'snapshots':resource_snapshots,'dma':resource_dma}
            report['registers_at_stop']=client.registers();pc=report['registers_at_stop']['pc'];report['pc_bytes_at_stop']=client.read_memory(pc,32).hex()
            report['stack_at_stop']=client.read_memory(report['registers_at_stop']['a7'],32).hex()
            report['status']='first_failure'
            if stop_after and all(p['status']=='hit' for p in report['scenario']['phases']):
                finish_profile();report['status']='bounded_output_prefix_complete';report['prefix_end']=stop_after
            if len(report['scenario']['phases'])==576 and all(p['status']=='hit' for p in report['scenario']['phases']):
                report['ending']=ending_outcome(report['scenario'],runtime_base,prefix_size)
                require(loss['events']>0 and loss['dropped_events']==loss['dropped_notifications']==0,'Incomplete event loss accounting')
                if inspect_output:
                    finish_profile();directory=out/'dma-ending'
                    client.request('profile.start',{'path':str(directory),'frames':3,'slots':True,'memory':False,'screenshots':'none','pc_samples':True})
                    stop=client.run_until({'frame':report['ending']['final_frame']+30},timeout=30)
                    require(stop.get('reason')=='target','Unexpected access during post-ending observation')
                    client.request('profile.stop');dma.append({'phase':'post_ending',**summarize_dma(directory,image)})
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


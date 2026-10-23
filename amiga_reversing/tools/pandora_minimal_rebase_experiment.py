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


def build(root,out):
    qualification=load(root/'runtime/observations/pandora-saved-earth-walkthrough.json')
    target=root/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
    original=target/'binary.bin';source=next(target.glob('*.s'))
    require(sha(original)==qualification['input_identities']['original_payload_sha256'],'Original binary differs')
    require(sha(source)==qualification['input_identities']['original_rendered_source_sha256'],'Original source differs')
    exact=load(root/'.runtime-state/pandora-app-usage-closure/exact.json')
    package=root/'bin/rebuilt'/TARGET/'source-packages'/exact['source_package_sha256']
    require(sha(package/source.name)==sha(source),'Source package differs')
    text=source.read_text();edits=[('    ORG $10000','    ORG $80000'),('\tlea.l fixed_base_image_copy_stub(pc),a0','\tbra.w initialize_runtime_workspace')]
    for before,after in edits:require(text.count(before)==1,'Experimental source anchor differs');text=text.replace(before,after)
    out.mkdir(parents=True,exist_ok=False);experimental=out/'experiment.s';experimental.write_text(text)
    assets={name:sha(package/name) for name in re_incbin(source.read_text())}
    payload=out/'experiment.bin';listing=out/'experiment.lst'
    command=[str(root/'tools/vasmm68k_mot.exe'),'-Fbin','-m68000','-no-opt','-I',str(root/'ext/amiga_includes/ndk_2.0/include'),'-I',str(package),'-L',str(listing),'-o',str(payload),str(experimental)]
    completed=subprocess.run(command,capture_output=True,text=True);(out/'assemble.log').write_text(completed.stdout+completed.stderr)
    require(completed.returncode==0,'Experimental assembly failed; inspect assemble.log')
    require(payload.stat().st_size==original.stat().st_size==376832,'Instruction/source extent changed')
    require(BASE+payload.stat().st_size==0xDC000<=0x100000 and BASE>=0x80000,'New image overlaps original/fixed low Chip RAM')
    from amiga_reversing.disasm.app_access_audit import decode_retained_instruction
    rows=load(root/'.runtime-state/pandora-app-access-audit/instructions.json');data=payload.read_bytes()
    for row in rows:
        pc=row['source_offset'];fact=decode_retained_instruction(data[pc:pc+row['size']],project_root=root)
        require(fact['size']==row['size'],'Canonical observation offset changed')
    config={'experimental_only':True,'general_native_plan_admission':False,'original_source_sha256':sha(source),'original_binary_sha256':sha(original),
        'assembly_base':BASE,'load_address':BASE,'entrypoint':BASE,'full_image_interval':[BASE,BASE+len(data)],'old_materialized_interval':[0x10000,0x65370],
        'profile':{'model':'A500','chipset':'ECS','video':'PAL','cpu':'68000','chip':'1M','slow':'512K','fast':'0'},
        'original_profile_unchanged':True,'original_profile_equivalence_claimed':False,
        'source_edits':[{'before':a,'after':b} for a,b in edits],'assets_sha256':assets,'payload_sha256':sha(payload),'source_sha256':sha(experimental),
        'native_instruction_extents_checked':len(rows),'changed_instruction_extents':0,'tool_sha256':sha(Path(__file__))}
    write(out/'experiment-config.json',config)
    return payload,config


def re_incbin(text):
    import re
    return sorted(set(re.findall(r'^\s*INCBIN\s+"([^"]+)"',text,re.MULTILINE|re.IGNORECASE)))


def observe(root,out,payload,config,rom,binary):
    from amiga_reversing.tools.direct_payload_adapter import DirectPayloadContract,build_boot_adf
    from amiga_reversing.tools.copperline_control import CopperlineProcess
    from amiga_reversing.tools.copperline_runtime import wait_for_marker,verify_handoff,release_handoff,wait_for_pc,run_scenario
    contract=DirectPayloadContract('pandora-explicit-rebase','pandora-experimental',sha(payload),BASE,BASE,{'a1':BASE},0x7FFF8,0x48414E44)
    adf=out/'experiment.adf';write(out/'boot-build.json',build_boot_adf(contract,payload,adf))
    old_popen=subprocess.Popen
    def launch(command,*args,**kwargs):
        command=list(command)
        if Path(command[0]).name=='copperline':
            for flag,value in [('--model','A500'),('--chipset','ECS'),('--chip','1M')]:command[command.index(flag)+1]=value
        return old_popen(command,*args,**kwargs)
    report={'experimental_only':True,'config':config,'payload_sha256':sha(payload),'adf_sha256':sha(adf),'rom_sha256':sha(rom),'emulator_sha256':sha(binary),'moved_pcs':[]}
    try:
        with patch('amiga_reversing.tools.copperline_control.subprocess.Popen',launch):
            with CopperlineProcess(binary,rom=rom,floppy=adf) as process:
                client=process.client;report['boot_marker']=wait_for_marker(client,0x7FFF8,contract.handoff_marker_value.to_bytes(4,'big'),90)
                require(report['boot_marker']['matched'],'Boot handoff missing')
                report['handoff']=verify_handoff(client,contract,payload);release_handoff(client,contract)
                for offset in [0,0x46A,0x48C]:
                    stop=wait_for_pc(client,BASE+offset,30);require(stop['status']=='hit','Moved entry was not observed')
                    require(client.read_memory(BASE+offset,16)==payload.read_bytes()[offset:offset+16],'Experimental PC bytes differ')
                    report['moved_pcs'].append({'source_offset':offset,'runtime_pc':client.registers()['pc'],'frame':stop['stop_event']['frame']})
                    print('MOVED_PC',hex(client.registers()['pc']),flush=True)
                watch={'kind':'mmio','addr':0x10000,'len':0x55370,'access':'access'}
                ident=client.request('break.add',watch)['id']
                for address in [0x10000,0x1046A]:client.add_breakpoint(address)
                report['guards']={'CPU_data':watch,'fallback_PC_sentinels':[0x10000,0x1046A],'all_instruction_fetches_covered':False,'DMA_covered':False,'readback':client.request('break.list')}
                require(any(r.get('id')==ident and all(r.get(k)==v for k,v in watch.items()) for r in report['guards']['readback']['breaks']),'Old data guard readback differs')
                scenario=copy.deepcopy(load(root/'.runtime-state/pandora-player/finale-cold-b/compiled.json'))
                view={'base_addr':BASE,'source_start':0,'source_end':0x55370,'runtime_base':BASE,'execution_view_id':'explicit-experiment-not-native-proof'}
                def moved(address):return BASE+address-ORIGINAL if ORIGINAL<=address<0x65370 else address
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
                    phase.update(breakpoint_address=BASE+phase['source_offset'],runtime_view=view)
                    for read in phase.get('capture',{}).get('memory_reads',[]):update_read(read)
                    if 'until_memory' in phase:update_read(phase['until_memory'])
                scenario['symbols']['runtime_view']=view
                for function in scenario['symbols'].get('functions',[]):function.update(runtime_start=BASE+function['source_start'],runtime_end=BASE+function['source_end'])
                write(out/'runtime-scenario.json',scenario)
                report['scenario']=run_scenario(client,scenario,payload,trace_directory=out)
                report['registers_at_stop']=client.registers();pc=report['registers_at_stop']['pc'];report['pc_bytes_at_stop']=client.read_memory(pc,32).hex()
                report['stack_at_stop']=client.read_memory(report['registers_at_stop']['a7'],32).hex()
                report['status']='route_reached_final_phase_needs_outcome_review' if all(p['status']=='hit' for p in report['scenario']['phases']) else 'first_failure'
    except BaseException as exc:
        report['status']='experiment_error';report['error']={'type':type(exc).__name__,'message':str(exc)};raise
    finally:write(out/'report.json',report);print('RESULT',report['status'],flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qualified-checkout',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--run',action='store_true');p.add_argument('--rom',type=Path);p.add_argument('--copperline',type=Path);args=p.parse_args();root=args.qualified_checkout.resolve()
    require(not args.run or (args.rom and args.copperline),'Run requires explicit legal ROM and Copperline paths')
    sys.path.insert(0,str(root));import amiga_reversing.tools.copperline_runtime as runtime
    require(Path(runtime.__file__).resolve().is_relative_to(root),'Invoke this experiment by file pathname to use the explicit qualified runtime')
    out=args.output.resolve();payload,config=build(root,out)
    if args.run:observe(root,out,payload,config,args.rom.resolve(),args.copperline.resolve())

if __name__=='__main__':main()

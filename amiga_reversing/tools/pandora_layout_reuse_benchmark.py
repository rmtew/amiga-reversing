import hashlib,json,resource,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from amiga_reversing.disasm import source_export,layout_export_cache
from amiga_reversing.disasm.source_package import materialize_source_package
from amiga_reversing.disasm.c_backend import assemble_platform_source_path_with_c_backend
T='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
folder=root/'.runtime-state/layout-m0/reuse-benchmark';folder.mkdir(exist_ok=False)
expected={'pandora_original_ecs1m':'70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f','pandora_image_80000_ecs1m':'5a6f969515baea1806627ddfcae75d2fd35ff002f738ddaae1c2c0b28af4bf62','pandora_cursor_e0000_ecs1m':'36c1a03579fcc6a9f9f200313d488fed280e3e8848c8216d66a8ce32448488b0'}
count=0;original_builder=source_export.build_listing_artifact_profile_from_binary_source
# Counter only; the unchanged native builder receives identical arguments.
def counted(*args,**kwargs):
 global count
 count+=1
 return original_builder(*args,**kwargs)
source_export.build_listing_artifact_profile_from_binary_source=counted
rows=[];payloads={}
steps=[('cold-image','pandora_image_80000_ecs1m',True),('warm-cursor-1','pandora_cursor_e0000_ecs1m',True),('warm-cursor-2','pandora_cursor_e0000_ecs1m',False),('warm-image-return','pandora_image_80000_ecs1m',False),('clean-cursor','pandora_cursor_e0000_ecs1m',True),('cold-original','pandora_original_ecs1m',True)]
for name,layout,assemble in steps:
 if name=='clean-cursor':layout_export_cache._CACHE.reset()
 print('BEGIN',name,flush=True);start=time.perf_counter();cpu=time.process_time();before=count
 payload=source_export.source_export_payload(T,project_root=root,binary_assets=True,layout_id=layout)
 elapsed=time.perf_counter()-start;cpu_elapsed=time.process_time()-cpu
 case=folder/name;case.mkdir();(case/'export.json').write_text(json.dumps(payload,indent=2)+'\n')
 if payload.get('status')!='ok':raise RuntimeError(name+' '+str(payload.get('reason',payload)))
 row=dict(name=name,layout_id=layout,export_wall_seconds=elapsed,export_CPU_seconds=cpu_elapsed,native_analysis_invocations=count-before,max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=hashlib.sha256(payload['source_text'].encode()).hexdigest(),package_sha256=payload['package']['sha256'],layout_plan_sha256=payload['layout_plan_sha256'],projection=payload['listing_profile'].get('layout_projection'))
 old=json.loads((root/'.runtime-state/layout-m0/seeded-exports'/layout/'export.json').read_text())
 assert payload['source_text']==old['source_text'] and payload['package']==old['package'],'Retained clean output differs: '+name
 row['retained_clean_source_and_package_exact']=True
 if assemble:
  source=materialize_source_package(payload['package'],case/'package')
  data,profile=assemble_platform_source_path_with_c_backend('amiga-raw',source,include_dir=source.parent,target_cpu='68000',project_root=root)
  (case/'C.bin').write_bytes(data);binary=case/'vasm.bin'
  result=subprocess.run([str(root/'tools/vasmm68k_mot.exe'),'-Fbin','-m68000','-no-opt','-I',str(source.parent),'-o',str(binary),str(source)],capture_output=True,text=True)
  (case/'assembly.log').write_text(result.stdout+result.stderr)
  assert result.returncode==0 and binary.read_bytes()==data and hashlib.sha256(data).hexdigest()==expected[layout],'Assembly/payload mismatch: '+name
  row.update(C_equals_vasm=True,payload_sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
 rows.append(row);payloads[name]=payload
 (folder/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',json.dumps(row),flush=True)
assert payloads['warm-cursor-1']['source_text']==payloads['warm-cursor-2']['source_text']==payloads['clean-cursor']['source_text']
assert payloads['warm-cursor-1']['package']==payloads['warm-cursor-2']['package']==payloads['clean-cursor']['package']
assert [r['native_analysis_invocations'] for r in rows]==[1,0,0,0,1,1]
result=dict(status='pass',rows=rows,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native_analysis_invocations=count,normal_profiles=3,existing_capture_payloads_unchanged=True,limits=['Sequential same-process cold/warm cases, not a universal speedup claim.','CPU timings cover the calling process; vasm verification time is outside export timing.','max_RSS is cumulative high-water; projection owned_bytes excludes package/JSON buffers and baseline ownership.','Code/bootstrap or source-mapped placement changes conservatively rebuild. Structure-macro exports retain the clean path.','Existing controller/pixel/PCM captures are reused only because executable bytes, native plans and machine/input identities are unchanged.'])
(folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');layout_export_cache._CACHE.reset();print('RESULT pass',flush=True)

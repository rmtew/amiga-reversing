"""Qualify the bounded body-background AllocMem profile using normal inputs.

Run in a fresh interpreter. Native planning owns fixups and returned placement;
this client owns only the emulator lifetime and the existing walkthrough recipe.
Fixed exports are preserved. Successful OS return is a separate lifecycle gate.
"""
from __future__ import annotations

import sys
_PRELOADED = any('amiga_reversing.tools.'+name in sys.modules for name in
    ('runtime_allocation','direct_payload_adapter','copperline_runtime','pandora_layout_runtime'))

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import threading

from amiga_reversing.disasm.behaviour_validation import LoadedSource
from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.restoration import revisions
from amiga_reversing.tools import runtime_allocation, direct_payload_adapter, copperline_runtime, pandora_layout_runtime
from amiga_reversing.tools.pandora_layout_walkthrough import TARGET,build_from_export

_SOURCES=[LoadedSource(module.__file__) for module in
    (runtime_allocation,direct_payload_adapter,copperline_runtime,pandora_layout_runtime)]
_SOURCES += [LoadedSource(__file__)] + [LoadedSource(PROJECT_ROOT/'tools'/name) for name in
    ('amiga_direct_payload_bootblock.s','amiga_runtime_allocation.i','amiga_runtime_allocation_unwind.i')]


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-json',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scenario',type=Path,required=True)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--copperline',type=Path,required=True)
    parser.add_argument('--mode',choices=('prefix','title','full','unheld','fault_before','fault_after','qualify'),default='prefix')
    parser.add_argument('--scratch-extra',type=int,choices=(0,64),action='append')
    parser.add_argument('--jobs',type=int,choices=(1,2),default=1)
    args=parser.parse_args()
    if _PRELOADED:raise ValueError('Fresh CLI interpreter required; cached runtime modules are not admitted')
    def identities():return {str(source.path.relative_to(PROJECT_ROOT)):source.require_current() for source in _SOURCES}
    source_ids=identities();before=revisions(TARGET)
    payload=json.loads(args.export_json.read_text())
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    binary,config=build_from_export(PROJECT_ROOT,output/'static-build',payload)
    print('BEGIN_NATIVE_CONTEXT',flush=True)
    _,_,artifact=build_project_listing_artifact_profile(TARGET)
    results=[];lock=threading.Lock()
    try:
        candidate=artifact.runtime_allocation_plan('pandora_ui_snapshot_body',payload['layout_id'])
        backend=artifact.loaded_backend_identity()
        (output/'native-candidate.json').write_text(json.dumps(dict(plan=candidate,
            subject=before,backend=backend,source_identities=source_ids),indent=2)+'\n')
        if candidate['status']!='bounded_allocation_candidate':
            raise ValueError('Native allocation refused: '+str(candidate.get('reason')))
        def validate(actual):
            with lock:
                identities()
                if revisions(TARGET)!=before or artifact.loaded_backend_identity()!=backend:
                    raise ValueError('Allocation context changed; restart required')
                return artifact.runtime_allocation_plan('pandora_ui_snapshot_body',payload['layout_id'],actual)
        def run(case):
            mode,extra=case;out=output/(mode+'-'+str(extra));out.mkdir(exist_ok=False)
            current={**config,'runtime_allocation':runtime_allocation.capsule(candidate,scratch_extra=extra,
                fault={'fault_before':'before_owner','fault_after':'after_owner'}.get(mode))}
            shutil.copyfile(binary,out/'experiment.bin')
            (out/'experiment-config.json').write_text(json.dumps(current,indent=2)+'\n')
            print('RUN',mode,extra,flush=True)
            result=pandora_layout_runtime.observe(out,out/'experiment.bin',current,args.rom.resolve(),args.copperline.resolve(),
                True,mode=='full','take_sonicdriver' if mode=='prefix' else 'title_menu_loop' if mode=='title' else None,
                180 if mode=='title' else 0,False,mode!='unheld',scenario_path=args.scenario.resolve(),allocation_validator=validate)
            identities()
            expected=('allocation_failure_unwound' if mode.startswith('fault_') else
                'bounded_output_prefix_complete' if mode in ('prefix','title') else 'saved_earth_and_escaped_relocated_cold_boot')
            if result['status']!=expected:raise ValueError('Run did not meet its explicit objective: '+result['status'])
            record=dict(case=mode,scratch_extra=extra,status=result['status'],
                report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),
                ending=result.get('ending'),lease=result.get('runtime_allocation',{}).get('lease'))
            print('DONE',json.dumps(record),flush=True)
            return record
        extras=args.scratch_extra or [0,64]
        if len(set(extras))!=len(extras):raise ValueError('Duplicate allocation profile')
        def batch(cases):
            with ThreadPoolExecutor(max_workers=args.jobs) as pool:
                results.extend(pool.map(run,cases))
        if args.mode=='qualify':
            batch([('fault_before',0),('fault_after',0)])
            batch([('full',extra) for extra in extras])
            batch([('title',extra) for extra in extras])
            batch([('unheld',extras[0])])
        else:batch([(args.mode,extra) for extra in extras])
        validate(None)
        (output/'summary.json').write_text(json.dumps(dict(status='declared_route_objectives_met_output_comparison_separate',
            results=results,subject=before,native_backend=backend,source_identities=source_ids,
            scope='One bounded Chip allocation owner; no all-path alias proof or successful OS return claim.'),indent=2)+'\n')
    finally:artifact.close()
    return 0


if __name__=='__main__':raise SystemExit(main())

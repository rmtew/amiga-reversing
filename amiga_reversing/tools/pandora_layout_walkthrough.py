"""Use normal canonical layout exports with Pandora's qualified input route.

This adapter consumes a native plan. It neither plans placements nor repairs
addresses. Runtime qualification remains distinct from successful assembly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def export_context(payload, original, metadata_hash):
    """Check consumed identities; native services remain the layout authority."""
    require(payload.get('status') == 'ok' and payload.get('layout_status') == 'source_only_unqualified'
            and payload.get('layout_runtime_qualified') is False and payload.get('non_verification') is True,
            'A normal, explicitly unqualified layout export is required')
    require(payload.get('target') == TARGET and payload.get('metadata_hash') == metadata_hash,
            'Export belongs to stale or different canonical metadata')
    require(payload.get('target_identity_sha256') == digest(original), 'Export input identity differs')
    plan = payload.get('layout_plan')
    require(isinstance(plan, dict), 'Native layout plan is missing')
    require(digest(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()) == payload.get('layout_plan_sha256'),
            'Native layout plan identity differs')
    require(plan.get('layout_id') == payload.get('layout_id') and plan.get('status') == 'placement_valid',
            'Native placement is refused or selects another layout')
    require(plan.get('chip_bytes') == 0x100000, 'Only the qualified ECS/1MiB Chip diagnostic profile is supported')
    bootstrap = plan.get('bootstrap')
    require(isinstance(bootstrap, dict) and bootstrap.get('kind') == 'retained_prefix_copy',
            'Retained native initialization contract is required')
    require(bootstrap.get('variant') in ('native', 'forward_disjoint'), 'Unsupported bootstrap runtime variant')
    require(bootstrap.get('input_sha256') == digest(original) and bootstrap.get('file_size') == len(original),
            'Bootstrap input identity or complete staging size differs')
    image = next((r for r in plan.get('regions', []) if r.get('region_id') == bootstrap.get('image_region_id')), None)
    require(image and image.get('region_kind') == 'image' and image.get('size') == bootstrap.get('copied_source_end'),
            'Native copied image contract differs')
    # Deliberately consume the placement result rather than recomputing a
    # competing Python placement/alias/alignment model.
    return plan, bootstrap, image


def seed_copies(plan, original, assembled=None):
    """Consume native initializer coordinates; never guess seed or pointer bytes."""
    from amiga_reversing.tools.direct_payload_adapter import normalize_seed_copies
    copies=[]
    for region in plan['regions']:
        seed=region.get('loader_seed')
        if seed is None:continue
        require(seed.get('phase')=='before_payload_entry','Unsupported seed phase')
        source,size=seed['source_offset'],seed['size']
        require(len(original[source:source+size])==size,'Seed source is outside original input')
        if assembled is not None:
            require(assembled[source:source+size]==original[source:source+size],
                    'Seed source was rewritten; original-byte companion initialization is unsupported')
        copies.append((source,seed['runtime_address'],size))
    return normalize_seed_copies(tuple(copies),payload_size=len(original),load_address=plan['bootstrap']['load_address'])


def loader_family_context(payload, original, assembled, family):
    """Use one explicit pre-entry seed program in every comparison control."""
    from amiga_reversing.tools.direct_payload_adapter import normalize_seed_copies, seed_reservation_spans, rounded_reservation_span
    plan=payload['layout_plan']
    plans={plan['layout_id']:(payload['layout_plan_sha256'],plan)}
    for member in family:
        member_plan,_,_=export_context(member,original,payload['metadata_hash'])
        existing=plans.get(member_plan['layout_id'])
        require(existing is None or existing[0]==member['layout_plan_sha256'],'Conflicting loader-family layout identities')
        plans[member_plan['layout_id']]=(member['layout_plan_sha256'],member_plan)
    selected=seed_copies(plan,original,assembled)
    program=normalize_seed_copies(tuple(copy for _,member in plans.values()
        for copy in seed_copies(member,original,assembled)),
        payload_size=len(original),load_address=plan['bootstrap']['load_address'])
    # Own independently moved CPU workspace backing before I/O. Consume the
    # native extents; this does not choose placements or initialize unknown RAM.
    workspace_spans={rounded_reservation_span(r['runtime_address'],r['size'])
        for _,member in plans.values() for r in member['regions']
        if not r.get('parent_region_id') and r.get('region_kind')=='workspace'
        and r['runtime_address']!=r['original_address']}
    reservations=tuple(sorted(set(seed_reservation_spans(program))|workspace_spans))
    identities=[dict(layout_id=k,layout_plan_sha256=v[0]) for k,v in sorted(plans.items())]
    return selected,program,reservations,identities


def build_from_export(root, out, payload, *, family=()):
    from amiga_reversing.disasm.binary_source import read_binary_source_bytes
    from amiga_reversing.disasm.c_backend import assemble_platform_source_path_with_c_backend
    from amiga_reversing.disasm.effective_metadata import effective_metadata_hash
    from amiga_reversing.disasm.project_paths import resolve_project_paths
    from amiga_reversing.disasm.source_package import materialize_source_package
    paths = resolve_project_paths(TARGET, project_root=root)
    original = read_binary_source_bytes(paths.binary_source)
    plan, bootstrap, image = export_context(payload, original, effective_metadata_hash(paths.target_dir))
    require(not out.exists(), 'Output directory must be new; existing evidence is never overwritten')
    out.mkdir(parents=True)
    source = materialize_source_package(payload['package'], out/'package')
    backend = root/'src/build/platform_file_lib.dll'
    backend_hash = digest(backend.read_bytes())
    data, profile = assemble_platform_source_path_with_c_backend('amiga-raw', source,
        include_dir=source.parent, target_cpu='68000', project_root=root)
    require(digest(backend.read_bytes()) == backend_hash, 'Assembly backend changed during execution; restart required')
    binary = out/'experiment.bin'
    completed = subprocess.run([str(root/'tools/vasmm68k_mot.exe'), '-Fbin', '-m68000', '-no-opt',
        '-I', str(source.parent), '-o', str(binary), str(source)], capture_output=True, text=True)
    (out/'assemble.log').write_text(completed.stdout+completed.stderr)
    require(completed.returncode == 0 and binary.read_bytes() == data, 'C and vasm assembly failed or disagreed')
    require(len(data) == bootstrap['file_size'], 'Complete file extent changed')
    assets = {}
    for item in payload['package']['manifest']['files']:
        if item.get('kind') != 'asset':
            continue
        start, size = item['source_offset'], item['size']
        require(item['source_section_index'] == 0 and original[start:start+size] == data[start:start+size],
                'Raw asset changed outside explicit typed reference fields: '+item['path'])
        require(digest(data[start:start+size]) == item['sha256'], 'Asset identity differs')
        assets[item['path']] = item['sha256']
    original_control = all(r['runtime_address'] == r['original_address'] for r in plan['regions'])
    require(not original_control or data == original, 'Original layout is not byte exact')
    own_seeds,seed_program,shared_reservations,family_identities=loader_family_context(payload,original,data,family)
    config = dict(normal_layout_export=True, layout_id=plan['layout_id'], layout_plan=plan,
        layout_plan_sha256=payload['layout_plan_sha256'], source_package_sha256=payload['package']['sha256'],
        original_binary_sha256=digest(original), original_source_sha256=digest(source.read_bytes()),
        payload_sha256=digest(data), source_sha256=digest(source.read_bytes()),
        assembly_backend_file_sha256=backend_hash, assembly_profile=profile,
        backend_identity_scope='File snapshot unchanged across assembly; runtime evidence binds the resulting executable bytes separately.',
        original_control=original_control, matched_startup=bootstrap['variant'] == 'forward_disjoint',
        assembly_base=image['runtime_address'], load_address=bootstrap['load_address'], entrypoint=bootstrap['load_address'],
        full_image_interval=[bootstrap['load_address'], bootstrap['load_address']+bootstrap['file_size']],
        old_materialized_interval=[image['original_address'], image['original_address']+image['size']],
        copied_prefix_bytes=bootstrap['copied_source_end'], assets_sha256=assets,
        loader_selected_seed_copies=[dict(source_offset=s,runtime_address=a,size=n) for s,a,n in own_seeds],
        loader_seed_copies=[dict(source_offset=s,runtime_address=a,size=n) for s,a,n in seed_program],
        loader_family_mode='common_guest_seed_program',
        loader_shared_reservations=shared_reservations,
        loader_family=family_identities,
        seed_initialization_scope='Guest boot-shim copies from original staged bytes before HAND; no host seed/gameplay-memory writes. Existing host GO marker release is retained.',
        profile=dict(model='A500', chipset='ECS', video='PAL', cpu='68000', chip='1M', slow='512K', fast='0'),
        runtime_qualified=False)
    (out/'experiment-config.json').write_text(json.dumps(config, indent=2)+'\n')
    return binary, config


def main():
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT
    from amiga_reversing.disasm.source_export import source_export_payload
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layout', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--export-json', type=Path, help='Reuse an identity-checked normal export, not a patched payload')
    parser.add_argument('--family-export-json',type=Path,action='append',default=[],
        help='Explicit paired-loader family; both runs reserve the union of native seed destinations before I/O')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--scenario', type=Path, help='Explicit existing qualified compiled normal-input route')
    parser.add_argument('--rom', type=Path)
    parser.add_argument('--copperline', type=Path)
    parser.add_argument('--capture-pcm', action='store_true')
    parser.add_argument('--phase-locked-boot', action='store_true')
    parser.add_argument('--stop-after')
    parser.add_argument('--title-frames', type=int, default=0)
    args = parser.parse_args()
    require(not args.run or (args.scenario and args.rom and args.copperline), 'Run requires explicit route, ROM and emulator')
    payload = (json.loads(args.export_json.read_text()) if args.export_json else
               source_export_payload(TARGET, project_root=PROJECT_ROOT, binary_assets=True, layout_id=args.layout))
    require(payload.get('layout_id') == args.layout, 'Requested layout differs from export')
    binary, config = build_from_export(PROJECT_ROOT, args.output.resolve(), payload,
        family=[json.loads(path.read_text()) for path in args.family_export_json])
    if args.run:
        from amiga_reversing.tools.pandora_layout_runtime import observe
        observe(args.output.resolve(),binary,config,args.rom.resolve(),args.copperline.resolve(),
            True,args.capture_pcm,args.stop_after,args.title_frames,False,args.phase_locked_boot,
            scenario_path=args.scenario.resolve())
    print(json.dumps(dict(layout_id=args.layout, payload_sha256=config['payload_sha256'],runtime_qualified=False)))


if __name__ == '__main__':
    main()

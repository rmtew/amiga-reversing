"""Complete native-source package for the explicitly supported Pandora DOS profile.

Placement and reference ownership remain native facts. Authored runtime templates
are selected here and receive only native admitted coordinates/constraints. No
rendered game text or address-looking words are rewritten.
"""
import hashlib
import json
from pathlib import Path
import tempfile
from .behaviour_validation import LoadedSource
from .source_package import collect_package_includes,extend_source_package,materialize_source_package
from .c_backend import assemble_platform_source_path_with_c_backend
from amiga_reversing.tools.pandora_OS_application import OWNERS,IMAGE_OWNER,HIGH_MASK_OWNER,application_owners,application_sources,LOADED_SOURCE as APP_SOURCE

LOADED_SOURCE=LoadedSource(__file__)
TARGET='amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'


def required(metadata_path,layout_id):
    if metadata_path is None or layout_id is None:return False
    metadata=json.loads(metadata_path.read_text())
    layout=next((v for v in metadata.get('memory_layouts',[]) if v['layout_id']==layout_id),{})
    boot=next((v for v in metadata.get('bootstrap_contracts',[]) if v['contract_id']==layout.get('bootstrap_contract_id')),{})
    return 'exit_dispatch_call_source_offset' in boot


def native_contract(artifact,target,layout_id,*,allocate_image=True,allocate_high_masks=None):
    LOADED_SOURCE.require_current();APP_SOURCE.require_current()
    if target!=TARGET:raise ValueError('No hosted application template is registered for this target')
    if allocate_high_masks is None:allocate_high_masks=allocate_image
    owners=(*OWNERS,IMAGE_OWNER) if allocate_image else OWNERS
    if allocate_high_masks:
        if not allocate_image:raise ValueError('High-mask profile requires the admitted image owner')
        owners=(*owners,HIGH_MASK_OWNER)
    plans={n:artifact.runtime_allocation_plan(n,layout_id) for n in owners}
    if any(p.get('status')!='bounded_allocation_candidate' for p in plans.values()):
        raise ValueError('Hosted application has a refused native owner')
    batch=artifact.runtime_allocation_batch_plan(layout_id,dict(schema_version=1,layout_id=layout_id,
        chip_bytes=0x100000,placements=[dict(region_id=n,runtime_address=p['staged_address']) for n,p in plans.items()]))
    if batch.get('status')!='actual_placements_valid' or batch.get('uncovered_runtime_extents')!=[]:
        raise ValueError('Hosted application has incomplete native backing')
    return dict(backend=artifact.loaded_backend_identity(),candidates=plans,template_geometry=batch)


def attach(payload,contract,project_root):
    LOADED_SOURCE.require_current();APP_SOURCE.require_current()
    # Use the normal game's identical package and native assembler, not a saved
    # binary or a second interpretation of its pointer/reference facts.
    with tempfile.TemporaryDirectory(prefix='pandora-application-') as temporary:
        source=materialize_source_package(payload['package'],Path(temporary)/'game')
        data,_=assemble_platform_source_path_with_c_backend('amiga-raw',source,
            include_dir=source.parent,target_cpu='68000',project_root=project_root)
    expected=hashlib.sha256(data).hexdigest()
    files,_=application_sources(data,contract,game=True,project_root=project_root,
        layout_id=payload['layout_id'],expected_payload_sha256=expected)
    main='amiga_pandora_OS.s';include_root=project_root/'ext/amiga_includes/ndk_2.0/include'
    provided={name:content for name,content in files.items() if name!=main}
    records=collect_package_includes(files[main].decode(),include_root,provided=provided)
    for record in records:
        if record['path'] in files:
            record.update(kind='runtime_bindings' if record['path'].startswith('pandora_OS_') else 'application_source',
                provenance='native-admitted-fields' if record['path'].startswith('pandora_OS_') else 'authored-framework-template')
    def add(name,data,kind,provenance):
        records.append(dict(path=name,data_hex=data.hex(),size=len(data),kind=kind,provenance=provenance))
    add(main,files[main],'application_source','authored-framework-template')
    add('build.py',(project_root/'tools/amiga_pandora_package_build.py').read_bytes(),'build_source','authored-framework-template')
    add('native-runtime-bindings.json',(json.dumps(contract,sort_keys=True,indent=2)+'\n').encode(),'runtime_bindings','native-admitted-fields')
    owners=application_owners(contract)
    profile='pandora-dos-allocated-image-v1' if IMAGE_OWNER in owners else 'pandora-dos-owned-prefix-v1'
    fixed=contract['template_geometry']['fixed_leases_requiring_OS_acquisition']
    application=dict(schema='native-hosted-application-source/v1',profile=profile,
        entry_source=main,game_source=payload['filename'],expected_payload_sha256=expected,
        expected_payload_bytes=len(data),native_layout_id=payload['layout_id'],
        native_layout_plan_sha256=payload['layout_plan_sha256'],
        provenance=dict(game='canonical native Pandora rendering',runtime='authored framework templates',bindings='native allocation plans and declared bootstrap import'),
        dynamic_owners=list(owners),fixed_lease_intents=fixed,
        status='source_only_unqualified',requires='vasm plus Python standard library to build; declared ECS/1MiB Chip/512KiB Slow host to run')
    fixed_listing=', '.join(f"`${r['address']:X}..${r['address']+r['size']:X}` ({r['size']:,} bytes)" for r in fixed)
    readme=f'''# Pandora restored DOS application source

Game source: `{payload['filename']}` is the canonical native renderer output.
Runtime source: `{main}` and its `amiga_pandora_OS_*.i` includes are authored
framework templates. `pandora_OS_*.i` and `native-runtime-bindings.json` are
programmatic output of native admitted fields, owners and bootstrap contracts.
No worker edits the rendered game source. Both parts belong to this package.

Build outside the repository, with Python standard library and vasm:

    python build.py --vasm /path/to/vasmm68k_mot

This assembles game source into `bin/Pandora.payload`, checks the native expected
SHA256 `{expected}`, then assembles `bin/Pandora` as a normal CODE HUNK. No ROM,
emulator, native backend or filesystem-image tool is needed to build these DOS
files. On the declared host, copy both together, cd into that directory and run
Pandora. The package has no proprietary executable/ROM or raw captures; the
canonical game's source-selected assets are included for your local build.

Original byte-exact output remains a separate normal export; this restored
payload is deliberately different. Original input SHA256:
`{payload['target_identity_sha256']}`. Startup retains the owned helper and
initialization. The loader owns {len(owners)} actual Exec AllocMem regions
({', '.join(owners)}), validates
all typed fields before one-time application, binds the explicit first-init/
restart dispatch and enters the real game. F7 or the normal ending restart
returns to DOS after DMA/blitter quiescence, view/vector/IRQ state restoration,
audio release and exact owned frees. Startup failures unwind and return20.

{len(fixed)} fixed AllocAbs claims remain: {fixed_listing}.
Their combined {sum(r['size'] for r in fixed):,} bytes are restrictions, not fully
allocator-selected loading. The retained input still contains a duplicated image
prefix; do not free it merely because the copy completed. Requires
a declared 68000/PAL/ECS host with1MiB Chip plus512KiB Slow; no RTG/multitasking,
arbitrary CPU fault recovery or exact original startup-clock claim. Export and
assembly are not runtime qualification; see Proposal046 and the hosted cold-run
receipts. Do not manually patch addresses: revise canonical facts and re-export
so the native coordinates, width/alias constraints and tables stay consistent.
'''
    add('README-application.md',readme.encode(),'documentation','application-export-service')
    payload['package']=extend_source_package(payload['package'],records,application=application)
    payload['application']=application
    LOADED_SOURCE.require_current();APP_SOURCE.require_current()
    return payload


def verify(target, payload, project_root):
    """Build the complete current export, without mistaking it for the original."""
    import subprocess
    import sys
    from .source_export import source_export_payload
    from .source_package import validate_source_package
    from .oracle_compatibility import _resolve_capability_with_workflow, _selected_capability_path
    LOADED_SOURCE.require_current(); APP_SOURCE.require_current()
    package = payload['package']
    validate_source_package(package)
    # An internally consistent caller-supplied ZIP is not a native proof.
    current = source_export_payload(target, project_root=project_root,
        binary_assets=True, layout_id=payload['layout_id'],
        minimum_asset_size=package['manifest']['policy']['minimum_asset_size'],
        structure_macros='structure_macros' in payload)
    if current.get('status') == 'refused' or current['package']['sha256'] != package['sha256']:
        raise ValueError('Stale hosted source package; re-export current canonical facts and templates')
    capability, _ = _resolve_capability_with_workflow(target, 'assemble_vasm_source', project_root=project_root)
    vasm = _selected_capability_path(capability, 'functional_resolved_path')
    if vasm is None:
        return dict(package_sha256=package['sha256'], exact=False, build_verified=False,
            status='missing_prerequisite', message='No configured vasm assembler', runtime_verified=False)
    with tempfile.TemporaryDirectory(prefix='verify-hosted-source-') as temporary:
        source = materialize_source_package(package, Path(temporary)/'package')
        result = subprocess.run([sys.executable, str(source.parent/'build.py'), '--vasm', str(vasm)],
            cwd=source.parent, capture_output=True, text=True)
        if result.returncode:
            return dict(package_sha256=package['sha256'], exact=False, build_verified=False,
                status='mismatch', stdout=result.stdout, stderr=result.stderr, runtime_verified=False)
        receipt = json.loads((source.parent/'bin/build-receipt.json').read_text())
    LOADED_SOURCE.require_current(); APP_SOURCE.require_current()
    return dict(package_sha256=package['sha256'], exact=receipt['original_binary_exact'],
        build_verified=True, status='build_verified', runtime_verified=False, build=receipt)

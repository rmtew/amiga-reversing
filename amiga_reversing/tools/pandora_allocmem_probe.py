"""Measure guest Exec allocation/free before designing Pandora's M5 loader.

This diagnostic never starts Pandora, patches a game pointer or certifies an
allocation as a legal game placement. The caller supplies a normal export; its
native owner and input extents determine the request/backing. Raw media stay in
the requested local output directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from amiga_reversing.disasm.binary_source import read_binary_source_bytes
from amiga_reversing.disasm.effective_metadata import effective_metadata_text
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.tools.copperline_control import CopperlineProcess
from amiga_reversing.tools.copperline_runtime import (
    release_handoff, verify_handoff, wait_for_marker,
)
from amiga_reversing.tools.direct_payload_adapter import (
    DirectPayloadContract, NDK_INCLUDE, VASM, build_boot_adf,
)
from amiga_reversing.tools.pandora_layout_walkthrough import TARGET, export_context


def run(export: Path, output: Path, rom: Path, copperline: Path) -> dict:
    payload = json.loads(export.read_text())
    paths = resolve_project_paths(TARGET)
    original = read_binary_source_bytes(paths.binary_source)
    metadata_hash = hashlib.sha256(effective_metadata_text(
        paths.target_dir, binary_source=paths.binary_source).encode()).hexdigest()
    plan, bootstrap, _ = export_context(payload, original, metadata_hash)
    if bootstrap['load_address'] != 0x20000:
        raise ValueError('Diagnostic code requires the reviewed staging base $20000')
    owner = next(r for r in plan['regions'] if r['region_id'] == 'pandora_ui_snapshot_body')
    if owner['size'] != 2304 or owner['original_address'] != 0x7f0:
        raise ValueError('Reviewed body snapshot extent changed; inspect before probing')
    output.mkdir(parents=True, exist_ok=False)
    source = PROJECT_ROOT / 'tools/amiga_allocmem_probe.s'
    binary = output / 'probe.bin'
    subprocess.run([str(VASM), '-quiet', '-m68000', '-Fbin', '-I' + str(NDK_INCLUDE),
                    '-DPROBE_SIZE=' + str(owner['size']), '-o', str(binary), str(source)], check=True)
    identity = hashlib.sha256(binary.read_bytes()).hexdigest()
    results = []
    # Match the real full staged input backing even though this diagnostic
    # payload is only one sector. No allocation may corrupt future input bytes.
    backing = ((bootstrap['load_address'], (bootstrap['file_size'] + 7) & ~7),)
    for padding in (0, 64):
        out = output / str(padding)
        contract = DirectPayloadContract('allocator-probe', TARGET, identity, 0x20000,
            0x20000, {'d5': padding}, 0x7fff8, 0x48414e44, reservations=backing)
        build = build_boot_adf(contract, binary, out / 'probe.adf')
        with CopperlineProcess(str(copperline), rom=str(rom), floppy=out / 'probe.adf',
                               machine_profile='a500ecs_1m') as process:
            client = process.client
            if not wait_for_marker(client, 0x7fff8, b'HAND', 90)['matched']:
                raise RuntimeError('Diagnostic did not reach the verified cold handoff')
            verify_handoff(client, contract, binary)
            release_handoff(client, contract)
            if not wait_for_marker(client, 0x7fff8, b'DONE', 30)['matched']:
                raise RuntimeError('Guest allocation/free diagnostic did not finish')
            raw = client.read_memory(0x20100, 16)
            base, scratch, requested, freed = [int.from_bytes(raw[i:i+4], 'big')
                                               for i in range(0, 16, 4)]
            if requested != padding or freed != bool(base):
                raise RuntimeError('Diagnostic allocation/free result is inconsistent')
            results.append(dict(prior_scratch_bytes=padding, owner_base=base,
                scratch_base=scratch, owner_free_completed=bool(freed),
                adf_sha256=hashlib.sha256((out / 'probe.adf').read_bytes()).hexdigest(),
                registers=client.registers()))
            print('ALLOCATOR_PROBE', padding, hex(base), 'freed', bool(freed), flush=True)
    report = dict(schema='pandora-allocmem-probe/v1', status='diagnostic_only_not_gameplay',
        owner=owner, input_backing=backing, results=results,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        payload_sha256=identity, export_sha256=hashlib.sha256(export.read_bytes()).hexdigest(),
        layout_plan_sha256=payload['layout_plan_sha256'], metadata_sha256=metadata_hash,
        rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
        emulator_sha256=hashlib.sha256(copperline.read_bytes()).hexdigest(),
        limits=['Only allocation/free capability and actual return values; not a game execution.',
                'No game-pointer fixups, hardware takeover or OS cleanup are implemented.',
                'Only staged-input and marker backing are reserved here; other fixed game ranges are not leased.',
                'A successful AllocMem return is not admission of a legal Pandora placement.'])
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-json', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--copperline', type=Path, required=True)
    args = parser.parse_args()
    run(args.export_json, args.output, args.rom, args.copperline)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

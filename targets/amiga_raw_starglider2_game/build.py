#!/usr/bin/env python3
"""Rebuild the original raw payload and its explicitly separate analysis views."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

EXPECTED_SIZE = 412736
EXPECTED_SHA256 = '662976920689c38fd47271ed7e656a92caf20aa20ce0b8801db2bdc77ba864d9'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Missing or unsafe package input: ' + relative)
    return path


def check_inputs(root, manifest):
    for entry in manifest['files']:
        path = safe_path(root, entry['path'])
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError('Changed package input: ' + entry['path'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vasm', default='vasmm68k_mot', help='Motorola vasm frontend, name or absolute path')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'rendered-manifest.json').read_text())
    check_inputs(root, manifest)
    vasm = shutil.which(args.vasm)
    if vasm is None:
        raise FileNotFoundError('Install vasmm68k_mot or pass --vasm /absolute/path')
    tool_hash = digest(Path(vasm))
    output_dir = root / 'bin/rebuilt'
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    built = {}
    for item in manifest['build_outputs']:
        source = safe_path(root, item['source'])
        output = output_dir / item['filename']
        result = subprocess.run([vasm, '-quiet', '-Fbin', '-m68000', '-no-opt',
                                 '-I' + str(root / 'includes'), '-o', str(output), str(source)],
                                cwd=root, capture_output=True, text=True)
        (output_dir / (item['filename'] + '.log')).write_text(result.stdout + result.stderr)
        result.check_returncode()
        data = output.read_bytes()
        if len(data) != item['bytes'] or digest(output) != item['sha256']:
            raise ValueError('Output differs from reviewed original/view: ' + item['filename'])
        built[item['role']] = data
        outputs.append(dict(role=item['role'], filename=item['filename'], bytes=len(data), sha256=digest(output)))
    original = built['original_main']
    if len(original) != EXPECTED_SIZE or hashlib.sha256(original).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Main output does not match the known original identity')
    for asset in manifest['assets']:
        data = safe_path(root, asset['path']).read_bytes()
        start = asset['source_offset']
        if data != original[start:start + asset['size']]:
            raise ValueError('INCBIN asset differs from its original source slice: ' + asset['path'])
    spec = importlib.util.spec_from_file_location('sg2_original_protection_recipe', root / 'tools/starglider2_protection.py')
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    decoded, _ = recipe.extract(original)
    expected_view = decoded + original[0x13D1C - 0x1000:0x13D5C - 0x1000]
    view = built['decoded_analysis_view']
    if view != expected_view or recipe.encode(view[:recipe.SIZE]) != original[0x12F80 - 0x1000:0x13D1C - 0x1000]:
        raise ValueError('Decoded analysis view or inverse differs from original encoded storage')
    if built['boot_installer_context'][20:] != built['boot_resident_view']:
        raise ValueError('Boot installer source bytes differ from the resident shim view')
    check_inputs(root, manifest)
    if digest(Path(vasm)) != tool_hash:
        raise ValueError('Assembler changed during the build')
    receipt = dict(schema_version=1, status='pass', format='raw_payload_not_AmigaDOS_HUNK',
                   main_bytes=EXPECTED_SIZE, main_sha256=EXPECTED_SHA256, main_matches_original_identity=True,
                   asset_count=len(manifest['assets']), all_asset_source_slices_equal=True,
                   decoded_view_inverse_exact=True, boot_copy_source_matches_resident_view=True,
                   source_commit=manifest['source_commit'], assembler_sha256=tool_hash,
                   flags=['-Fbin', '-m68000', '-no-opt'], outputs=outputs)
    (output_dir / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: all 412736 main bytes match the known original SHA256')
    print('PASS: all INCBIN slices, separate analysis outputs and inverse recipe match')
    print('SHA256 ' + EXPECTED_SHA256)
    print('The main output is a raw image, not an AmigaDOS executable or bootable disk.')


if __name__ == '__main__':
    main()

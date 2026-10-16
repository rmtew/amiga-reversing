"""Explicit, fixed-size optional patches for raw single-section targets.

This does not alter canonical facts, generated source, or original payloads.
The CLI admits canonical boundary rows before writing a new rebuilt artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def anchor_offset(key: str) -> int:
    match = re.fullmatch(r's0:([0-9A-Fa-f]{8}):instruction', key)
    if not match:
        raise ValueError('Only raw section-zero instruction anchors are supported')
    return int(match[1], 16)


def apply_patches(original: bytes, manifest: dict, enabled: list[str]) -> tuple[bytes, list[dict]]:
    """Validate the entire selected set before changing any bytes."""
    if manifest.get('schema_version') != 1 or manifest.get('layout') != 'raw-single-section':
        raise ValueError('Unsupported patch manifest version or layout')
    if sha256(original) != manifest.get('original_sha256'):
        raise ValueError('Original payload hash mismatch')
    records = manifest['patches']
    ids = [p['id'] for p in records]
    if len(set(ids)) != len(ids) or len(set(enabled)) != len(enabled):
        raise ValueError('Duplicate patch identifiers')
    if set(enabled) - set(ids):
        raise ValueError('Unknown enabled patch')
    selected = [p for p in records if p['id'] in enabled]
    ranges = []
    for patch in selected:
        if not patch.get('rationale') or not patch.get('preconditions'):
            raise ValueError('Patch needs rationale and preconditions')
        if set(patch.get('conflicts', [])) & set(enabled):
            raise ValueError('Conflicting optional patches')
        start, end = anchor_offset(patch['start']), anchor_offset(patch['end'])
        expected, replacement = bytes.fromhex(patch['expected_hex']), bytes.fromhex(patch['replacement_hex'])
        if not 0 <= start < end <= len(original):
            raise ValueError('Patch range is outside original payload')
        if len(expected) != end-start or len(replacement) != end-start:
            raise ValueError('Optional patches must preserve layout and size')
        if original[start:end] != expected:
            raise ValueError('Patch expected bytes mismatch')
        if any(start < old_end and old_start < end for old_start, old_end in ranges):
            raise ValueError('Overlapping optional patches')
        ranges.append((start, end))
    result = bytearray(original)
    for patch, (start, end) in zip(selected, ranges):
        result[start:end] = bytes.fromhex(patch['replacement_hex'])
    return bytes(result), selected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--enable', action='append', default=[])
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args(argv)
    from amiga_reversing.disasm.binary_source import BinarySourceKind
    from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile
    from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    paths = resolve_project_paths(manifest['target_id'])
    if paths.binary_source.kind != BinarySourceKind.RAW_BINARY:
        raise ValueError('Optional patch CLI currently admits raw targets only')
    output = args.output_directory.resolve()
    if not output.is_relative_to((PROJECT_ROOT / 'bin/rebuilt').resolve()):
        raise ValueError('Output must be a fresh directory under bin/rebuilt')
    original = paths.binary_source.read_bytes()
    payload, selected = apply_patches(original, manifest, args.enable)
    if selected:
        _, _, artifact = build_project_listing_artifact_profile(manifest['target_id'])
        try:
            for patch in selected:
                for key in (patch['start'], patch['end']):
                    row = artifact.row_for_source_offset(section_index=0, offset=anchor_offset(key))
                    if not row or row.get('stable_key') != key:
                        raise ValueError(f'Patch boundary is not a canonical instruction: {key}')
                source = (args.manifest.parent / patch['assembly']).resolve()
                if not source.is_relative_to(args.manifest.parent.resolve()):
                    raise ValueError('Assembly annotation must be inside the patch directory')
                if sha256(source.read_bytes()) != patch['assembly_sha256']:
                    raise ValueError('Assembly annotation hash mismatch')
        finally:
            artifact.close()
    receipt = {'schema_version': 1, 'kind': 'fixed_size_optional_patch',
               'layout': 'raw-single-section', 'artifact_file': 'payload.bin',
               'target_id': manifest['target_id'],
               'manifest_sha256': sha256(manifest_bytes), 'original_sha256': sha256(original),
               'output_sha256': sha256(payload), 'size': len(payload),
               'enabled': [p['id'] for p in selected], 'default_original': not selected,
               'patches': selected}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'payload.bin').write_bytes(payload)
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

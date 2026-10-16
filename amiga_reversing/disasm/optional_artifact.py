"""Runtime admission for explicit fixed-size patches; no interior source mapping."""
from pathlib import Path
import re

from amiga_reversing.disasm.binary_source import BinarySourceKind
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.tools.optional_patch import apply_patches, anchor_offset, sha256

KIND = 'fixed_size_optional_patch'


def validate(manifest: dict, directory: Path, target_id: str):
    fields = {'schema_version', 'kind', 'layout', 'artifact_file', 'target_id',
              'manifest_sha256', 'original_sha256', 'output_sha256', 'size',
              'enabled', 'default_original', 'patches'}
    if set(manifest) != fields or manifest['kind'] != KIND or manifest['target_id'] != target_id:
        raise ValueError('Invalid optional artifact contract')
    if not manifest['enabled'] or manifest['default_original'] is not False:
        raise ValueError('Runtime optional artifact needs an explicitly enabled correction')
    for field in ('manifest_sha256', 'original_sha256', 'output_sha256'):
        if not isinstance(manifest[field], str) or not re.fullmatch('[0-9a-f]{64}', manifest[field]):
            raise ValueError('Invalid optional artifact identity')
    source = resolve_project_paths(target_id).binary_source
    if source.kind != BinarySourceKind.RAW_BINARY:
        raise ValueError('Optional artifacts require a raw target')
    original = source.read_bytes()
    expected, selected = apply_patches(original, manifest, manifest['enabled'])
    if selected != manifest['patches'] or type(manifest['size']) is not int or manifest['size'] != len(expected):
        raise ValueError('Optional artifact selection or size mismatch')
    name = manifest['artifact_file']
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise ValueError('Optional artifact requires a sibling payload filename')
    path = directory / name
    payload = path.read_bytes()
    if payload != expected or sha256(payload) != manifest['output_sha256']:
        raise ValueError('Optional artifact differs from its exact patch ledger')
    return manifest, path


def verify_binding(manifest: dict, artifact):
    for patch in manifest['patches']:
        for key in (patch['start'], patch['end']):
            row = artifact.row_for_source_offset(section_index=0, offset=anchor_offset(key))
            if not row or row.get('stable_key') != key:
                raise ValueError('Optional artifact boundary is not a canonical instruction')


def overlaps(manifest: dict, start: int, end: int) -> bool:
    return any(start < anchor_offset(p['end']) and anchor_offset(p['start']) < end
               for p in manifest['patches'])

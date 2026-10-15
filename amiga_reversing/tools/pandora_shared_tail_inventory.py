"""Read-only native inventory for Pandora's shared hit-snapshot/palette tail.

Enumerates current accepted references; absence is never an ownership proof.
The interpretation and bounded phase contract live in the validation ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.restoration_client import RestorationClient

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
SYMBOLS = (
    'clear_rgb12_palette_components', 'add_rgb12_palette_components',
    'subtract_rgb12_palette_components', 'unpack_rgb12_palette_components',
    'prepare_work_buffer_arguments', 'return_work_buffer_argument',
    'render_work_buffer_overlay', 'fade_out_work_buffer_palette',
    'prime_blitter_completion_request', 'start_seeded_zero_copy_blit',
    'save_ui_overlay_background', 'restore_ui_overlay_background',
)


def collect(client):
    state = client.call(TARGET, 'state')
    if not state['ready']:
        raise ValueError('Open the resident target and wait until ready before collecting')
    revision = state['revision']

    def query(**parameters):
        items = []
        while True:
            result = client.call(TARGET, 'query', expected_revision=revision, limit=100, **parameters)
            items.extend(result['items'])
            if not result['has_more']:
                return items
            cursor = result['next_cursor']
            if not result['items'] or not cursor or cursor == parameters.get('cursor'):
                raise ValueError('Native query pagination made no progress')
            parameters['cursor'] = cursor

    regions = query(kind='memory_regions')
    hit = next(r for r in regions if r['region_id'] == 'pandora_ui_snapshot_hit')
    pointers = query(kind='typed_pointers', struct_name='ui_overlay_descriptor')
    all_pointers = query(kind='typed_pointers')
    fields = query(kind='fields', struct_name='ui_overlay_descriptor')
    bitmap = [p for p in pointers if p['field_name'] == 'bitmap_ptr']
    references = {name: query(kind='references', symbol=name) for name in SYMBOLS}
    binary = resolve_project_paths(TARGET).binary_source.path.read_bytes()
    return {
        'schema_version': 1, 'target_id': TARGET, 'revision': revision,
        'subject_revision': state['subject_revision'],
        'original_sha256': hashlib.sha256(binary).hexdigest(),
        'scope': 'Accepted native facts and initial typed fields only; indirect/unclassified paths and later pointer mutation remain open.',
        'hit_region': hit,
        'typed_overlay_pointer_population': len(pointers),
        'initial_bitmap_fields': bitmap,
        'all_typed_pointer_population': len(all_pointers),
        'typed_pointer_fields_in_hit_region': [p for p in all_pointers
            if type(p.get('resolution', {}).get('encoded_value')) is int
            and hit['runtime_address'] <= p['resolution']['encoded_value']
            < hit['runtime_address']+hit['size']],
        'overlay_field_use_population': len(fields),
        'resolved_bitmap_field_uses': [f for f in fields if f.get('field_name') == 'bitmap_ptr'],
        'unresolved_overlay_field_uses': [f for f in fields if f.get('status') == 'unresolved'],
        'references': references,
        'bltcon1_writers': query(kind='instructions', query='bltcon1'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(collect(RestorationClient(timeout=300)), indent=2)+'\n')


if __name__ == '__main__':
    main()

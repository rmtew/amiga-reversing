"""Collect native initialized world-object/descriptor reference identities."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.restoration_client import RestorationClient

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'


def collect(client):
    state = client.call(TARGET, 'state')
    if not state['ready']:
        raise ValueError('Wait for the resident target to become ready')
    revision = state['revision']
    binary = resolve_project_paths(TARGET).binary_source.path.read_bytes()
    families = {}
    for schema, expected in [('world_object_source_reference', 36),
                             ('world_position_descriptor_source_reference', 61)]:
        result = client.call(TARGET, 'query', kind='typed_pointers', struct_name=schema,
                             expected_revision=revision, limit=100)
        if result['has_more'] or len(result['items']) != expected:
            raise ValueError(f'Unexpected initialized reference population for {schema}')
        entries = []
        for item in result['items']:
            resolution = item['resolution']
            encoded = int.from_bytes(binary[item['source_offset']:item['source_offset']+4], 'big')
            if resolution['outcome'] == 'symbolic' and resolution.get('encoded_value') != encoded:
                raise ValueError('Native encoded pointer identity differs from original bytes')
            if resolution['outcome'] == 'symbolic' and resolution.get('target_section_index') != 0:
                raise ValueError('Native reference resolves outside the accepted source section')
            entries.append({'source_offset': item['source_offset'], 'encoded_pointer': encoded,
                            'resolution': resolution['outcome'], 'reason': resolution.get('reason'),
                            'target_section_index': resolution.get('target_section_index'),
                            'native_target_offset': resolution.get('target_offset'),
                            'symbol': resolution.get('symbol')})
        families[schema] = entries
    nulls = [entry['source_offset'] for values in families.values() for entry in values
             if not entry['encoded_pointer']]
    if nulls != [0x3096]:
        raise ValueError('The initialized object sentinel changed')
    return {'schema_version': 1, 'target_id': TARGET, 'revision': revision,
            'subject_revision': state['subject_revision'],
            'original_sha256': hashlib.sha256(binary).hexdigest(), 'families': families,
            'symbolic_nonzero_reference_count': sum(bool(entry['encoded_pointer']) and entry['resolution'] == 'symbolic'
                for values in families.values() for entry in values),
            'unresolved_nonzero_reference_count': sum(bool(entry['encoded_pointer']) and entry['resolution'] != 'symbolic'
                for values in families.values() for entry in values),
            'physical_prefixes': [
                {'start': 0x300A, 'end': 0x309A, 'entries': 36, 'role': '35 objects then NULL'},
                {'start': 0x309A, 'end': 0x310E, 'entries': 29, 'role': 'active descriptors'},
                {'start': 0x310E, 'end': 0x318E, 'entries': 32, 'role': 'sort descriptor source'}],
            'limits': ['Initial source references, not immutable runtime values or unique objects.',
                       'The object scan uses NULL; physical prefixes are not all-input bounds.',
                       'Changed candidate cooldown overwrites the distance threshold register.',
                       'Callback, storage ownership and asynchronous lifetimes remain open.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(collect(RestorationClient(timeout=300)), indent=2)+'\n')


if __name__ == '__main__':
    main()

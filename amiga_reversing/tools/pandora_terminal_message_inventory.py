"""Enumerate the terminal record family through current native typed references."""
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

    def query(**parameters):
        items = []
        while True:
            r = client.call(TARGET, 'query', expected_revision=revision, limit=100, **parameters)
            items.extend(r['items'])
            if not r['has_more']:
                return items
            cursor = r['next_cursor']
            if not r['items'] or not cursor or cursor == parameters.get('cursor'):
                raise ValueError('Native query pagination made no progress')
            parameters['cursor'] = cursor

    binary = resolve_project_paths(TARGET).binary_source.path.read_bytes()
    pointers = query(kind='typed_pointers', struct_name='terminal_location_message_reference')
    labels = query(kind='typed_pointers', struct_name='terminal_clearance_label_reference')
    records = []
    for pointer in pointers:
        resolution = pointer['resolution']
        if resolution['outcome'] != 'symbolic' or resolution.get('target_section_index') != 0:
            raise ValueError('Terminal record is not resolved by native source mapping')
        offset = resolution['target_offset']
        end = binary.index(0, offset+4)+1
        records.append({'pointer_source_offset': pointer['source_offset'],
                        'encoded_pointer': resolution['encoded_value'],
                        'native_target_offset': offset, 'symbol': resolution['symbol'],
                        'world_x': int.from_bytes(binary[offset:offset+2], 'big'),
                        'world_y': int.from_bytes(binary[offset+2:offset+4], 'big'),
                        'text_start': offset+4, 'end_offset': end,
                        'text': binary[offset+4:end-1].decode('ascii')})
    display = []
    for pointer in labels:
        resolution = pointer['resolution']
        if resolution['outcome'] != 'symbolic' or resolution.get('target_section_index') != 0:
            raise ValueError('Clearance label is not resolved by native source mapping')
        offset = resolution['target_offset']
        end = binary.index(0, offset)+1
        display.append({'pointer_source_offset': pointer['source_offset'],
                        'encoded_pointer': resolution['encoded_value'],
                        'native_target_offset': offset, 'symbol': resolution['symbol'],
                        'text': binary[offset:end-1].decode('ascii')})
    return {'schema_version': 1, 'target_id': TARGET, 'revision': revision,
            'subject_revision': state['subject_revision'],
            'original_sha256': hashlib.sha256(binary).hexdigest(),
            'records': records, 'display_labels': display,
            'header_field_uses': query(kind='fields', struct_name='terminal_location_message_header'),
            'limits': ['Initial accepted typed references, not immutable runtime pointer values.',
                       'Physical table prefixes are not admission guards; source scan still uses NULL.',
                       'Byte display selector domain is distinct from security authorization.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(collect(RestorationClient(timeout=300)), indent=2)+'\n')


if __name__ == '__main__':
    main()

"""Collect the ranged-impact family's canonical fields and native resolutions."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.restoration_client import RestorationClient
from amiga_reversing.disasm.typed_pointer_report import typed_pointer_report

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
OWNERS = ('ranged_hit_visual_descriptor', 'ranged_hit_visual_state',
          'ranged_hit_visual_geometry_frames', 'ranged_hit_visual_animation', 'ranged_hit_visual_frame_ptrs')


def collect(client):
    state = client.call(TARGET, 'state')
    if not state['ready']:
        raise ValueError('Wait for the resident target to become ready')
    paths = resolve_project_paths(TARGET)
    metadata = effective_target_metadata(paths.target_dir)
    layouts = {layout.name: layout for layout in metadata.data_block_layouts}
    selected = [layouts[name] for name in OWNERS]
    rows = {}
    for layout in selected:
        listing = client._request('/api/projects/'+TARGET+'/listing?'+urlencode({
            'section_index': layout.hunk, 'source_offset': layout.source_start, 'before': 0, 'after': 192}))['data']
        for row in listing['rows']:
            if row.get('kind') == 'data' and layout.source_start <= row['start_offset'] < layout.source_end:
                rows[(row['section_index'], row['start_offset'])] = row
    fields = tuple(entity for entity in metadata.seeded_entities if any(
        entity.hunk == layout.hunk and layout.source_start <= entity.addr < layout.source_end for layout in selected))
    scoped = replace(metadata, seeded_entities=fields)
    report = typed_pointer_report(scoped, lambda section_index, offset: rows.get((section_index, offset)), limit=100)
    if report['has_more']:
        raise ValueError('Ranged-impact family exceeds the bounded report size')
    after = client.call(TARGET, 'state')
    if after['revision'] != state['revision']:
        raise ValueError('Target revision changed during native field collection')
    return {'schema_version': 1, 'target_id': TARGET, 'revision': state['revision'],
            'subject_revision': state['subject_revision'],
            'original_sha256': hashlib.sha256(paths.binary_source.path.read_bytes()).hexdigest(),
            'layouts': [{'name': layout.name, 'start': layout.source_start, 'end': layout.source_end,
                         'layout_id': layout.layout_id} for layout in selected], 'pointers': report,
            'limits': ['Initial encoded fields, not immutable runtime values or allocation/lifetime proof.',
                       'The adjacent second visual state and earlier frame sequence remain outside this family.',
                       'A1 return facts cover the three known consumers; arbitrary future callers are not inferred.',
                       'Ray termination and callback/IRQ/DMA exclusion remain open.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(collect(RestorationClient(timeout=300)), indent=2)+'\n')


if __name__ == '__main__':
    main()

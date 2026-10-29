"""Join native source facts to canonical layouts for gap discovery.

Names/comments are audit signals, never admission evidence. This tool performs
no decoding, pointer guessing, code promotion, naming or metadata mutation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

_SUFFIX = re.compile(r"_(?:base|bases|pointer|pointers|offset|offsets)(?:_\d+)?$")


def _span(item):
    return item.get('offset', 0), item.get('offset', 0) + item.get('size', 0)


def _field_gap(access, structs):
    if access.get('access') == 'address':
        return 'address_formation'
    width = access.get('access_size', 0)
    if width == 0:
        return 'address_formation_or_unknown_width'
    record = structs.get(access.get('root_struct_name'))
    if record is None:
        return 'missing_structure_contract'
    lo = access['displacement']
    hi = lo + width
    if lo < 0 or hi > record['size']:
        return 'outside_declared_record'
    # Diagnostic coverage only: native facts still own field/type admission.
    # A parent declaration is no longer a blanket unimplemented mechanism.
    fields = list(record.get('fields', []))
    seen = {record['name']}
    inherited = bool(record.get('base_struct'))
    while record.get('base_struct'):
        parent = record['base_struct']
        if parent in seen:
            return 'cyclic_inherited_structure_contract'
        seen.add(parent)
        record = structs.get(parent)
        if record is None:
            return 'missing_inherited_structure_contract'
        fields.extend(record.get('fields', []))
    end = lo
    for start, stop in sorted(_span(field) for field in fields):
        if stop <= end:
            continue
        if start > end:
            break
        end = max(end, stop)
    if end < hi:
        if access.get('source_zero_write') is True:
            return 'source_zero_write_to_field_hole'
        return 'declared_field_hole'
    return 'covered_inherited_span_requires_native_review' if inherited else 'covered_partial_or_composite_access'


def inventory(analysis: dict, metadata: dict, source: str) -> dict:
    """Return candidate evidence, keeping domains and unmeasured facts explicit."""
    sections = {s['section_index']: s for s in analysis.get('sections', [])}
    structs = {s['name']: s for s in metadata.get('custom_structs', [])}
    policy = analysis.get('analysis_policy', {}).get('structured_data_items', [])
    by_name = defaultdict(list)
    for item in policy:
        if item.get('label'):
            by_name[item['label']].append(item)
    entities = defaultdict(list)
    for entity in metadata.get('seeded_entities', []):
        if entity.get('name'):
            entities[entity['name']].append(entity)
    layouts = {r['name']: r for r in metadata.get('data_block_layouts', []) if r.get('name')}
    absolute_slots = defaultdict(list)
    for slot in metadata.get('absolute_storage_slots', []):
        absolute_slots[slot['symbol']].append(slot)
    app_fields = defaultdict(list)
    for field in analysis.get('base_layout_fields', []):
        app_fields[field['symbol']].append(field)
    definitions = defaultdict(list)
    refs = defaultdict(list)
    app_refs = defaultdict(list)
    values = {}
    consumers = defaultdict(list)
    for section_id, section in sections.items():
        for ref in section.get('rendered_symbol_accesses', []):
            row = dict(section_index=section_id, **ref)
            refs[ref['symbol_name']].append(row)
            if ref['access_kind'] == 'label_statement':
                definitions[ref['symbol_name']].append((section_id, ref['offset']))
        for ref in section.get('app_slot_refs', []):
            app_refs[ref['symbol_name']].append(dict(section_index=section_id, **ref))
        for value in section.get('address_values', []):
            values[section_id, value['id']] = value
        for consumer in section.get('address_value_consumers', []):
            if consumer.get('contract_name'):
                consumers[consumer['contract_name']].append(dict(section_index=section_id, **consumer))
    policy_indices = {id(item): index for index, item in enumerate(policy)}
    policy_catalog, layout_catalog, value_catalog = {}, {}, {}

    def policy_ref(item):
        key = f"policy:{policy_indices[id(item)]}"
        policy_catalog[key] = item
        return key

    def layout_ref(layout):
        if layout is None:
            return None
        key = layout['layout_id']
        layout_catalog[key] = layout
        return key

    def value_ref(consumer):
        key = f"s{consumer['section_index']}:v{consumer['address_value_id']}"
        value_catalog[key] = values.get((consumer['section_index'], consumer['address_value_id']))
        return key

    names = sorted(name for name in refs if _SUFFIX.search(name))
    named = []
    for name in names:
        source_definitions = definitions.get(name, [])
        is_code = any(any(run['start_offset'] <= offset < run['end_offset']
                          for run in sections[section_id].get('accepted_code_runs', []))
                      for section_id, offset in source_definitions)
        is_text = (any(r.get('kind') == 4 for r in by_name.get(name, [])) or
                   any(r.get('subtype') in {'string', 'string_control_stream', 'length_prefixed_string'}
                       for r in entities.get(name, [])))
        kind = ('code_name_signal' if is_code else 'text_name_signal' if is_text else 'named_base_layout_storage' if name in app_fields
                else 'named_absolute_storage' if name in absolute_slots
                else 'named_source_storage' if source_definitions else 'other_symbol_domain')
        producers = [value_ref(c) for c in consumers.get(name, [])]
        named.append(dict(name=name, signal='suffix', disposition=kind,
                          definitions=[dict(section_index=s, offset=o) for s, o in source_definitions],
                          canonical_item_ids=[policy_ref(item) for item in by_name.get(name, [])],
                          canonical_entities=entities.get(name, []), canonical_layout_id=layout_ref(layouts.get(name)),
                          base_layout_fields=app_fields.get(name, []), absolute_storage_slots=absolute_slots.get(name, []),
                          app_accesses=app_refs.get(name, []),
                          address_consumers=consumers.get(name, []), address_producer_ids=producers,
                          rendered_references=refs[name],
                          exported_definition=bool(re.search(r'^' + re.escape(name) + r'(?::|\s+(?i:EQU)\b)', source, re.M))))
    generic_fields = [dict(domain='base_layout', field=field,
                           app_accesses=app_refs.get(field['symbol'], []),
                           address_consumers=consumers.get(field['symbol'], []))
                      for field in analysis.get('base_layout_fields', [])
                      if re.fullmatch(r'app_[0-9a-fA-F]+', field['symbol'])]
    policy_by_section = defaultdict(list)
    for item in policy:
        policy_by_section[item.get('section_index')].append(item)
    tables, interiors, unresolved = [], [], []
    for section_id, section in sections.items():
        for table in section.get('table_descriptors', []):
            if table.get('role') == 'lookup_table':
                tables.append(dict(section_index=section_id, **table))
        for name, rows in refs.items():
            starts = {offset for s, offset in definitions.get(name, []) if s == section_id}
            if len(starts) != 1:
                continue
            start = next(iter(starts))
            for row in rows:
                target = row.get('target_offset')
                if (row['section_index'] == section_id and row['access_kind'] == 'operand'
                        and row.get('target_section_index') == section_id and target is not None and target != start):
                    interiors.append(dict(section_index=section_id, source_offset=row['offset'],
                                          operand_index=row.get('operand_index'), symbol=name,
                                          base_source_offset=start, target_source_offset=target,
                                          addend=target-start, evidence='native_rendered_target_identity',
                                          canonical_layout_id=layout_ref(layouts.get(name)),
                                          target_policy_item_ids=[policy_ref(item) for item in policy_by_section[section_id]
                                                               if item['offset'] <= target < item['offset'] + item['size']]))
        for access in section.get('recovered_platform_unresolved_typed_accesses', []):
            mechanism = (_field_gap(access, structs) if access['classification'] == 'field_gap'
                         else access['classification'])
            unresolved.append(dict(section_index=section_id, mechanism=mechanism, **access))
    arrays = []
    for layout in metadata.get('data_block_layouts', []):
        for element in layout.get('elements', []):
            binding = element.get('type_binding') or {}
            record = structs.get(binding.get('bound_type_id'))
            count = binding.get('array_count') or element.get('array_count') or 1
            if record is None or count < 2 or record['size'] != 4 or len(record.get('fields', [])) != 1:
                continue
            field = record['fields'][0]
            if field['offset'] != 0 or field['size'] != 4 or field.get('value_kind') not in {'target_pointer', 'struct_pointer'}:
                continue
            start = layout['source_start'] + element['offset']
            end = start + element['width']
            if (end > layout['source_end'] or end-start != count*record['size']
                    or (element.get('array_stride') or record['size']) != record['size']):
                continue
            section_id = layout['hunk']
            matching = [t for t in sections.get(section_id, {}).get('table_descriptors', [])
                        if t['start_offset'] == start and t['end_offset'] == end and t['table_kind'] in {'pointer', 'absolute_code_dispatch'}]
            collection_consumers = [dict(section_index=sid, **consumer)
                                    for sid, consumer_section in sections.items()
                                    for consumer in consumer_section.get('table_consumers', [])
                                    if consumer.get('table_section_index') == section_id
                                    and consumer.get('table_start_offset') == start
                                    and consumer.get('table_end_offset') == end]
            overlapping = [r for r in policy if r.get('section_index') == section_id and start <= r.get('offset', -1) < end]
            leaves = [r for r in overlapping if r['size'] == 4 and (r['offset'] - start) % 4 == 0]
            contracts = [t for t in sections.get(section_id, {}).get('table_descriptors', [])
                         if t['start_offset'] < end and t['end_offset'] > start]
            arrays.append(dict(layout_id=layout['layout_id'], name=layout.get('name'), section_index=section_id,
                               start_offset=start, end_offset=end, record_count=count, record_type=record['name'],
                               pointer_field=field, native_collection_contracts=matching,
                               native_collection_consumers=collection_consumers,
                               native_leaf_items=len(leaves), native_overlapping_items=len(overlapping),
                               native_overlapping_contracts=contracts, bound_targets=sum(bool(r.get('has_target')) for r in leaves),
                               mechanism='collection_contract_exposed' if matching else 'canonical_array_projected_as_leaves',
                               experiment=('Follow native consumer index domains and original pointee producers; structural extent does not prove selector bounds.'
                                           if matching else 'Reproduce the homogeneous pointer-record array through metadata admission; preserve domains/aliases while testing shared collection projection.')))
    orphans = [dict(section_index=sid, **r) for sid, section in sections.items()
               for r in section.get('orphan_code_signals', [])]
    return dict(schema_version=2, kind='source_gap_discovery_not_fact_admission',
                canonical_policy_items=policy_catalog, canonical_layouts=layout_catalog, address_values=value_catalog,
                summary=dict(native_table_contracts=sum(len(s.get('table_descriptors', [])) for s in sections.values()),
                             native_table_consumer_records=sum(len(s.get('table_consumers', [])) for s in sections.values()),
                             native_address_expression_records=sum(len(s.get('address_expressions', [])) for s in sections.values()),
                             suffix_names=len(named), suffix_dispositions=dict(Counter(r['disposition'] for r in named)),
                             lookup_contracts=len(tables), lookup_kinds=dict(Counter(r['table_kind'] for r in tables)),
                             interior_reference_records=len(interiors), unresolved_typed_accesses=len(unresolved),
                             unresolved_mechanisms=dict(Counter(r['mechanism'] for r in unresolved)),
                             orphan_signal_statuses=dict(Counter(r['status'] for r in orphans)),
                             generic_base_layout_fields=len(generic_fields),
                             generic_base_symbols=len({r['field']['symbol'] for r in generic_fields}),
                             homogeneous_pointer_record_arrays=len(arrays), array_projection_mechanisms=dict(Counter(r['mechanism'] for r in arrays))),
                record_contracts={name: structs[name] for name in sorted(
                    {r['root_struct_name'] for r in unresolved if r.get('root_struct_name')} | {r['record_type'] for r in arrays}
                    | {policy_catalog[key]['struct_name'] for row in named for key in row['canonical_item_ids']
                       if policy_catalog[key].get('struct_name')})
                    if name in structs},
                named_signals=named, generic_base_fields=generic_fields,
                lookup_contracts=tables, interior_references=interiors,
                unresolved_typed_accesses=unresolved, pointer_record_arrays=arrays, orphan_code_signals=orphans,
                unresolved_indirect_sites=[dict(section_index=sid, **r) for sid, s in sections.items()
                                           for r in s.get('recovered_indirect_sites', []) if r['status'] == 'unresolved'],
                scope=['Suffixes and comments only discover candidates; meaningful bases, scalar tables and routine names are not automatically defects.',
                       'Source coordinates, runtime/base-layout identities and actual rendered target offsets remain separate. No parsing address-looking numbers or guessing pointer targets.',
                       'A declared field hole is not a framework defect or permission to invent a universal polymorphic field meaning.',
                       'Metadata array extent is structural evidence, not a runtime selector bound. Collection projection candidates require positive/refusal fixtures before changes.',
                       'Catalog references identify exact input records; their indices are snapshot identities, not independently promoted facts.',
                       'Native rendered accesses describe the inline export. exported_definition checks the selected source; INCBIN packaging may intentionally hide internal boundaries.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    payloads = {key: getattr(args, key).read_bytes() for key in ('analysis', 'metadata', 'source')}
    report = inventory(json.loads(payloads['analysis']), json.loads(payloads['metadata']), payloads['source'].decode())
    report['input_sha256'] = {key: hashlib.sha256(value).hexdigest() for key, value in payloads.items()}
    report['input_binding'] = 'Caller supplies matching retained artifacts. Hashes identify inputs; discovery is not an independent correspondence/admission proof.'
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()

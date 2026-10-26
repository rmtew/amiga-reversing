"""Conservative, read-only projection of native instruction/access evidence.

No instruction decoding, assembly parsing or register-flow inference belongs here.
An app-slot rendering is an analyzer attribution, not a proven register value.
"""
from collections import Counter


class AuditIncomplete(ValueError):
    """Input cannot support a complete accepted-instruction inventory."""


def collect_instruction_pages(call, target, revision, *, progress=None):
    """Pin every page to one revision; refuse previews, gaps and changing totals."""
    rows, cursor, total, seen = [], None, None, set()
    while True:
        args = dict(kind='instructions', limit=100, expected_revision=revision)
        if cursor is not None:
            args['cursor'] = cursor
        page = call(target, 'query', **args)
        if page.get('revision') != revision or page.get('truncated_fields'):
            raise AuditIncomplete('stale or truncated instruction evidence')
        if total is None:
            total = page['total']
        if page['total'] != total or page['offset'] != len(rows):
            raise AuditIncomplete('instruction population changed or page missing')
        for row in page['items']:
            if row.get('preview_truncated') or 'operand_facts' not in row:
                raise AuditIncomplete('native operand evidence missing')
            identity = (row['section_index'], row['source_offset'])
            if identity in seen:
                raise AuditIncomplete('duplicate instruction')
            seen.add(identity)
            rows.append(row)
        if progress is not None:
            progress(len(rows), total)
        next_cursor = page.get('next_cursor')
        if not next_cursor:
            if page.get('has_more') or len(rows) != total:
                raise AuditIncomplete('incomplete instruction population')
            return rows
        if next_cursor == cursor or not page['items']:
            raise AuditIncomplete('nonadvancing instruction page')
        cursor = next_cursor


def _same_operand(records, index):
    return [r for r in records if r['operand_index'] == index]


def _native_derived_span_width(refs, operand_width):
    """Use the native full transfer span; never infer MOVEM size in Python."""
    if not refs:
        return None
    spans = set()
    for ref in refs:
        width, element, count = (ref.get(k) for k in
            ('data_access_size', 'element_width', 'transfer_count'))
        if (ref.get('derived') is not True or ref.get('access') not in {'read', 'write', 'read-write'}
                or any(type(n) is not int for n in (width, element, count))
                or element not in (1, 2, 4) or element != operand_width
                or not 1 <= count <= 16 or width != element * count or width > 64):
            return None
        spans.add(width)
    return next(iter(spans)) if len(spans) == 1 else None


def _gaps(fields, envelope):
    covered = set()
    for field in fields:
        covered.update(range(field['offset'], field['offset'] + field['size']))
    result = []
    for offset in range(envelope):
        if offset not in covered:
            if result and result[-1]['end'] == offset:
                result[-1]['end'] += 1
            else:
                result.append(dict(start=offset, end=offset + 1))
    return result


def build_app_access_audit(instructions, layout_fields, *, app_base, identity):
    """Enumerate operands, preserving conflicting and unresolved domains.

    Concrete addresses prove physical overlap only. They do not prove ownership,
    all-path register provenance, allocation size or an indexed access's bounds.
    """
    fields = [dict(f) for f in layout_fields if f.get('base_symbol') == '__amiga_app_base__']
    envelope = max((f['offset'] + f['size'] for f in fields), default=0)
    if not envelope:
        raise AuditIncomplete('app layout missing')
    gaps = _gaps(fields, envelope)
    sites, seen = [], set()
    for row in instructions:
        row_id = (row['section_index'], row['source_offset'])
        if row_id in seen or 'operand_facts' not in row:
            raise AuditIncomplete('duplicate instruction or missing native operand evidence')
        seen.add(row_id)
        for op in row['operand_facts']:
            if not op['memory']:
                continue
            index = op['operand_index']
            refs = _same_operand(row.get('app_slot_refs', []), index)
            typed = _same_operand(row.get('typed_accesses', []), index)
            unresolved = _same_operand(row.get('unresolved_typed_accesses', []), index)
            platform = _same_operand(row.get('platform_evidence', []), index)
            observations = _same_operand(row.get('address_evidence', []), index)
            addresses = {a['address'] for a in observations if a['has_address'] and not a['conflicted']}
            if op['absolute_address'] is not None:
                addresses.add(op['absolute_address'])
            width = op['width_bytes']
            derived_span = _native_derived_span_width(refs, width)
            address_use = op['access'] in {'address', 'branch_target'}
            concrete_overlap = [a - app_base for a in sorted(addresses)
                                if a < app_base + envelope and a + (width or 1) > app_base]
            hardware = any(p['shape'] in {'hardware_register_access', 'hardware_register_family'} for p in platform)
            base_contradiction = bool(refs and addresses and not op['indexed'] and
                                      any(a != app_base + r['displacement'] for a in addresses for r in refs))
            conflict = bool((refs and hardware) or base_contradiction or any(a['conflicted'] for a in observations))
            # Keep proof strength separate from the exclusive grouping.
            if conflict:
                domain = 'conflicting_evidence'
            elif hardware:
                domain = 'hardware'
            elif concrete_overlap:
                domain = 'physical_app_envelope_alias'
            elif refs:
                domain = 'native_app_attribution'
            elif typed or unresolved:
                domain = 'other_typed_record'
            elif op['base_register'] == 'A7':
                domain = 'stack'
            elif op['base_register'] == 'A6':
                domain = 'unresolved_A6'
            elif op['base_register']:
                domain = 'unresolved_register_alias'
            else:
                domain = 'other_address'
            relative = sorted({r['displacement'] for r in refs} | set(concrete_overlap))
            conditional = [op['displacement']] if domain == 'unresolved_A6' and op['displacement_known'] else []
            footprint_source = 'native_form_operand'
            if derived_span is not None and not conflict and not op['indexed'] and not address_use:
                width = derived_span
                footprint_source = 'native_derived_span'
            footprint_known = bool(width and not op['indexed'] and not address_use and
                                   (not op['bulk_transfer'] or footprint_source == 'native_derived_span'))
            overlaps, gap_hits, conditional_overlaps, conditional_gap_hits = [], [], [], []
            if footprint_known:
                for start in relative:
                    for f in fields:
                        if start < f['offset'] + f['size'] and start + width > f['offset']:
                            overlaps.append(f['symbol'])
                    for gap in gaps:
                        if start < gap['end'] and start + width > gap['start']:
                            gap_hits.append(dict(start=max(start, gap['start']), end=min(start + width, gap['end'])))
                for start in conditional:
                    conditional_overlaps.extend(f['symbol'] for f in fields
                                                if start < f['offset'] + f['size'] and start + width > f['offset'])
                    conditional_gap_hits.extend(dict(start=max(start, g['start']), end=min(start + width, g['end']))
                                                for g in gaps if start < g['end'] and start + width > g['start'])
            sites.append(dict(section_index=row_id[0], source_offset=row_id[1], operand_index=index,
                              domain=domain, **{k: op[k] for k in op if k != 'operand_index'},
                              app_attributions=refs, typed_accesses=typed, unresolved_typed_accesses=unresolved,
                              address_evidence=observations, platform_evidence=platform,
                              concrete_addresses=sorted(addresses), app_offsets=relative,
                              base_address_contradiction=base_contradiction,
                              conditional_app_offsets=conditional,
                              conditional_overlapping_declarations=sorted(set(conditional_overlaps)),
                              conditional_undeclared_intersections=conditional_gap_hits,
                              role=(refs[0]['access'] if len(refs) == 1 else op['access']),
                              role_basis=('native_app_ref' if len(refs) == 1 else 'native_form_operand'),
                              address_only=address_use, footprint_known=footprint_known,
                              footprint_width_bytes=width if footprint_known else None,
                              footprint_source=footprint_source,
                              overlapping_declarations=sorted(set(overlaps)), undeclared_intersections=gap_hits))
    domains = Counter(s['domain'] for s in sites)
    app_sites = [s for s in sites if s['app_attributions'] or s['domain'] == 'physical_app_envelope_alias']
    field_report = []
    for f in fields:
        matches = [s for s in app_sites if f['symbol'] in s['overlapping_declarations']]
        conditional_matches = [s for s in sites if f['symbol'] in s['conditional_overlapping_declarations']]
        field_report.append({**f, 'fixed_footprint_sites': len(matches),
                             'conditional_A6_fixed_sites': len(conditional_matches),
                             'conditional_A6_site_ids': [[s['section_index'], s['source_offset'], s['operand_index']] for s in conditional_matches],
                             'site_ids': [[s['section_index'], s['source_offset'], s['operand_index']] for s in matches]})
    return dict(schema='app-access-audit-v1', identity=identity, app_base=app_base,
                scope='accepted native instructions; static operands, not runtime events', exhaustive_game_usage=False,
                counts=dict(instructions=len(seen), memory_shaped_operand_sites=len(sites), domains=dict(sorted(domains.items())),
                            native_app_attributed_sites=sum(bool(s['app_attributions']) for s in sites),
                            app_related_sites=len(app_sites), app_related_roles=dict(Counter(s['role'] for s in app_sites)),
                            indexed_app_related_sites=sum(s['indexed'] for s in app_sites),
                            indexed_unresolved_A6_sites=sum(s['indexed'] and s['domain'] == 'unresolved_A6' for s in sites),
                            scalar_unresolved_A6_sites=sum(not s['indexed'] and s['domain'] == 'unresolved_A6' for s in sites),
                            unknown_width_sites=sum(not s['width_bytes'] for s in sites),
                            layout_fields=len(fields), alias_fields=sum(bool(f.get('alias')) for f in fields),
                            envelope_bytes=envelope, declared_union_bytes=envelope-sum(g['end']-g['start'] for g in gaps),
                            declaration_gap_bytes=sum(g['end']-g['start'] for g in gaps), declaration_gaps=len(gaps)),
                declarations=field_report, gaps=gaps, sites=sites,
                limits=['Native app refs can use the A6 fallback convention; symbolic attribution is not all-path base proof.',
                        'Concrete address observations retain their native source and conflict flag; they are not execution events.',
                        'Native form roles do not independently enumerate every read side of read-modify-write operations.',
                        'Indexed domains, bulk-transfer footprints, implicit stack accesses and unaccepted/opaque code are not closed.',
                        'Conditional A6 joins assume A6 equals the stated app base; no register-flow proof is added.',
                        'Zero fixed-footprint sites does not mean unused; cursors, indexing and ranges may cover declarations or gaps.',
                        'App envelope overlap is physical alias evidence, not an allocation or ownership boundary.'])


def decode_retained_instruction(data, *, project_root):
    """Use the shared native serializer on one exact retained instruction.

    This is a decoder/evidence projection, not a simulator or base-flow proof.
    It intentionally returns no platform attribution without a target artifact.
    """
    import ctypes as C
    import json
    from amiga_reversing.disasm.c_backend import _platform_file_dll
    dll = _platform_file_dll(project_root)
    fn = dll.platform_file_instruction_evidence_json_alloc
    fn.argtypes = [C.c_void_p, C.c_size_t, C.c_uint8, C.POINTER(C.c_void_p)]
    fn.restype = C.c_int
    output = C.c_void_p()
    buf = C.create_string_buffer(data, len(data)) if data else None
    try:
        if fn(buf, len(data), 0, C.byref(output)) or not output.value:
            raise AuditIncomplete('native decoder refused exact retained instruction')
        return json.loads(C.string_at(output.value))
    finally:
        if output.value:
            dll.platform_file_free_text(output)


def explicit_register_writes(evidence):
    """Project generated operand roles and native register lists/EA updates.

    Callee effects, exception frames and unknown semantic forms are not inferred.
    A CALL here describes only the instruction, not its target body.
    """
    if not evidence['metadata_available']:
        raise AuditIncomplete('native generated form semantics missing')
    writes = set()
    for op in evidence['operand_facts']:
        if op['direct_register'] and op['access'] in {'register_write', 'memory_write'}:
            writes.add(op['direct_register'])
        if op['access'] == 'register_list_write':
            writes.update(op['register_list'])
        if op['base_register'] and op['ea_update']:
            writes.add(op['base_register'])
    return sorted(writes)

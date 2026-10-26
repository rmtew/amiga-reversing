import pytest

from amiga_reversing.disasm.app_access_audit import AuditIncomplete, build_app_access_audit, collect_instruction_pages


FIELDS = [dict(base_symbol='__amiga_app_base__', symbol='counter', offset=4, size=4, alias=False),
          dict(base_symbol='__amiga_app_base__', symbol='counter_low', offset=7, size=1, alias=True)]


def row(offset=0, **changes):
    op = dict(operand_index=0, memory=True, base_register='A6', absolute_address=None,
              displacement=5, displacement_known=True, width_bytes=1, indexed=False,
              bulk_transfer=False, access='memory_read')
    op.update(changes)
    return dict(section_index=0, source_offset=offset, operand_facts=[op])


def audit(*rows):
    return build_app_access_audit(rows, FIELDS, app_base=0x1000, identity={})


def test_attribution_is_not_base_proof_and_alias_fields_are_not_double_counted():
    r = row()
    r['app_slot_refs'] = [dict(operand_index=0, displacement=7, symbol='app_0007', access='read-write')]
    report = audit(r)
    assert report['counts']['declared_union_bytes'] == 4
    site = report['sites'][0]
    assert site['domain'] == 'native_app_attribution'
    assert site['role'] == 'read-write'
    assert site['overlapping_declarations'] == ['counter', 'counter_low']
    assert not report['exhaustive_game_usage']


def test_hardware_and_conflicting_attribution_are_separate():
    r = row()
    r['platform_evidence'] = [dict(operand_index=0, shape='hardware_register_family', effective_address=None,
                                   requires_input_contract=True, relative_base_offsets=[0xa0, 0xb0])]
    assert audit(r)['sites'][0]['domain'] == 'hardware'
    r['app_slot_refs'] = [dict(operand_index=0, displacement=5, symbol='app_0005', access='read')]
    assert audit(r)['sites'][0]['domain'] == 'conflicting_evidence'


def test_absolute_and_cursor_observations_are_physical_aliases_with_gap_intersection():
    absolute = row(absolute_address=0x1002, base_register=None, width_bytes=4)
    cursor = row(offset=2, base_register='A0')
    cursor['address_evidence'] = [dict(operand_index=0, has_address=True, address=0x1007, conflicted=False, source='native')]
    report = audit(absolute, cursor)
    assert report['sites'][0]['undeclared_intersections'] == [dict(start=2, end=4)]
    assert [s['domain'] for s in report['sites']] == ['physical_app_envelope_alias'] * 2


@pytest.mark.parametrize('changes', [dict(indexed=True), dict(bulk_transfer=True), dict(width_bytes=0), dict(access='address')])
def test_uncertain_or_address_only_footprints_do_not_claim_gap_coverage(changes):
    r = row(absolute_address=0x1002, **changes)
    site = audit(r)['sites'][0]
    assert not site['footprint_known']
    assert not site['undeclared_intersections']


def test_unresolved_registers_and_other_record_domains_remain_visible():
    a6, a0, typed, stack = row(), row(2, base_register='A0'), row(4), row(6, base_register='A7')
    typed['typed_accesses'] = [dict(operand_index=0, root_struct_name='AudioChannel')]
    assert [s['domain'] for s in audit(a6, a0, typed, stack)['sites']] == [
        'unresolved_A6', 'unresolved_register_alias', 'other_typed_record', 'stack']


def page(items, offset=0, total=None, **extras):
    return dict(revision='r', items=items, offset=offset, total=total if total is not None else len(items), **extras)


def test_revision_bound_pages():
    pages = iter([page([row()], total=2, next_cursor='next', has_more=True), page([row(2)], offset=1, total=2)])
    calls = []
    def call(*args, **kwargs):
        calls.append(kwargs)
        return next(pages)
    assert len(collect_instruction_pages(call, 'target', 'r')) == 2
    assert calls[1]['cursor'] == 'next'
    assert all(c['expected_revision'] == 'r' for c in calls)


@pytest.mark.parametrize('broken', [dict(revision='stale'), dict(truncated_fields=['items.0']),
                                    dict(total=2), dict(offset=1), dict(items=[row(), row()])])
def test_incomplete_or_stale_pages_fail_closed(broken):
    p = page([row()])
    p.update(broken)
    with pytest.raises(AuditIncomplete):
        collect_instruction_pages(lambda *a, **k: p, 'target', 'r')


def test_concrete_address_contradicts_app_attribution():
    r = row(absolute_address=0x2000)
    r['app_slot_refs'] = [dict(operand_index=0, displacement=5, symbol='app_0005', access='read')]
    site = audit(r)['sites'][0]
    assert site['domain'] == 'conflicting_evidence' and site['base_address_contradiction']


def test_conditional_A6_field_join_is_separate_from_native_attribution():
    r = row(displacement=7)
    report = audit(r)
    site = report['sites'][0]
    assert not site['app_offsets'] and not site['overlapping_declarations']
    assert site['conditional_app_offsets'] == [7]
    assert site['conditional_overlapping_declarations'] == ['counter', 'counter_low']
    assert report['declarations'][0]['fixed_footprint_sites'] == 0
    assert report['declarations'][0]['conditional_A6_fixed_sites'] == 1


def test_saved_evidence_replay_rejects_changed_input(tmp_path):
    import json
    from hashlib import sha256
    from amiga_reversing.tools.pandora_app_access_audit import load_evidence
    rows, nav = [row()], {'app_slot_analysis': {}}
    identity = {key: sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                for value, key in ((rows, 'native_instruction_evidence_sha256'), (nav, 'native_navigation_sha256'))}
    for name, value in [('instructions', rows), ('navigation', nav), ('identity', identity)]:
        (tmp_path / (name + '.json')).write_text(json.dumps(value))
    assert load_evidence(tmp_path) == (rows, nav, identity)
    (tmp_path / 'instructions.json').write_text('[]')
    with pytest.raises(AuditIncomplete, match='differs'):
        load_evidence(tmp_path)


def test_public_report_has_bound_site_file_and_no_original_instruction_bytes(tmp_path):
    import json
    from hashlib import sha256
    from amiga_reversing.tools.pandora_app_access_audit import write_report
    path = tmp_path / 'audit.json'
    write_report(audit(row()), path)
    summary = json.loads(path.read_text())
    details = tmp_path / summary['site_details']['file']
    assert summary['site_details']['sha256'] == sha256(details.read_bytes()).hexdigest()
    assert summary['site_details']['records'] == 1
    assert 'sites' not in summary
    assert 'bytes' not in json.loads(details.read_text())


def test_native_grouped_span_drives_footprint_without_upgrading_base_evidence():
    r = row(base_register='A5', bulk_transfer=True, width_bytes=2)
    r['app_slot_refs'] = [dict(operand_index=0, displacement=4, symbol='counter', access='read',
        derived=True, base_displacement=4, operand_displacement=0, data_access_size=4,
        element_width=2, transfer_count=2, base_evidence='a6_fallback')]
    site = audit(r)['sites'][0]
    assert site['domain'] == 'native_app_attribution'
    assert site['width_bytes'] == 2 and site['footprint_width_bytes'] == 4
    assert site['footprint_known'] and site['footprint_source'] == 'native_derived_span'
    assert site['overlapping_declarations'] == ['counter', 'counter_low']
    assert site['app_attributions'][0]['base_evidence'] == 'a6_fallback'


@pytest.mark.parametrize('mutation', [dict(data_access_size=6), dict(element_width=4),
    dict(transfer_count=0), dict(transfer_count=True), dict(derived=False), dict(access='address')])
def test_malformed_or_unbound_grouped_span_remains_unknown(mutation):
    r = row(base_register='A5', bulk_transfer=True, width_bytes=2)
    ref = dict(operand_index=0, displacement=4, symbol='counter', access='read', derived=True,
        data_access_size=4, element_width=2, transfer_count=2, base_evidence='a6_fallback')
    ref.update(mutation)
    r['app_slot_refs'] = [ref]
    site = audit(r)['sites'][0]
    assert not site['footprint_known']
    assert site['footprint_width_bytes'] is None
    assert not site['overlapping_declarations']


@pytest.mark.parametrize('stride', [6, -6])
def test_iterated_native_span_preserves_holes_and_counter_evidence(stride):
    fields = [dict(base_symbol='__amiga_app_base__', symbol=s, offset=o, size=n, alias=False)
              for s, o, n in [('first', 0, 2), ('untouched', 2, 4), ('second', 6, 2)]]
    r = row(base_register='A5', width_bytes=2)
    r['app_slot_refs'] = [dict(operand_index=0, displacement=0 if stride > 0 else 6,
        symbol='first', access='read', derived=True, data_access_size=2, element_width=2, transfer_count=1,
        base_evidence='a6_fallback', loop_iteration_count=2, loop_iteration_stride=stride,
        loop_header_offset=0, loop_tail_offset=4, loop_counter_register='D7')]
    site = build_app_access_audit([r], fields, app_base=0x1000, identity={})['sites'][0]
    assert site['footprint_known'] and site['footprint_span_bytes'] == 8
    assert site['footprint_iteration_count'] == 2
    assert site['overlapping_declarations'] == ['first', 'second']
    assert not site['undeclared_intersections'] and not site['undeclared_intersection_patterns']
    assert site['app_attributions'][0]['base_evidence'] == 'a6_fallback'


@pytest.mark.parametrize('mutation', [dict(loop_iteration_count=0), dict(loop_iteration_count=True),
    dict(loop_iteration_count=65537), dict(loop_counter_register='A0'), dict(loop_tail_offset=0),
    dict(loop_iteration_stride='6'), dict(data_access_size=3)])
def test_invalid_native_iteration_pattern_cannot_fall_back_to_scalar_coverage(mutation):
    r = row(base_register='A5', width_bytes=2)
    ref = dict(operand_index=0, displacement=4, symbol='counter', access='read', derived=True,
        data_access_size=2, element_width=2, transfer_count=1, base_evidence='a6_fallback',
        loop_iteration_count=2, loop_iteration_stride=2, loop_header_offset=0,
        loop_tail_offset=4, loop_counter_register='D7')
    ref.update(mutation)
    r['app_slot_refs'] = [ref]
    assert not audit(r)['sites'][0]['footprint_known']


def test_strided_intersection_is_compressed_not_filled_in():
    from amiga_reversing.disasm.app_access_audit import _pattern_intersection
    result = _pattern_intersection(0, 2, 65536, 6, 0, 400000)
    assert result['first_start'] == 0 and result['last_start'] == 393210
    assert result['count'] == 65536 and result['transfer_width'] == 2
    assert 'start' not in result  # Four-byte holes are not reported as touched.

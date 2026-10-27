"""Discovery joins retain native domains; suffixes never admit semantic facts."""
from copy import deepcopy
from amiga_reversing.tools.source_gap_inventory import inventory


def test_suffix_names_distinguish_code_storage_and_literal_text():
    section = dict(section_index=0, accepted_code_runs=[dict(start_offset=0, end_offset=4)],
                   rendered_symbol_accesses=[
                       dict(symbol_name=name, offset=offset, access_kind='label_statement')
                       for name, offset in [('initialize_pointers', 0), ('sprite_bases', 8), ('message_base', 16)]])
    analysis = dict(sections=[section], base_layout_fields=[dict(symbol='draw_buffer_base', offset=4)],
                    analysis_policy=dict(structured_data_items=[dict(label='message_base', kind=4)]))
    section['rendered_symbol_accesses'].append(dict(symbol_name='draw_buffer_base', offset=4, access_kind='equate'))
    result = inventory(analysis, {}, 'initialize_pointers:\nsprite_bases:\nmessage_base:\ndraw_buffer_base EQU 4\n')
    rows = {r['name']: r for r in result['named_signals']}
    assert rows['initialize_pointers']['disposition'] == 'code_name_signal'
    assert rows['message_base']['disposition'] == 'text_name_signal'
    assert rows['draw_buffer_base']['disposition'] == 'named_base_layout_storage'
    assert rows['sprite_bases']['disposition'] == 'named_source_storage'
    assert all(r['exported_definition'] for r in rows.values())


def test_native_interior_identity_rescan_detects_exact_child_label():
    owner = dict(section_index=0, offset=8, size=8, kind=1, label='pool')
    analysis = dict(analysis_policy=dict(structured_data_items=[owner]),
                    sections=[dict(section_index=0, rendered_symbol_accesses=[
        dict(symbol_name='pool', offset=8, access_kind='label_statement'),
        dict(symbol_name='pool', offset=0, access_kind='operand', target_section_index=0, target_offset=10),
        # Hardware/runtime domain is not a source parent/addend.
        dict(symbol_name='hardware', offset=4, access_kind='operand', target_section_index=None, target_offset=10),
    ])])
    before = inventory(analysis, {}, '')
    assert before['interior_references'] == [dict(section_index=0, source_offset=0, operand_index=None,
                                                symbol='pool', base_source_offset=8, target_source_offset=10,
                                                addend=2, evidence='native_rendered_target_identity',
                                                canonical_layout_id=None, target_policy_item_ids=['policy:0'])]
    assert before['canonical_policy_items']['policy:0'] == owner
    changed = deepcopy(analysis)
    refs = changed['sections'][0]['rendered_symbol_accesses']
    refs[1]['symbol_name'] = 'str_child'
    refs.append(dict(symbol_name='str_child', offset=10, access_kind='label_statement'))
    assert inventory(changed, {}, '')['interior_references'] == []


def test_field_holes_not_conflated_with_inheritance_or_zero_width():
    metadata = dict(custom_structs=[dict(name='R', size=8, fields=[dict(offset=0, size=2), dict(offset=4, size=4)]),
                                   dict(name='Derived', size=8, base_struct='R', fields=[])])
    accesses = [dict(root_struct_name=root, displacement=offset, access_size=width, classification='field_gap')
                for root, offset, width in [('R', 2, 2), ('R', 4, 2), ('R', 8, 2), ('R', 0, 0), ('Derived', 0, 2)]]
    analysis = dict(sections=[dict(section_index=0, recovered_platform_unresolved_typed_accesses=accesses)])
    result = inventory(analysis, metadata, '')
    assert [r['mechanism'] for r in result['unresolved_typed_accesses']] == [
        'declared_field_hole', 'covered_partial_or_composite_access', 'outside_declared_record',
        'address_formation_or_unknown_width', 'requires_native_inheritance_projection']


def test_pointer_array_contract_requires_canonical_type_and_exact_extent():
    pointer = dict(offset=0, size=4, value_kind='target_pointer', pointer_address_domain='mapped_source')
    metadata = dict(custom_structs=[dict(name='Ref', size=4, fields=[pointer])], data_block_layouts=[
        dict(layout_id='L', name='name_pointers', hunk=0, source_start=100, source_end=112,
             elements=[dict(offset=0, width=12, array_count=3, array_stride=4,
                            type_binding=dict(bound_type_id='Ref'))])])
    analysis = dict(sections=[dict(section_index=0)], analysis_policy=dict(structured_data_items=[
        dict(section_index=0, offset=offset, size=4, has_target=True) for offset in [100, 104, 108]]))
    result = inventory(analysis, metadata, '')
    assert result['pointer_record_arrays'][0]['mechanism'] == 'canonical_array_projected_as_leaves'
    assert result['pointer_record_arrays'][0]['native_leaf_items'] == 3
    assert result['pointer_record_arrays'][0]['bound_targets'] == 3
    analysis['sections'][0]['table_descriptors'] = [dict(start_offset=100, end_offset=112, table_kind='pointer')]
    assert inventory(analysis, metadata, '')['pointer_record_arrays'][0]['mechanism'] == 'collection_contract_exposed'
    scalar = deepcopy(metadata)
    scalar['custom_structs'][0]['fields'][0]['value_kind'] = 'scalar'
    assert inventory(analysis, scalar, '')['pointer_record_arrays'] == []
    bad_stride = deepcopy(metadata)
    bad_stride['data_block_layouts'][0]['elements'][0]['array_stride'] = 8
    assert inventory(analysis, bad_stride, '')['pointer_record_arrays'] == []


def test_generic_base_field_retains_fallback_and_separate_offset_domain():
    field = dict(layout_name='app', base_symbol='APP', symbol='app_0203', offset=515, size=1)
    access = dict(symbol_name='app_0203', offset=10, displacement=515, access='write', base_evidence='a6_fallback')
    analysis = dict(base_layout_fields=[field], sections=[dict(section_index=0, app_slot_refs=[access])])
    report = inventory(analysis, {}, '')
    assert report['summary']['generic_base_symbols'] == 1
    row = report['generic_base_fields'][0]
    assert row['domain'] == 'base_layout' and row['field']['offset'] == 515
    assert row['app_accesses'][0]['offset'] == 10
    assert row['app_accesses'][0]['base_evidence'] == 'a6_fallback'
    assert not report['named_signals']


def test_collection_consumers_keep_instruction_section_and_exact_table_identity():
    pointer = dict(offset=0, size=4, value_kind='target_pointer')
    metadata = dict(custom_structs=[dict(name='Ref', size=4, fields=[pointer])], data_block_layouts=[
        dict(layout_id='L', name='names', hunk=0, source_start=100, source_end=112,
             elements=[dict(offset=0, width=12, array_count=3, type_binding=dict(bound_type_id='Ref'))])])
    consumer = dict(consumer_offset=8, table_section_index=0, table_start_offset=100, table_end_offset=112,
                    index_mask_domain=None, index_compare_domain=None, index_loop_domain=None)
    other_domain = {**consumer, 'table_section_index': 1}
    other_extent = {**consumer, 'table_end_offset': 108}
    analysis = dict(sections=[dict(section_index=0, table_descriptors=[
        dict(start_offset=100, end_offset=112, table_kind='pointer')]),
        dict(section_index=1, table_consumers=[consumer, other_domain, other_extent])])
    report = inventory(analysis, metadata, '')
    row = report['pointer_record_arrays'][0]
    assert row['native_collection_consumers'] == [dict(section_index=1, **consumer)]
    assert row['mechanism'] == 'collection_contract_exposed'
    assert row['native_collection_consumers'][0]['index_mask_domain'] is None
    assert report['summary']['native_table_contracts'] == 1
    assert report['summary']['native_table_consumer_records'] == 3

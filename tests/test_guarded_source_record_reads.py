"""Branch predicates refine correlated source records, never equal-looking domains."""
from contextlib import contextmanager
import json

import pytest

from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource


SELECT = '''tst.w d7
 beq.w other
 lea.l base(pc),a0
 bra.w joined
other:
 lea.l extended(pc),a0
joined:
'''


@contextmanager
def records(tmp_path, body, *, prefix=SELECT, base_count=0, child_count=1, conflicting=False, independent_entry=None, record_array=False):
    prefix_size, base_size, child_size = (2, 4, 12) if record_array else (4, 4, 8)
    data = (f'base:\n dc.w {base_count},{base_count}\nextended:\n'
            f' dc.w {child_count}\n dc.l 123\n dc.w {child_count}\n dc.l 456\n') if record_array else (
            f'base:\n dc.w {base_count},9\nextended:\n dc.w {child_count},8\n dc.l 123\n')
    text = (' SECTION code,code\n ORG $1000\n ' + prefix + body + '\n rts\n'
            'safe_stack:\n dcb.b 32,0\nsafe_stack_end:\n' + data)
    original, _ = cb.assemble_platform_source_text_with_c_backend('amiga-raw', text)
    path = tmp_path / 'input.bin'
    path.write_bytes(original)
    base, child = len(original) - base_size - child_size, len(original) - child_size
    metadata = dict(target_type='program', entry_register_seeds=[], custom_structs=[
        dict(name='Header', size=prefix_size, fields=[
            dict(name='count', type='WORD', offset=0, size=2)] + ([] if record_array else [
            dict(name='flags', type='WORD', offset=2, size=2)])),
        dict(name='ExtendedHeader', size=prefix_size+4, base_struct='Header', base_offset=prefix_size, fields=[
            dict(name='extra', type='LONG', offset=prefix_size, size=4)])], seeded_entities=[
        dict(addr=base, end=base+base_size, hunk=0, name='base_header', type='data', unit='word', struct_name='Header'),
        dict(addr=child, end=child+child_size, hunk=0, name='extended_header', type='data', unit='word', struct_name='ExtendedHeader')])
    if independent_entry is not None:
        metadata['seeded_code_entrypoints'] = [dict(hunk=0, addr=independent_entry)]
    if conflicting:
        metadata['custom_structs'].append(dict(name='Other', size=8, fields=[
            dict(name='different', type='LONG', offset=0, size=4)]))
        metadata['seeded_entities'].append(dict(addr=child, end=child+8, hunk=0,
            name='conflicting_header', type='data', unit='word', struct_name='Other'))
    mp = tmp_path / 'metadata.json'
    mp.write_text(json.dumps(metadata))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000, entrypoint=0x1000,
        code_start_offset=0, display_path=str(path), analysis_cache_path=tmp_path / 'analysis')
    artifact = cb.build_listing_artifact_profile_from_binary_source(source, metadata_path=mp)[2]
    try:
        payload = artifact.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        inline = artifact.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw', inline)[0] == original
        yield payload['sections'][0], inline
    finally:
        artifact.close()


def extra_reads(section):
    rows = [r for r in section['recovered_platform_typed_accesses'] if r['field_name'] == 'extra']
    sites = {(r['offset'], r['operand_index']) for r in rows}
    assert not any((r['offset'], r['operand_index']) in sites
                   for r in section['recovered_platform_unresolved_typed_accesses'])
    return rows


@pytest.mark.parametrize('load,between,test,read', [
    ('move.w (a0),d0', '', 'tst.w d0', '4(a0)'),
    ('move.w (a0),d0', '', '', '4(a0)'),  # MOVE defines the tested Z too.
    ('move.w (a0),d0', '', 'cmp.w #0,d0', '4(a0)'),
    ('move.w (a0),d0', 'move.w d0,d1\n moveq.l #7,d0', 'tst.w d1', '4(a0)'),
    ('move.w (a0),d0', 'move.l d0,d1\n moveq.l #7,d0', 'tst.w d1', '4(a0)'),
    ('move.w (a0),d0', 'movea.l a0,a2', 'tst.w d0', '4(a2)'),
    ('move.w (a0)+,d0', '', 'tst.w d0', '2(a0)'),
    ('move.w (a0),d0', 'move.l d0,-(a7)\n moveq.l #7,d0\n move.l (a7)+,d1', 'tst.w d1', '4(a0)'),
    ('move.w (a0),d0', 'move.l a0,-(a7)', 'tst.w d0', '4(a0)'),
])
def test_nonzero_field_selects_existing_extended_record(tmp_path, load, between, test, read):
    body = f'lea.l safe_stack_end(pc),a7\n {load}\n {between}\n {test}\n beq.w done\n move.l {read},d2\ndone:\n'
    with records(tmp_path, body) as (section, inline):
        refs = extra_reads(section)
        assert len(refs) == 1
        assert refs[0]['root_struct_name'] == 'ExtendedHeader'
        assert 'ExtendedHeader_extra' in inline


@pytest.mark.parametrize('between,test,options', [
    ('move.w #1,(a0)', 'tst.w d0', {}),
    ('move.b #1,(a0)', 'tst.w d0', {}),
    ('move.w #1,(a3)', 'tst.w d0', {}),
    ('jsr (a3)', 'tst.w d0', {}),
    ('move.b #1,d0', 'tst.w d0', {}),
    ('addq.w #1,d0', 'tst.w d0', {}),
    ('', 'tst.b d0', {}),
    ('', 'tst.l d0', {}),
    ('', 'tst.w d1', {}),
    ('lea.l base(pc),a0', 'tst.w d0', {}),
    ('', 'tst.w d0', dict(base_count=1)),  # No type-tag invariant is invented.
])
def test_mutation_partial_values_calls_and_stale_roots_refuse(tmp_path, between, test, options):
    body = f'move.w (a0),d0\n {between}\n {test}\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body, **options) as (section, inline):
        assert not extra_reads(section)
        assert 'ExtendedHeader_extra(a0)' not in inline


def test_same_candidate_set_is_not_same_selected_record(tmp_path):
    independent = '''tst.w d6
 beq.w second
 lea.l base(pc),a2
 bra.w second_join
second:
 lea.l extended(pc),a2
second_join:
'''
    body = independent + 'move.w (a0),d0\n beq.w done\n move.l 4(a2),d2\ndone:\n'
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


def test_replacing_root_with_same_domain_does_not_reuse_old_read(tmp_path):
    replace = SELECT.replace('d7', 'd6').replace('other', 'new_other').replace('joined', 'new_joined')
    body = 'move.w (a0),d0\n' + replace + 'tst.w d0\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


@pytest.mark.parametrize('between,read', [
    ('movea.w d0,a2\n move.w a2,d1\n moveq.l #7,d0\n tst.w d1', '4(a0)'),
    ('movem.l d0/a0,-(a7)\n moveq.l #7,d0\n lea.l base(pc),a0\n movem.l (a7)+,d1/a2\n tst.w d1', '4(a2)'),
    ('move.l a0,-(a7)\n tst.w d0\n beq.w done\n lea.l base(pc),a0\n movea.l (a7)+,a2\n tst.w d0', '4(a2)'),
])
def test_correlations_use_shared_register_and_stack_transfers(tmp_path, between, read):
    body = f'lea.l safe_stack_end(pc),a7\n move.w (a0),d0\n {between}\n beq.w done\n move.l {read},d2\ndone:\n'
    with records(tmp_path, body) as (section, _):
        assert len(extra_reads(section)) == 1


@pytest.mark.parametrize('between', [
    'move.l d0,d1',  # LONG flags also depend on D0's unknown upper WORD.
    'move.l d0,-(a7)\n moveq.l #7,d0\n move.l (a7)+,d1\n tst.w d1',  # Unknown SP may alias the records.
    'pea (a3)\n tst.w d0',  # Unmodelled implicit stack write.
    'link.w a6,#-8\n tst.w d0',
])
def test_wide_flags_and_unowned_stack_effects_refuse(tmp_path, between):
    with records(tmp_path, f'move.w (a0),d0\n {between}\n beq.w done\n move.l 4(a0),d2\ndone:\n') as (section, _):
        assert not extra_reads(section)


def test_partial_write_to_saved_scalar_cannot_restore_its_relation(tmp_path):
    body = '''lea.l safe_stack_end(pc),a7
 move.w (a0),d0
 move.l d0,-(a7)
 moveq.l #7,d0
 move.b #1,1(a7)
 move.l (a7)+,d1
 tst.w d1
 beq.w done
 move.l 4(a0),d2
done:
'''
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


def test_join_of_different_predicates_refuses(tmp_path):
    body = '''move.w (a0),d0
 tst.w d6
 beq.w other_flags
 tst.w d0
 bra.w flags_join
other_flags:
 tst.w d1
flags_join:
 beq.w done
 move.l 4(a0),d2
done:
'''
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


@pytest.mark.parametrize('previous', [False, True])
def test_loop_repeated_read_does_not_reuse_an_earlier_iteration(tmp_path, previous):
    # Read the same site repeatedly; the tested scalar is either this read or
    # a saved prior iteration. Equal site/domain IDs alone do not make them equal.
    body = f'''move.w (a0),d1
 tst.w {'d0' if previous else 'd1'}
 beq.w next
 move.l 4(a0),d2
next:
 move.w d1,d0
 dbf d6,loop
'''
    prefix = 'moveq.l #0,d0\nloop:\n' + SELECT
    with records(tmp_path, body, prefix=prefix) as (section, _):
        assert bool(extra_reads(section)) is (not previous)


def test_zero_branch_can_select_the_extended_record_without_tag_guessing(tmp_path):
    body = 'move.w (a0),d0\n bne.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body, base_count=3, child_count=0) as (section, _):
        assert len(extra_reads(section)) == 1


def test_conflicting_source_record_ownership_refuses(tmp_path):
    body = 'move.w (a0),d0\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body, conflicting=True) as (section, _):
        assert not extra_reads(section)


def test_preceding_mutation_prevents_original_byte_binding(tmp_path):
    body = 'move.w #1,(a0)\n move.w (a0),d0\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


def test_implicit_stack_effect_before_the_read_prevents_original_byte_binding(tmp_path):
    body = 'pea (a3)\n move.w (a0),d0\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


def test_direct_memory_test_and_flag_preserving_gap(tmp_path):
    body = 'tst.w (a0)\n nop\n lea.l base(pc),a3\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    with records(tmp_path, body) as (section, _):
        assert len(extra_reads(section)) == 1


def test_join_keeps_a_scalar_relation_only_when_both_paths_copy_it(tmp_path):
    body = '''move.w (a0),d0
 tst.w d6
 beq.w word_copy
 move.l d0,d1
 bra.w copied
word_copy:
 move.w d0,d1
copied:
 tst.w d1
 beq.w done
 move.l 4(a0),d2
done:
'''
    with records(tmp_path, body) as (section, _):
        assert len(extra_reads(section)) == 1


def test_known_disjoint_cell_keeps_local_relation_without_global_writer_seeding(tmp_path):
    body = '''move.w (a0),d0
 lea.l safe_stack(pc),a3
 move.l d0,(a3)
 moveq.l #7,d0
 move.l (a3),d1
 tst.w d1
 beq.w done
 move.l 4(a0),d2
done:
'''
    with records(tmp_path, body) as (section, _):
        assert len(extra_reads(section)) == 1


def test_partial_write_to_local_cell_drops_scalar_relation(tmp_path):
    body = '''move.w (a0),d0
 lea.l safe_stack(pc),a3
 move.l d0,(a3)
 moveq.l #7,d0
 move.b #1,1(a3)
 move.l (a3),d1
 tst.w d1
 beq.w done
 move.l 4(a0),d2
done:
'''
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


def test_join_does_not_conflate_two_field_read_identities(tmp_path):
    body = '''tst.w d6
 beq.w read_flags
 move.w (a0),d0
 bra.w read_join
read_flags:
 move.w 2(a0),d0
read_join:
 tst.w d0
 beq.w done
 move.l 4(a0),d2
done:
'''
    with records(tmp_path, body) as (section, _):
        assert not extra_reads(section)


def test_independent_entry_has_no_unchanged_source_snapshot_contract(tmp_path):
    body = 'move.w (a0),d0\n beq.w done\n move.l 4(a0),d2\ndone:\n'
    # The initial program skips this exposed entry. Its LEAs recover the same
    # source addresses, but invocation does not promise unchanged record bytes.
    prefix = 'bra.w done\n' + SELECT
    with records(tmp_path, body, prefix=prefix, independent_entry=4) as (section, _):
        assert not extra_reads(section)


def test_advancing_to_another_array_record_cannot_keep_the_previous_relation(tmp_path):
    # The joined prefix has a different stride from its derived array. Even a
    # bounded cursor transition cannot bind the next record to the earlier read.
    body = 'move.w (a0)+,d0\n tst.w d0\n beq.w done\n move.l 2(a0),d2\ndone:\n'
    with records(tmp_path, body, record_array=True) as (section, _):
        assert not extra_reads(section)

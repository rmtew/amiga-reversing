"""Pointer-string discovery uses encoded addresses, never numeric containment."""
import json
from pathlib import Path
import pytest
from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from amiga_reversing.disasm.manual_actions import append_manual_actions, ManualActionKind as Kind
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('mode', ['small', 'large', 'local_numbers', 'ambiguous', 'duplicate', 'owned', 'suffix'])
def test_pointer_table_text_preserves_address_domain_and_ownership(tmp_path, mode):
    asm = ''' SECTION code,code
 ORG $1000
 lea.l table(pc),a0
 movea.l 0(a0,d0.w),a1
 rts
 table: dc.l first,second,third,0
 first: dc.b " ...leading alpha",0
 second: dc.b " second beta",0
 third: dc.b "third gamma",0
''' + (' dcb.b $1200,0\n' if mode != 'small' else '')
    raw, _ = cb.assemble_platform_source_text_with_c_backend('amiga-raw', asm)
    table, first, second, third = 10, 26, 44, 57
    assert [int.from_bytes(raw[table+4*i:table+4*i+4], 'big') for i in range(3)] == [
        0x1000+first, 0x1000+second, 0x1000+third]
    if mode in ('local_numbers', 'suffix'):
        changed = bytearray(raw)
        for i in range(3):
            value = int.from_bytes(raw[table+4*i:table+4*i+4], 'big')
            value = value-0x1000 if mode == 'local_numbers' else value+int(i == 0)
            changed[table+4*i:table+4*i+4] = value.to_bytes(4, 'big')
        raw = bytes(changed)
    binary = tmp_path/'text.bin'; binary.write_bytes(raw)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x1000,
        entrypoint=0x1000, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    seeds = [dict(seed_id='table', kind='data', mode='required', hunk=0,
        addr=table, end=table+16, name='directory', data_role='pointer_table', unit='long')]
    if mode == 'owned':
        seeds.append(dict(seed_id='opaque', kind='data', mode='required', hunk=0,
            addr=first, end=third, name='opaque_record', data_role='raw', unit='byte'))
    append_manual_actions(tmp_path, binary_source=source, actions=[
        (Kind.CREATE_MANUAL_SEED, {'seed': seed}) for seed in seeds])
    with effective_metadata_file(tmp_path) as metadata:
        if mode in ('ambiguous', 'duplicate'):
            # Native pointer-only aliases do not create alternate code entries.
            policy = json.loads(Path(metadata).read_text())
            policy['execution_views'] = [dict(source_start=start, source_end=len(raw),
                base_addr=0x1000, runtime_view_use='pointer_target')
                for start in [0, 1 if mode == 'ambiguous' else 0]]
            metadata = tmp_path/'pointer-mappings.json'; metadata.write_text(json.dumps(policy))
        artifact = cb.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]
    try:
        payload = artifact.analysis_payload()[0]
        assert not payload['incomplete_analysis']
        offsets = {i['offset'] for i in payload['analysis_policy']['structured_data_items']
                   if i.get('source_pattern') == 'pointer_string_table'}
        if mode in ('local_numbers', 'ambiguous', 'owned'):
            assert not offsets
        elif mode == 'suffix':
            assert first not in offsets and {first+1, second} <= offsets
        else:
            assert {first, second} <= offsets
        text = artifact.inline_source_text_with_profile()[0]
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw', text)[0] == raw
        _assert_vasm_bytes(tmp_path, text, raw)
    finally:
        artifact.close()

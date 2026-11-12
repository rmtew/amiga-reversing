"""An inferred owner/addend must not hide an exact authored data boundary."""
import pytest

from amiga_reversing.disasm import c_backend as cb
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind, append_manual_actions
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata
from tests.test_typed_pointer_domains import _assert_vasm_bytes


@pytest.mark.parametrize('load', [0, 0x1000])
@pytest.mark.parametrize('named', [False, True])
@pytest.mark.parametrize('interior_delta', [0, 2])
def test_exact_data_name_precedes_inferred_owner_expression(tmp_path, load, named, interior_delta):
    raw, _ = cb.assemble_platform_source_text_with_c_backend('amiga-raw', f'''
 SECTION code,code
 ORG ${load:x}
owner: dcb.b 16,$81
point: dcb.b 8,$82
entry: lea.l point+{interior_delta}(pc),a0
 rts
''')
    path = tmp_path/'input.bin'; path.write_bytes(raw)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=path,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=load,
        entrypoint=load+24, code_start_offset=24, display_path=str(path),
        analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    actions = [(ManualActionKind.CREATE_MANUAL_SEED, {'seed': dict(
        seed_id='owner', kind='data', mode='required', hunk=0, addr=0,
        end=24, name='opaque_owner', unit='byte')})]
    if named:
        actions.append((ManualActionKind.RENAME_DATA_SYMBOL, {'data_symbol': dict(
            hunk=0, addr=16, name='named_buffer')}))
    append_manual_actions(tmp_path, actions=actions, binary_source=source)
    with effective_metadata_file(tmp_path) as metadata:
        a = cb.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]
    try:
        text = a.inline_source_text_with_profile()[0]
        if named and interior_delta == 0:
            assert '\tlea.l named_buffer(pc),a0\n' in text
            assert 'named_buffer:\n' in text
        else:
            owner = 'opaque_owner' if load == 0 else f'abs_0_{load:08X}'
            assert f'\tlea.l {owner}+{16+interior_delta}(pc),a0\n' in text
        assert cb.assemble_platform_source_text_with_c_backend('amiga-raw', text)[0] == raw
        _assert_vasm_bytes(tmp_path, text, raw)
    finally:
        a.close()

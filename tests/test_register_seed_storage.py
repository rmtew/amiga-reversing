"""Native policy transport must retain entry contexts beyond its inline buffer."""
import json
from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource


def test_native_register_contexts_survive_growth_and_policy_roundtrip(tmp_path):
    binary = tmp_path / 'source.bin'
    binary.write_bytes(bytes.fromhex('4e75') * 300)
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.LOCAL_OFFSET, load_address=0, entrypoint=0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path / 'cache')
    seeds = [dict(hunk=0, entry_offset=i*2, register='A0', kind='struct_ptr', struct_name='Header', note='header',
                  context_name=f'phase_{i}') for i in range(262)]
    metadata = tmp_path / 'target_metadata.json'
    metadata.write_text(json.dumps(dict(target_type='raw_binary', custom_structs=[
        dict(name='Header', size=2, fields=[dict(name='value', type='WORD', offset=0, size=2)])],
        entry_register_seeds=seeds)))
    result = c_backend.effective_policy_project_source_with_c_backend(source, metadata_path=metadata)['analysis_policy']
    contexts = result['register_seeds']
    assert len(contexts) == len(seeds)
    assert [s['entry_offset'] for s in contexts] == [s['entry_offset'] for s in seeds]
    assert contexts[-1]['context_name'] == 'phase_261'

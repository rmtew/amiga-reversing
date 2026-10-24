"""Frozen source identities and generated encoding coordinates, not patch guesses."""
import json
from pathlib import Path
from amiga_reversing.disasm.binary_source import BinarySourceKind,RawAddressModel,RawBinarySource
from amiga_reversing.disasm.c_backend import build_listing_artifact_profile_from_binary_source


def test_native_inventory_retains_source_targets_and_encoder_fields(tmp_path):
    data=bytes.fromhex('20790001000c41fa00044e750001000000010000')
    binary=tmp_path/'input.bin';binary.write_bytes(data)
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x10000,
        entrypoint=0x10000,code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    metadata=dict(seeded_entities=[dict(addr=12,end=16,hunk=0,unit='long',name='pointer',
        struct_name='Record',field_name='source',field_type='long',value_kind='target_pointer'),
        dict(addr=16,end=20,hunk=0,unit='long',name='scalar')])
    path=tmp_path/'metadata.json';path.write_text(json.dumps(metadata))
    _,_,artifact=build_listing_artifact_profile_from_binary_source(source,metadata_path=path)
    try:
        complete=artifact.query_payload('expressions',limit=100)
        expressions=complete['items']
        first=artifact.query_payload('expressions',limit=1)
        second=artifact.query_payload('expressions',offset=1,limit=1)
        assert first['total']==second['total']==complete['total']==len(expressions)
        assert len(first['items'])==len(second['items'])==1 and first['has_more']
        assert first['items']+second['items']==expressions[:2]
        incoming=artifact.query_payload('expressions',section_index=0,source_offset=12,direction='incoming',limit=100)
        assert incoming['items'] and all(e['has_target'] and e['target_offset']==12 for e in incoming['items'])
        absolute=next(e for e in expressions if e['kind']==1 and e['source_offset']==0 and e['operand_index']==0)
        assert absolute['has_target'] and absolute['target_section_index']==0 and absolute['target_offset']==12
        field=absolute['instruction_field']
        assert field['absolute'] and field['extension_offset']==2 and field['extension_bytes']==4
        assert field['original_encoder_matches'] and field['instruction_bytes']==6
        relative=next(e for e in expressions if e['kind']==1 and e['source_offset']==6 and e['operand_index']==0)
        assert relative['has_target'] and relative['target_offset']==12
        assert relative['instruction_field']['extension_bytes']==2
        assert not relative['instruction_field']['absolute']
        pointer=next(e for e in expressions if e['source_offset']==12 and e['kind'] in (3,4))
        assert pointer['has_target'] and pointer['target_offset']==0 and pointer['pointer_width']==4
        assert not any(e['source_offset']==16 and e['kind'] in (3,4) for e in expressions)
    finally:artifact.close()

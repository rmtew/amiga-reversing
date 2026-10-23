"""Canonical identities keep operand presentation, copied views and xrefs aligned."""
import json
import subprocess
from pathlib import Path

import pytest

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.manual_actions import ManualActionKind as Kind, append_manual_actions, manual_action_log_path
from amiga_reversing.disasm.target_metadata import TargetMetadata, write_target_metadata


def fixture(tmp_path, copied=False, tail_size=4):
    value = 0x10008 if copied else 8
    binary = tmp_path / 'image.bin'
    binary.write_bytes(bytes.fromhex('0480')+value.to_bytes(4, 'big')+bytes.fromhex('4e7512345678'))
    if tail_size != 4:
        binary.write_bytes(binary.read_bytes()[:8]+bytes((i*17+3)&255 for i in range(tail_size)))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE if copied else RawAddressModel.LOCAL_OFFSET,
        load_address=0x10000 if copied else 0, entrypoint=0x10000 if copied else 0,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path, TargetMetadata(target_type='program', entry_register_seeds=()))
    append_manual_actions(tmp_path, binary_source=source, actions=[(Kind.CREATE_MANUAL_LABEL,
        {'label': dict(label_id='bank', hunk=0, addr=8, name='tile_bank', scope='global', address_domain='source')})])
    return source, value


def representation(value, symbol='tile_bank', width=4):
    return (Kind.CREATE_MANUAL_REPRESENTATION, {'representation': dict(representation_id='selected',
        hunk=0, addr=0, end=6, element_kind='immediate', operand_index=0, style='symbol',
        value=value, width_bytes=width, symbol=symbol)})


def artifact_for(tmp_path, source):
    with effective_metadata_file(tmp_path) as metadata:
        return c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)[2]


@pytest.mark.parametrize('copied', [False, True])
def test_source_identity_roundtrip_and_native_xref(tmp_path, copied):
    source, value = fixture(tmp_path, copied)
    records = append_manual_actions(tmp_path, binary_source=source, actions=[representation(value)])
    identity = records[0]['representation']['source_symbol']
    assert identity == dict(section_index=0, source_offset=8, runtime_view=int(copied), encoded_value=value)
    artifact = artifact_for(tmp_path, source)
    try:
        text = artifact.source_projection_with_profile()[0]
        assert 'subi.l #tile_bank,d0' in text
        refs = artifact.query_payload('references', symbol='tile_bank')['items']
        assert any(r['source_offset'] == 0 and r['target_offset'] == 8 for r in refs)
        rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend('amiga-raw', text)
        assert rebuilt == source.path.read_bytes()
        root = Path(__file__).resolve().parents[1]
        asm, output = tmp_path/'rendered.s', tmp_path/'vasm.bin'
        asm.write_text(text)
        subprocess.run([str(root/'ext/vasm/vasmm68k_mot'),'-quiet','-Fbin','-m68000',
            '-o',str(output),str(asm)],capture_output=True,check=True)
        assert output.read_bytes() == source.path.read_bytes()
    finally:
        artifact.close()


@pytest.mark.parametrize('symbol,value,width', [('missing',8,4), ('tile_bank',9,4), ('tile_bank',8,0),
                                               ('tile_bank',0x10008,2)])
def test_bad_source_selection_refused_before_history_append(tmp_path, symbol, value, width):
    source, _ = fixture(tmp_path)
    before = manual_action_log_path(tmp_path).read_bytes()
    with pytest.raises(ValueError, match='canonical|encoded value|decoded value'):
        append_manual_actions(tmp_path, binary_source=source, actions=[representation(value,symbol,width)])
    assert manual_action_log_path(tmp_path).read_bytes() == before


COPIED_BOOTSTRAP_PREFIX = """ SECTION section,code
start:
 lea.l stage2(pc),a0
 lea.l start(pc),a1
 lea.l $300.w,a2
 moveq.l #47,d0
copy_stage2:
 move.b (a0)+,(a2)+
 dbf.w d0,copy_stage2
 jmp $300.w
stage2:
 lea.l $10000.l,a2
 lea.l $10050.l,a3
 move.l #$62,d0
 cmpa.l a2,a1
 bcs.b forward
 adda.l d0,a1
 adda.l d0,a2
backward:
 move.b -(a1),-(a2)
 subq.l #1,d0
 bne.b backward
 jmp (a3)
forward:
 move.b (a1)+,(a2)+
 subq.l #1,d0
 bne.b forward
 jmp (a3)
 dcb.b 14,0
runtime_entry:
"""


def test_copied_call_expression_uses_attached_target_not_raw_decode_address(tmp_path):
    binary = tmp_path/'copy.bin'
    asm = COPIED_BOOTSTRAP_PREFIX+"""
 jsr $10060.l
 rts
 dcb.b 8,0
runtime_callee:
 rts
"""
    c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',asm,output_path=binary)
    binary.write_bytes(binary.read_bytes().ljust(0x10080, b'\0'))
    source = RawBinarySource(kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=0x20000, entrypoint=0x20000,
        code_start_offset=0, display_path=str(binary), analysis_cache_path=tmp_path/'analysis')
    metadata = tmp_path/'metadata.json'
    metadata.write_text('{}')
    _, _, artifact = c_backend.build_listing_artifact_profile_from_binary_source(source, metadata_path=metadata)
    try:
        text = artifact.source_projection_with_profile()[0]
        assert 'abs_0_00020060:' not in text
        refs = artifact.query_payload('references', source_offset=0x50, section_index=0, direction='outgoing')['items']
        assert any(r['target_offset']==0x60 for r in refs)
        assert all(r['target_offset']!=0x10060 for r in refs)
    finally:
        artifact.close()


def test_rename_tracks_coordinate_identity_in_render_and_xrefs(tmp_path):
    source, value = fixture(tmp_path)
    append_manual_actions(tmp_path, binary_source=source, actions=[representation(value)])
    append_manual_actions(tmp_path, binary_source=source, actions=[(Kind.RENAME_MANUAL_LABEL,
        {'label_id':'bank','name':'renamed_bank'})])
    artifact = artifact_for(tmp_path, source)
    try:
        text = artifact.source_projection_with_profile()[0]
        assert 'subi.l #renamed_bank,d0' in text and 'tile_bank' not in text
        assert artifact.query_payload('references', symbol='renamed_bank')['total'] == 1
        assert artifact.query_payload('references', symbol='tile_bank')['total'] == 0
    finally:
        artifact.close()


@pytest.mark.parametrize('field,value', [('encoded_value',9), ('runtime_view',1), ('source_offset',999),
                                       ('section_index',999)])
def test_native_reader_does_not_silently_fallback_for_invalid_identity(tmp_path, field, value):
    source, _ = fixture(tmp_path)
    from amiga_reversing.disasm.effective_metadata import effective_metadata_text
    data = json.loads(effective_metadata_text(tmp_path))
    identity = dict(section_index=0,source_offset=8,runtime_view=0,encoded_value=8)
    identity[field] = value
    data['manual_representations'] = [dict(hunk=0,addr=0,end=6,style='symbol',operand_index=0,
        symbol='tile_bank',source_symbol=identity)]
    path = tmp_path/'bad.json'
    path.write_text(json.dumps(data))
    with pytest.raises(RuntimeError):
        c_backend.build_listing_artifact_profile_from_binary_source(source,metadata_path=path)


@pytest.mark.parametrize("tail_size", [4, 27792])
def test_canonical_opaque_layout_exports_named_original_bytes(tmp_path, tail_size):
    from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
    source, _ = fixture(tmp_path, tail_size=tail_size)
    append_manual_actions(tmp_path,binary_source=source,actions=[(Kind.REMOVE_MANUAL_LABEL, {'label_id':'bank'})])
    kind, payload = target_catalog_manual_payload('target.data_block.layout.create',
        dict(hunk=0,source_start=8,source_end=8+tail_size,name='preserved_unknown_tail',role='opaque_data',default_unit='byte'))
    records = append_manual_actions(tmp_path,binary_source=source,actions=[(Kind(kind),payload)])
    layout = records[0]['data_block_layout']['layout_id']
    kind, payload = target_catalog_manual_payload('target.data_block.element.set',
        dict(layout_id=layout,offset=0,width=tail_size,kind='raw',name='preserved_unknown_tail'))
    append_manual_actions(tmp_path,binary_source=source,actions=[(Kind(kind),payload)])
    artifact = artifact_for(tmp_path,source)
    try:
        package = artifact.source_package_payload(4)
        assert len(package['assets']) == 1
        asset = package['assets'][0]
        assert asset['classification'] == 'opaque_data'
        assert asset['name'] == 'preserved_unknown_tail'
        assert bytes.fromhex(asset['data_hex']) == source.path.read_bytes()[8:]
        assert 'INCBIN "assets/preserved_unknown_tail.bin"' in package['source_text']
    finally:
        artifact.close()


def test_ambiguous_native_declarations_refuse_without_history_change(tmp_path, monkeypatch):
    source, value = fixture(tmp_path)
    before = manual_action_log_path(tmp_path).read_bytes()
    original = c_backend.CListingArtifact.query_payload
    def ambiguous(self, kind, **kwargs):
        result = original(self, kind, **kwargs)
        if kind == 'symbols' and kwargs.get('symbol') == 'tile_bank':
            result['items'] = result['items'] * 2
        return result
    monkeypatch.setattr(c_backend.CListingArtifact,'query_payload',ambiguous)
    with pytest.raises(ValueError,match='one canonical'):
        append_manual_actions(tmp_path,binary_source=source,actions=[representation(value)])
    assert manual_action_log_path(tmp_path).read_bytes() == before


@pytest.mark.parametrize('runtime_only', [False,True])
def test_equate_reference_never_claims_coincident_file_bytes(tmp_path,runtime_only):
    source, value = fixture(tmp_path)
    equate = dict(name='scratch_address',value=value)
    if runtime_only:
        equate.update(address_domain='runtime',group='scratch',extent_bytes=4)
    append_manual_actions(tmp_path,binary_source=source,actions=[
        (Kind.CREATE_MANUAL_TARGET_EQUATE,{'target_equate':equate}),representation(value,'scratch_address')])
    artifact = artifact_for(tmp_path,source)
    try:
        refs = artifact.query_payload('references',symbol='scratch_address')['items']
        assert len(refs)==1 and refs[0]['target_offset'] is None
        assert 'scratch_address' in artifact.source_projection_with_profile()[0]
    finally:
        artifact.close()


def test_non_source_declaration_still_requires_native_symbol_codec(tmp_path,monkeypatch):
    source, value = fixture(tmp_path)
    before = manual_action_log_path(tmp_path).read_bytes()
    original = c_backend.CListingArtifact.query_payload
    def unsupported_declaration(self,kind,**kwargs):
        if kind=='symbols' and kwargs.get('symbol')=='unknown_generated_equate':
            return {'items':[dict(name='unknown_generated_equate',source_offset=None)]}
        return original(self,kind,**kwargs)
    monkeypatch.setattr(c_backend.CListingArtifact,'query_payload',unsupported_declaration)
    with pytest.raises(ValueError,match='unsupported or invalid native'):
        append_manual_actions(tmp_path,binary_source=source,actions=[representation(value,'unknown_generated_equate')])
    assert manual_action_log_path(tmp_path).read_bytes()==before


def test_hidden_analysis_label_does_not_fragment_explicit_opaque_asset(tmp_path):
    from amiga_reversing.disasm.manual_action_catalog import target_catalog_manual_payload
    binary=tmp_path/'copied.bin'
    c_backend.assemble_platform_source_text_with_c_backend('amiga-raw',COPIED_BOOTSTRAP_PREFIX+
        ' lea.l $20080.l,a0\n move.l a0,$dff050.l\n rts\n dcb.b 4,0\n',output_path=binary)
    binary.write_bytes(binary.read_bytes()+bytes(range(128)))
    source=RawBinarySource(kind=BinarySourceKind.RAW_BINARY,path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE,load_address=0x20000,entrypoint=0x20000,
        code_start_offset=0,display_path=str(binary),analysis_cache_path=tmp_path/'analysis')
    write_target_metadata(tmp_path,TargetMetadata(target_type='program',entry_register_seeds=()))
    append_manual_actions(tmp_path,binary_source=source,actions=[
        (Kind.CREATE_MANUAL_TARGET_EQUATE,{'target_equate':dict(name='runtime_scratch',value=0x20080,
            group='scratch',address_domain='runtime',extent_bytes=4)}),
        (Kind.CREATE_MANUAL_REPRESENTATION,{'representation':dict(representation_id='scratch',
            hunk=0,addr=0x50,end=0x56,element_kind='absolute_address',operand_index=0,style='symbol',
            symbol='runtime_scratch',value=0x20080,width_bytes=4)})])
    kind,payload=target_catalog_manual_payload('target.data_block.layout.create',dict(hunk=0,
        source_start=0x62,source_end=0xE2,name='tile_bank',role='opaque_data',default_unit='byte'))
    records=append_manual_actions(tmp_path,binary_source=source,actions=[(Kind(kind),payload)])
    kind,payload=target_catalog_manual_payload('target.data_block.element.set',dict(
        layout_id=records[0]['data_block_layout']['layout_id'],offset=0,width=128,kind='raw',name='tile_bank'))
    append_manual_actions(tmp_path,binary_source=source,actions=[(Kind(kind),payload)])
    artifact=artifact_for(tmp_path,source)
    try:
        assert all(x['source_offset'] != 0x80 for x in artifact.source_plan_payload()['labels'])
        analysis,_=artifact.analysis_payload()
        assert any(x['offset']==0x80 for x in analysis['sections'][0]['symbol_origins'])
        package=artifact.source_package_payload(4)
        assert len(package['assets'])==1
        assert bytes.fromhex(package['assets'][0]['data_hex'])==source.path.read_bytes()[0x62:]
    finally:
        artifact.close()

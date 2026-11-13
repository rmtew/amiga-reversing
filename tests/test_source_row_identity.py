"""A canonical label is not the preferred byte row at the same coordinate."""
from pathlib import Path
import pytest
from amiga_reversing.disasm import c_backend,restoration

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def artifact(tmp_path):
    # Native source assembler is a producer; lookup reads a fresh raw analysis.
    # LEA exposes an independently addressable data label after the RTS.
    raw,_=c_backend.assemble_platform_source_text_with_c_backend('atari-st-raw',
        'section code,code\nlea.l message(pc),a0\nrts\nmessage:\ndc.b "AB",0,0\n',target_cpu='68000')
    path=tmp_path/'source.bin';path.write_bytes(raw)
    value=c_backend.CListingArtifact.create(c_backend._CBackendSourceFile(path,'atari-st-raw',0),
        metadata_text='',include_dir='',project_root=ROOT)
    try:yield value
    finally:value.close()


def test_label_and_instruction_are_distinct_native_identities(artifact):
    label=artifact.row_for_source_identity(section_index=0,offset=0,kind='label')
    instruction=artifact.row_for_source_identity(section_index=0,offset=0,kind='instruction')
    assert label['stable_key']=='s0:00000000:label'
    assert instruction['stable_key']=='s0:00000000:instruction'
    assert label['row_index']!=instruction['row_index']
    assert artifact.row_for_source_identity(section_index=0,offset=0,kind='data') is None


def test_data_label_and_data_row_resolve_without_containing_row_substitution(artifact):
    label=artifact.row_for_source_identity(section_index=0,offset=6,kind='label')
    data=artifact.row_for_source_identity(section_index=0,offset=6,kind='data')
    assert label['stable_key']=='s0:00000006:label'
    assert data['stable_key']=='s0:00000006:data'
    assert artifact.row_for_source_identity(section_index=0,offset=7,kind='label') is None
    assert artifact.row_for_source_identity(section_index=0,offset=7,kind='data') is None
    assert artifact.row_for_source_identity(section_index=1,offset=6,kind='label') is None
    assert artifact.row_for_source_identity(section_index=0,offset=6,kind='invented') is None


def test_interpretation_admits_inspected_label_evidence_but_not_stale_identity(artifact):
    body=dict(command_id='label.rename',context=dict(locator=dict(section_index=0,start_offset=6)),
        evidence=dict(reason='LEA-referenced string after the returning code',evidence_refs=['s0:00000006:label']))
    result=restoration._interpretation_body('fixture',body,dict(subject_revision='current'),artifact)
    assert result['interpretation']['evidence_refs']==['s0:00000006:label']
    body['evidence']['evidence_refs']=['s0:00000007:label']
    with pytest.raises(ValueError,match='not a current canonical row'):
        restoration._interpretation_body('fixture',body,dict(subject_revision='current'),artifact)


@pytest.mark.parametrize('platform', ['atari-st-raw', 'amiga-raw'])
def test_hardware_value_domains_follow_the_target_platform(tmp_path, platform):
    # These addresses are ordinary numeric references in an ST analysis, even
    # when an executable embeds unused Amiga code. The Amiga analysis still
    # retains its platform-specific naming and include contract.
    code = 'section code,code\nlea.l $dff000.l,a5\nmove.w #$1ff,$40(a5)\nmove.w #$7fff,$9e(a5)\nmovea.l $4.l,a6\njsr -150(a6)\nrts\n'
    raw, _ = c_backend.assemble_platform_source_text_with_c_backend(platform, code, target_cpu='68000')
    path = tmp_path / 'platform.bin'
    path.write_bytes(raw)
    value = c_backend.CListingArtifact.create(c_backend._CBackendSourceFile(path, platform, 0),
        metadata_text='', include_dir='', project_root=ROOT)
    try:
        source, _ = value.inline_source_text_with_profile()
    finally:
        value.close()
    if platform == 'atari-st-raw':
        assert 'BC0F_DEST' not in source and 'ADKF_CLRALL' not in source
        assert '_LVOSuperState' not in source
        assert 'hardware/blit.i' not in source
    else:
        assert 'BC0F_DEST' in source and 'ADKF_CLRALL' in source
        assert '_LVOSuperState' in source
    rebuilt, _ = c_backend.assemble_platform_source_text_with_c_backend(platform, source, target_cpu='68000',
        include_dir=c_backend._platform_include_dir_for_listing(platform, ROOT))
    assert rebuilt == raw

"""Instruction query exposes native evidence without interpreting rendered text."""
from contextlib import closing

from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile


def test_operand_width_roles_address_index_and_bulk():
    # LEA; byte read; bit write; indexed word; predecrement MOVEM; RTS.
    code = bytes.fromhex('4df9000039fc102e019508ee0001022a3436100048e7c0004e75')
    with closing(build_flat_m68k_bytes_listing_artifact_profile(code, display_path='access-evidence')[2]) as artifact:
        rows = artifact.query_payload('instructions', limit=100)['items']
    by_offset = {r['source_offset']: r for r in rows}
    lea = by_offset[0]['operand_facts'][0]
    assert lea['absolute_address'] == 0x39fc
    assert lea['access'] == 'address'
    byte = by_offset[6]['operand_facts'][0]
    assert (byte['base_register'], byte['displacement'], byte['width_bytes']) == ('A6', 0x195, 1)
    bit = by_offset[10]['operand_facts'][1]
    assert bit['width_bytes'] == 1
    assert bit['access'] == 'memory_write'  # Native role; not a complete RMW event trace.
    index = by_offset[16]['operand_facts'][0]
    assert index['indexed'] and index['displacement_known']
    assert (index['index_register'], index['index_width_bytes'], index['index_scale']) == ('D1', 2, 1)
    bulk = by_offset[20]['operand_facts'][1]
    assert bulk['bulk_transfer'] and bulk['width_bytes'] == 4
    assert bulk['ea_shape_id'] == 3
    assert all(key in by_offset[6] for key in ('app_slot_refs', 'typed_accesses', 'unresolved_typed_accesses', 'address_evidence', 'platform_evidence'))


def test_signed_displacements_absolute_word_and_nonmemory_register():
    code = bytes.fromhex('302efffc303610fc3038fffc4e75')
    with closing(build_flat_m68k_bytes_listing_artifact_profile(code, display_path='signed-access-evidence')[2]) as artifact:
        rows = artifact.query_payload('instructions', limit=100)['items']
    assert rows[0]['operand_facts'][0]['displacement'] == -4
    assert rows[1]['operand_facts'][0]['displacement'] == -4
    assert rows[2]['operand_facts'][0]['absolute_address'] == 0xfffffffc
    assert not rows[0]['operand_facts'][1]['memory']


def test_amiga_hardware_context_keeps_operand_domain_evidence(tmp_path):
    from pathlib import Path
    from amiga_reversing.disasm.c_backend import CListingArtifact, _CBackendSourceFile
    root = Path(__file__).resolve().parents[1]
    binary = tmp_path / 'hardware.bin'
    binary.write_bytes(bytes.fromhex('4df900dff0003d4000a64e75'))
    with closing(CListingArtifact.create(_CBackendSourceFile(binary, 'amiga-raw', entry_offset=0), metadata_text='',
                 include_dir=str(root / 'ext/amiga_includes/ndk_2.0/include'), project_root=root)) as artifact:
        rows = artifact.query_payload('instructions', limit=100)['items']
    write = next(r for r in rows if r['source_offset'] == 6)
    assert not write['app_slot_refs']
    assert write['platform_evidence']
    assert write['platform_evidence'][0]['shape'] == 'hardware_register_access'
    assert write['platform_evidence'][0]['effective_address'] == 0xdff0a6


def test_closed_audio_family_has_no_invented_address(tmp_path):
    from pathlib import Path
    from amiga_reversing.disasm.c_backend import CListingArtifact, _CBackendSourceFile, assemble_platform_source_text_with_c_backend
    root = Path(__file__).resolve().parents[1]
    binary = tmp_path / 'family.bin'
    assemble_platform_source_text_with_c_backend('amiga-raw', ''' SECTION code,code
 ORG 0
 moveq #3,d7
loop:
 lea.l $DFF000.l,a6
 move.w d7,d0
 mulu.w #16,d0
 adda.w d0,a6
 move.w d1,$A6(a6)
 dbf d7,loop
 rts
''', output_path=binary)
    with closing(CListingArtifact.create(_CBackendSourceFile(binary, 'amiga-raw', entry_offset=0), metadata_text='',
                 include_dir=str(root / 'ext/amiga_includes/ndk_2.0/include'), project_root=root)) as artifact:
        rows = artifact.query_payload('instructions', limit=100)['items']
    uses = [p for r in rows for p in r['platform_evidence'] if p['shape'] == 'hardware_register_family']
    assert len(uses) == 1
    assert uses[0]['effective_address'] is None
    assert uses[0]['relative_base_offsets'] == [0, 16, 32, 48]
    assert not uses[0]['requires_input_contract']

"""Accepted immediate pointer domains survive metadata and normal layout export."""
import json
import subprocess
from pathlib import Path

import pytest
from amiga_reversing.disasm.effective_metadata import _immediate_interpreted_ref_equate
from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
from tests.test_memory_layouts import region,layout


def reference(runtime=True):
    return dict(target_hunk=0,target_offset=0x50000,source_value=0x70000,
        **(dict(runtime_address=0x70000) if runtime else {}))


def test_runtime_point_survives_without_inventing_pointee_extent():
    r=_immediate_interpreted_ref_equate(reference())
    assert (r.address_domain,r.extent_bytes,r.group)==('runtime',1,'immediate_runtime_reference_points')
    scalar=_immediate_interpreted_ref_equate(reference(False))
    assert scalar.address_domain is None and scalar.extent_bytes is None


@pytest.mark.parametrize('moved',[False,True])
@pytest.mark.parametrize('runtime',[False,True])
def test_native_immediate_equate_uses_region_only_for_runtime_domain(tmp_path,moved,runtime):
    r=_immediate_interpreted_ref_equate(reference(runtime))
    equate=dict(name=r.name,value=r.value,value_representation='hex')
    if r.address_domain:equate.update(address_domain=r.address_domain,extent_bytes=r.extent_bytes,group=r.group)
    config=layout([('display',0xd8000)] if moved else [])
    meta=dict(memory_regions=[region('display',0x70000,32000,kind='display')],
        memory_layouts=[config],selected_memory_layout_id='diagnostic',target_equates=[equate],
        execution_views=[dict(source_start=0,source_end=8,base_addr=0x10000)],
        manual_representations=[dict(hunk=0,addr=0,end=6,style='symbol',element_kind='immediate',operand_index=0,symbol=r.name)])
    path=tmp_path/'metadata.json';path.write_text(json.dumps(meta))
    original=bytes.fromhex('0680000700004e75')
    _,_,artifact=build_flat_m68k_bytes_listing_artifact_profile(original,display_path='overlay-immediate',metadata_path=path)
    try:text=artifact.inline_source_text_with_profile()[0]
    finally:artifact.close()
    assert ('\tEQU\tdisplay_base' if runtime else '\tEQU\t$70000') in text
    source=tmp_path/'out.s';source.write_text(text);binary=tmp_path/'out.bin'
    subprocess.run([str(Path(__file__).resolve().parents[1]/'tools/vasmm68k_mot.exe'),'-Fbin','-m68000','-no-opt','-o',str(binary),str(source)],check=True,capture_output=True)
    expected=bytes.fromhex('0680000d80004e75') if moved and runtime else original
    assert binary.read_bytes()==expected

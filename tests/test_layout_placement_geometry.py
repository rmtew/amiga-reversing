"""Shared geometry keeps the data-relocation lane a semantic adapter."""
import ctypes
import json
from pathlib import Path

import pytest

from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
from tests.test_memory_regions import region


def test_native_geometry_half_open_bounds_overflow_and_translation():
    root=Path(__file__).resolve().parents[1]
    dll=ctypes.CDLL(str(root/'src/build/libamiga_backend.so'))
    fits=dll.m68k_memory_layout_extent_fits
    fits.argtypes=[ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint64]
    fits.restype=ctypes.c_int
    assert fits(0x7ff80,128,8,0x1000,0x80000)
    assert fits(0xc7ff80,128,8,0xc00000,0xc80000)
    assert fits(0xfffffff8,8,8,0,0x100000000)
    for args in [(0xfffffff8,16,8,0,0x100000000),(0x1000,0,8,0,0x80000),
                 (0x1000,8,3,0,0x80000),(0x1000,8,0,0,0x80000),
                 (0xff8,8,8,0x1000,0x80000),(0x7ff88,128,8,0x1000,0x80000),
                 (0x1000,8,8,0,0x100000001)]:
        assert not fits(*args)
    translate=dll.m68k_memory_layout_translate_reference
    translate.argtypes=[ctypes.c_uint32]*5+[ctypes.POINTER(ctypes.c_uint32)]
    translate.restype=ctypes.c_int
    out=ctypes.c_uint32()
    assert translate(0x397c,0xc7ff80,128,0x39fa,2,ctypes.byref(out))==0
    assert out.value==0xc7fffe
    for original,placed,size,address,width in [(0x397c,0xc7ff80,128,0x39fb,2),
        (0x397c,0xc7ff80,128,0x397b,1),(0,0xfffffff8,16,0,1)]:
        assert translate(original,placed,size,address,width,ctypes.byref(out))==-1


@pytest.mark.parametrize('destination,memory_class,refusal',[
    (0x1000,'chip',None),(0x7ff80,'chip',None),(0xff8,'chip','outside_supported_a500_memory'),
    (0x7ff88,'chip','outside_supported_a500_memory'),(0xc00000,'slow',None),
    (0xc7ff80,'slow',None),(0xc7ff88,'slow','outside_supported_a500_memory'),
    (0xc7ff81,'slow','reservation_alignment'),
])
def test_semantic_adapter_retains_a500_leases_and_exact_rewrite(tmp_path,destination,memory_class,refusal):
    path=tmp_path/'metadata.json';path.write_text(json.dumps({'memory_regions':[region()]}))
    _,_,artifact=build_flat_m68k_bytes_listing_artifact_profile(
        bytes.fromhex('4a390000397c4e75'),display_path='fixture',metadata_path=path)
    try:
        plan=artifact.memory_region_plan('key_state',destination,memory_class)
        assert plan['refusal']==refusal
        assert plan['status']==('refused' if refusal else 'ready')
        assert plan['reservation']=='exec_allocabs' and plan['reservation_size']==128
        if refusal is None:
            assert plan['rewrite_ledger']==[dict(section_index=0,source_offset=0,operand_index=0,
                region_offset=0,before='4a390000397c',after='4a39'+destination.to_bytes(4,'big').hex())]
    finally:
        artifact.close()

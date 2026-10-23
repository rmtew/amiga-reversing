"""Native materialization-index semantics against an independent point oracle."""
import ctypes as c
import random
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class Span(c.Structure):
    _fields_ = [(s, c.c_uint32) for s in ('address', 'size', 'section', 'source_offset')]


class Map(c.Structure):
    _fields_ = [('segments', c.c_void_p), ('count', c.c_size_t)]


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    output = tmp_path_factory.mktemp('runtime-map')/'map.so'
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    str(ROOT/'src/m68k_runtime_map.c'), '-o', str(output)], check=True)
    lib = c.CDLL(str(output))
    lib.m68k_runtime_map_build.argtypes = [c.POINTER(Map), c.POINTER(Span), c.c_size_t]
    lib.m68k_runtime_map_build.restype = c.c_int
    lib.m68k_runtime_map_destroy.argtypes = [c.POINTER(Map)]
    lib.m68k_runtime_map_resolve.argtypes = [c.POINTER(Map), c.c_uint32, c.c_uint32,
                                            c.POINTER(c.c_uint32), c.POINTER(c.c_uint32),
                                            c.POINTER(c.c_size_t)]
    lib.m68k_runtime_map_resolve.restype = c.c_int
    return lib


def build(lib, spans):
    index = Map()
    assert lib.m68k_runtime_map_build(c.byref(index), (Span*len(spans))(*[Span(*s) for s in spans]), len(spans)) == 0
    return index


def resolve(lib, index, address, size=1):
    section, offset, steps = c.c_uint32(), c.c_uint32(), c.c_size_t()
    rc = lib.m68k_runtime_map_resolve(c.byref(index), address, size,
                                    c.byref(section), c.byref(offset), c.byref(steps))
    return rc, section.value, offset.value, steps.value


def test_alias_conflict_gap_and_affine_seam(native):
    spans = [(100, 20, 0, 0), (105, 10, 0, 5), (120, 10, 0, 20),
             (112, 2, 1, 0), (140, 4, 0, 40)]
    index = build(native, spans)
    try:
        assert resolve(native, index, 105, 7)[:3] == (1, 0, 5)
        assert resolve(native, index, 111, 2)[0] == -1
        assert resolve(native, index, 114, 16)[:3] == (1, 0, 14)
        assert resolve(native, index, 130)[0] == 0
        assert resolve(native, index, 125, 16)[0] == 0
        assert resolve(native, index, 100, 0)[0] == -1
    finally:
        native.m68k_runtime_map_destroy(c.byref(index))


def test_seeded_point_oracle_and_order_independence(native):
    rng = random.Random(46001)
    for _ in range(40):
        spans = [(rng.randrange(128), rng.randrange(1, 24), rng.randrange(3), rng.randrange(80))
                 for _ in range(24)]
        spans += spans[:3]  # exact aliases are not conflicts
        index = build(native, spans)
        rng.shuffle(spans)
        permuted = build(native, spans)
        try:
            for addr in range(160):
                targets = {(section, source+addr-start) for start, size, section, source in spans
                           if start <= addr < start+size}
                expected = 0 if not targets else 1 if len(targets) == 1 else -1
                actual = resolve(native, index, addr)
                assert actual[0] == expected
                if expected == 1:
                    assert actual[1:3] == next(iter(targets))
                assert actual[:3] == resolve(native, permuted, addr)[:3]
        finally:
            native.m68k_runtime_map_destroy(c.byref(index))
            native.m68k_runtime_map_destroy(c.byref(permuted))


def test_invalid_build_preserves_live_index_and_upper_boundary(native):
    index = build(native, [(0xfffffff0, 16, 2, 0)])
    try:
        assert resolve(native, index, 0xffffffff)[:3] == (1, 2, 15)
        for span in [(1, 0, 0, 0), (0xfffffff0, 17, 0, 0), (0, 16, 0, 0xfffffff8)]:
            assert native.m68k_runtime_map_build(c.byref(index), (Span*1)(Span(*span)), 1) == -1
            assert resolve(native, index, 0xffffffff)[:3] == (1, 2, 15)
        assert resolve(native, index, 0xffffffff, 2)[0] == -1
    finally:
        native.m68k_runtime_map_destroy(c.byref(index))


def test_operation_counts_depend_on_intervals_not_bytes(native):
    for count in (128, 256, 512):
        index = build(native, [(i*32, 16, 0, i*16) for i in range(count)])
        try:
            assert resolve(native, index, (count-1)*32, 16)[3] <= count.bit_length()+1
        finally:
            native.m68k_runtime_map_destroy(c.byref(index))
    steps = []
    for size in (16, 349040, 8388608):
        index = build(native, [(0x10000, size, 0, 0)])
        try:
            answer = resolve(native, index, 0x10000, size)
            assert answer[:3] == (1, 0, 0)
            steps.append(answer[3])
        finally:
            native.m68k_runtime_map_destroy(c.byref(index))
    assert steps == [2, 2, 2]

"""Known indirect destinations belong in CFGs without claiming closed sets."""
from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import BinarySourceKind, RawAddressModel, RawBinarySource
from amiga_reversing.disasm.c_backend import (
    analyze_project_source_with_c_backend,
    assemble_platform_source_text_with_c_backend,
)

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    not (ROOT / 'src/build/platform_file_lib.dll').exists(),
    reason='Build native backend before exercising canonical CFG',
)


def analyze(tmp_path, text, base):
    original, _ = assemble_platform_source_text_with_c_backend(
        'amiga-raw', f' SECTION code,code\n ORG ${base:X}\n' + text,
        project_root=ROOT,
    )
    binary = tmp_path / 'indirect.bin'
    binary.write_bytes(original)
    source = RawBinarySource(
        kind=BinarySourceKind.RAW_BINARY, path=binary,
        address_model=RawAddressModel.RUNTIME_ABSOLUTE, load_address=base,
        entrypoint=base, code_start_offset=0, display_path=str(binary),
        analysis_cache_path=tmp_path / 'analysis',
    )
    return analyze_project_source_with_c_backend(source, metadata_path=None, project_root=ROOT)['sections'][0]


@pytest.mark.parametrize('base', [0x100, 0x10000])
@pytest.mark.parametrize('operation,kind', [('jsr', 3), ('jmp', 4)])
def test_traced_register_target_has_source_coordinate_edge(tmp_path, base, operation, kind):
    section = analyze(tmp_path, f' lea target(pc),a0\n {operation} (a0)\n rts\ntarget:\n rts\n dc.w 0\n', base)
    edges = [e for e in section['edges'] if e['source_offset'] == 4 and e['kind'] == kind]
    assert {e['target_offset'] for e in edges} == {8, 0xFFFFFFFF}
    destination = next(e for e in edges if e['target_offset'] == 8)
    assert section['blocks'][destination['target_block_index']]['start_offset'] == 8
    assert all(e['target_offset'] != base + 8 for e in edges)
    if operation == 'jsr':
        assert any(e['source_offset'] == 4 and e['target_offset'] == 6 and e['kind'] == 1 for e in section['edges'])


@pytest.mark.parametrize('base', [0x100, 0x10000])
def test_dispatch_exports_all_traced_entries_but_retains_unknown_edge(tmp_path, base):
    section = analyze(tmp_path, ''' moveq #0,d0
 movea.l table(pc,d0.w),a0
 jmp (a0)
table:
 dc.l first,second,third
first:
 moveq #1,d1
 rts
second:
 moveq #2,d1
 rts
third:
 moveq #3,d1
 rts
 dc.w 0
''', base)
    site = next(s for s in section['recovered_indirect_sites'] if s['offset'] == 6)
    assert site['target_count'] == 3
    edges = [e for e in section['edges'] if e['source_offset'] == 6 and e['kind'] == 4]
    assert {e['target_offset'] for e in edges} == {20, 24, 28, 0xFFFFFFFF}
    assert len(edges) == 4  # duplicate discovery provenance does not duplicate edges
    for edge in edges:
        if edge['target_offset'] == 0xFFFFFFFF:
            continue
        assert 0 <= edge['target_block_index'] < len(section['blocks'])
        assert section['blocks'][edge['target_block_index']]['start_offset'] == edge['target_offset']
    assert not any(e['target_offset'] == 8 for e in edges)  # table address is not executable


def test_unknown_register_is_not_resolved_from_numeric_coincidence(tmp_path):
    section = analyze(tmp_path, ' jsr (a0)\n rts\n dc.l $104\n rts\n dc.w 0\n', 0x100)
    edges = [e for e in section['edges'] if e['source_offset'] == 0 and e['kind'] == 3]
    assert len(edges) == 1 and edges[0]['target_offset'] == 0xFFFFFFFF


@pytest.mark.parametrize('base', [0x100, 0x10000])
def test_runtime_branch_keeps_distinct_continuation_inputs(tmp_path, base):
    section = analyze(tmp_path, ''' tst.w d0
 beq.w second
 lea first_continuation(pc),a3
 bra.w shared
second:
 lea second_continuation(pc),a3
 bra.w shared
shared:
 jmp (a3)
first_continuation:
 moveq #1,d1
 rts
second_continuation:
 moveq #2,d1
 rts
 dc.w 0
''', base)
    site = next(s for s in section['recovered_indirect_sites'] if s['offset'] == 22)
    assert site['target_count'] == 2 and site['status'] == 'per_caller'
    edges = [e for e in section['edges'] if e['source_offset'] == 22 and e['kind'] == 4]
    assert {e['target_offset'] for e in edges} == {24, 28, 0xFFFFFFFF}


def test_overwritten_register_does_not_retain_an_earlier_target(tmp_path):
    section = analyze(tmp_path, ''' lea target(pc),a0
 movea.l d1,a0
 jsr (a0)
 rts
target:
 rts
 dc.w 0
''', 0x100)
    edges = [e for e in section['edges'] if e['source_offset'] == 6 and e['kind'] == 3]
    assert len(edges) == 1 and edges[0]['target_offset'] == 0xFFFFFFFF


@pytest.mark.parametrize('base', [0x100, 0x10000])
@pytest.mark.parametrize('padding', [0, 24, 80])
@pytest.mark.parametrize('clobber', ['', ' movea.l d1,a3\n', ' bsr.w opaque_call\n'])
def test_continuations_survive_long_selectors_and_table_dispatch(tmp_path, base, padding, clobber):
    text = ''' tst.w d0
 beq.w second
 cmp.w #1,d0
 beq.w third
 lea first_continuation(pc),a3
 bra.w selector
first_continuation:
 moveq #1,d0
 rts
second:
 lea second_continuation(pc),a3
 bra.w selector
second_continuation:
 moveq #2,d0
 rts
third:
 lea third_continuation(pc),a3
 bra.w selector
third_continuation:
 moveq #3,d0
 rts
selector:
'''+(' nop\n' * padding)+clobber+''' moveq #0,d2
 movea.l table(pc,d2.w),a1
 jmp (a1)
table:
 dc.l writer_zero,writer_one
writer_zero:
 bclr.b d1,(a0)
 jmp (a3)
writer_one:
 bset.b d1,(a0)
 jmp (a3)
opaque_call:
 movea.l d1,a3
 rts
 dc.w 0
'''
    section = analyze(tmp_path, text, base)
    sites = section['recovered_indirect_sites']
    assert len(sites) == 3
    dispatch, *tails = sorted(sites, key=lambda s: s['offset'])
    assert dispatch['target_count'] == 2 and dispatch['status'] == 'jump_table'
    sets = []
    for site in tails:
        assert site['status'] == ('unresolved' if clobber else 'per_caller')
        edges = [e for e in section['edges'] if e['source_offset'] == site['offset'] and e['kind'] == 4]
        assert any(e['target_offset'] == 0xFFFFFFFF for e in edges)
        targets = {e['target_offset'] for e in edges if e['target_offset'] != 0xFFFFFFFF}
        assert len(targets) == (0 if clobber else 3)
        sets.append(targets)
    assert sets[0] == sets[1]

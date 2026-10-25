from pathlib import Path

import pytest

from amiga_reversing.disasm.binary_source import RawBinarySource, BinarySourceKind, RawAddressModel
from amiga_reversing.disasm.c_backend import analyze_project_source_with_c_backend


def analyze(tmp_path: Path, raw: str, runtime_base=None):
    path = tmp_path / "dispatch.bin"
    path.write_bytes(bytes.fromhex(raw))
    source = RawBinarySource(BinarySourceKind.RAW_BINARY, path,
        RawAddressModel.LOCAL_OFFSET if runtime_base is None else RawAddressModel.RUNTIME_ABSOLUTE,
        runtime_base or 0, runtime_base or 0, 0, str(path), path.with_suffix(".analysis"))
    return analyze_project_source_with_c_backend(source)["sections"][0]


@pytest.mark.parametrize("raw,site,target", [
    ("41fa00044ed04e75", 4, 6),  # Plain PC displacement stays unchanged.
    ("700241fb00044ed04e714e75", 6, 10),  # Known nonzero WORD index.
    ("700241fb08044ed04e714e75", 6, 10),  # Known LONG index.
    ("303cfffe41fb00064ed04e754e71", 8, 10),  # Signed low WORD, unknown high half.
])
def test_pc_lea_known_index_uses_effective_address(tmp_path, raw, site, target):
    section = analyze(tmp_path, raw)
    found = next(x for x in section["recovered_indirect_sites"] if x["offset"] == site)
    assert found["target"] == target
    assert found["target_count"] == 1


@pytest.mark.parametrize("raw,site", [
    ("41fb00044ed04e75", 4),  # Unknown index must not be assumed zero.
    ("303b000841fb08044ed00004000872014e7572024e75", 8),  # WORD-table load cannot supply a LONG index.
    ("303b000a301141fb00044ed00004000872014e7572024e75", 10),  # Clobbered table index.
])
def test_pc_lea_unknown_index_does_not_invent_base_target(tmp_path, raw, site):
    section = analyze(tmp_path, raw)
    found = next(x for x in section["recovered_indirect_sites"] if x["offset"] == site)
    assert found["status"] == "unresolved"
    assert found["target"] is None


@pytest.mark.parametrize("runtime_base", [None, 0x1000])
def test_word_table_load_pc_indexed_lea_and_indirect_jump(tmp_path, runtime_base):
    # At 10, two WORD offsets 4 and 8 point to complete routines at 14 and 18.
    section = analyze(tmp_path, "303b000841fb00044ed00004000872014e7572024e75", runtime_base)
    found = next(x for x in section["recovered_indirect_sites"] if x["offset"] == 8)
    refs = {x["offset"] for x in section["code_start_refs"]
            if x["source_offset"] == 8 and x["reason_name"] == "control_target"}
    assert refs == {14, 18}
    assert found["target_count"] == 2
    assert found["target"] != 10


def test_word_table_and_pc_relative_target_base_can_differ(tmp_path):
    section = analyze(tmp_path, "303b000841fb00084ed00000000472014e7572024e75")
    refs = {x["offset"] for x in section["code_start_refs"]
            if x["source_offset"] == 8 and x["reason_name"] == "control_target"}
    assert refs == {14, 18}


def test_following_zero_data_does_not_become_table_base_handler(tmp_path):
    raw = "303b000841fb00044ed000200024" + "0000" * 14 + "72014e7572024e75"
    section = analyze(tmp_path, raw)
    refs = {x["offset"] for x in section["code_start_refs"]
            if x["source_offset"] == 8 and x["reason_name"] == "control_target"}
    assert refs == {42, 46}


def test_word_memory_address_is_not_loaded_index_value(tmp_path):
    # Reading address $10 does not establish that D0 contains $10.
    section = analyze(tmp_path, "3038001041fb00044ed0" + "4e71" * 10 + "4e75")
    found = next(x for x in section["recovered_indirect_sites"] if x["offset"] == 8)
    assert found["target"] is None
    assert found["status"] == "unresolved"

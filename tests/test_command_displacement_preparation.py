"""One immutable displacement-use index per locked command preparation."""
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import server


def row(offset, parts):
    return {"kind": "instruction", "section_index": 0, "addr": offset,
            "start_offset": offset, "row_key": f"s0:{offset:08X}:instruction",
            "text": f"  move.l source,{offset}  \n", "opcode_or_directive": "move.l",
            "operand_parts": [{"kind": "displacement", "operand_index": i,
                "base_register": base, "displacement": disp, "value": disp,
                "width_bytes": 2} for i,(base,disp) in enumerate(parts)],
            "operand_accesses": ["read", "write"]}


class Artifact:
    def __init__(self, rows):
        self.rows, self.scans = rows, 0

    def summary_payload(self):
        return {"total_rows": len(self.rows)}, {}

    def window_payload(self, **kwargs):
        self.scans += 1
        return {"rows": self.rows}, {}


def query(base, displacement):
    return {"base_register": base, "displacement": displacement}


def test_index_retains_exact_count_first_32_rows_and_first_matching_operand():
    rows=[row(i*4, [("A5",4),("A5",4)]) for i in range(40)]
    rows += [row(200,[("A6",4),("A5",8)]),row(204,[("A5",-4)])]
    artifact=Artifact(rows)
    result=server._same_displacement_use_index(artifact)
    count,uses=result["A5",4]
    assert count==40 and len(uses)==32 and artifact.scans==1
    assert uses[0]=={"row_index":0,"hunk":0,"addr":0,
        "stable_key":"s0:00000000:instruction","row_text":"move.l source,0",
        "operand_index":0,"access":"read","width_bytes":2}
    assert [u["addr"] for u in uses]==list(range(0,128,4))
    assert result["A6",4][0]==result["A5",8][0]==result["A5",-4][0]==1
    assert result["A5",8][1][0]["operand_index"]==1
    assert server._same_displacement_use_index(artifact,only=("A5",4))=={("A5",4):result["A5",4]}


def test_preparation_index_is_project_projection_and_artifact_scoped(monkeypatch):
    first=Artifact([row(0,[("A5",4)])]);second=Artifact([row(8,[("A5",4)]),row(12,[("A6",8)])])
    current={"artifact":first,"key":"first"}
    monkeypatch.setattr(server,"_valid_c_listing_artifact",lambda _:current["artifact"])
    monkeypatch.setattr(server,"_project_listing_cache_key",lambda _:current["key"])
    token=server._COMMAND_DISPLACEMENT_SNAPSHOTS.set({})
    try:
        a=query("a5",4);server._copy_rsset_same_displacement_context("one",a)
        a["same_displacement_uses"][0]["addr"]=999
        b=query("A5",4);server._copy_rsset_same_displacement_context("one",b)
        server._copy_rsset_same_displacement_context("one",query("A6",8))
        assert first.scans==1 and b["same_displacement_uses"][0]["addr"]==0
        server._copy_rsset_same_displacement_context("two",query("A5",4));assert first.scans==2
        current["key"]="second"
        server._copy_rsset_same_displacement_context("one",query("A5",4));assert first.scans==3
        current["artifact"]=second
        c=query("A5",4);server._copy_rsset_same_displacement_context("one",c)
        assert second.scans==1 and c["same_displacement_uses"][0]["addr"]==8
    finally:server._COMMAND_DISPLACEMENT_SNAPSHOTS.reset(token)
    server._copy_rsset_same_displacement_context("one",query("A5",4))
    server._copy_rsset_same_displacement_context("one",query("A5",4))
    assert second.scans==3  # No reuse outside the locked preparation stage.


def test_absent_or_unusable_native_rows_do_not_invent_uses(monkeypatch):
    monkeypatch.setattr(server,"_valid_c_listing_artifact",lambda _:None)
    target=query("A5",4);server._copy_rsset_same_displacement_context("one",target)
    assert target==query("A5",4)
    for total,rows in [(None,[]),(0,[]),(1,None)]:
        artifact=SimpleNamespace(summary_payload=lambda:({"total_rows":total},{}),
            window_payload=lambda **kw:({"rows":rows},{}))
        assert server._same_displacement_use_index(artifact)=={}


def test_failed_preparation_discards_index_before_next_request(monkeypatch):
    artifact=Artifact([row(0,[("A5",4)])])
    monkeypatch.setattr(server,"_valid_c_listing_artifact",lambda _:artifact)
    monkeypatch.setattr(server,"_project_listing_cache_key",lambda _:"snapshot")
    def prepare(project, body, profile, cache):
        target=query("A5",4)
        server._copy_rsset_same_displacement_context(project,target)
        raise ValueError("invalid final command")
    monkeypatch.setattr(server,"_prepare_catalog_command",prepare)
    for _ in range(2):
        with pytest.raises(ValueError,match="invalid final command"):
            server._execute_catalog_commands_unchecked("one",[{}])
        assert server._COMMAND_DISPLACEMENT_SNAPSHOTS.get() is None
    assert artifact.scans==2


def test_derived_app_target_is_not_an_encoded_displacement_use():
    sample = row(0, [("A4", 0x78)])
    sample["app_slot_refs"] = [dict(symbol="cache", displacement=0xC3E,
        base_register="A4", operand_index=0, access="address", derived=True,
        base_displacement=0xBC6, operand_displacement=0x78, base_evidence="a6_fallback")]
    index = server._same_displacement_use_index(Artifact([sample]))
    assert set(index) == {("A4", 0x78)}
    assert index["A4", 0x78][0] == 1

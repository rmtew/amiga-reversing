from __future__ import annotations

import hashlib

import pytest

from amiga_reversing.tools import direct_payload_adapter as adapter


def test_boot_checksum_makes_a_boot_block_sum_to_all_ones() -> None:
    block = bytearray(adapter.BOOT_BLOCK_SIZE)
    block[0:4] = b"DOS\0"
    block[12:16] = b"TEST"
    block[4:8] = adapter.boot_checksum(block).to_bytes(4, "big")

    total = 0
    for offset in range(0, adapter.BOOT_BLOCK_SIZE, 4):
        total += int.from_bytes(block[offset : offset + 4], "big")
        total = (total & 0xFFFFFFFF) + (total >> 32)
    assert total == 0xFFFFFFFF


def test_build_boot_adf_embeds_the_validated_payload(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    payload = bytes(range(256)) * 2
    payload_path = tmp_path / "payload.bin"
    payload_path.write_bytes(payload)
    contract = adapter.DirectPayloadContract(
        identifier="test",
        target_id="target",
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        load_address=0x10000,
        entrypoint=0x10000,
        entry_registers={},
        handoff_marker_address=0x7FFF8,
        handoff_marker_value=0x48414E44,
    )
    monkeypatch.setattr(adapter, "assemble_boot_code", lambda *_args, **_kwargs: b"\x4e\x75")
    output = tmp_path / "direct.adf"

    result = adapter.build_boot_adf(contract, payload_path, output)

    image = output.read_bytes()
    assert result["floppy0"] == str(output)
    assert image[:4] == b"DOS\0"
    assert image[adapter.PAYLOAD_DISK_OFFSET : adapter.PAYLOAD_DISK_OFFSET + len(payload)] == payload


def test_build_boot_adf_rejects_a_payload_hash_mismatch(tmp_path) -> None:
    payload_path = tmp_path / "payload.bin"
    payload_path.write_bytes(bytes(512))
    contract = adapter.DirectPayloadContract("test", "target", "0" * 64, 0x10000, 0x10000, {}, 0x7FFF8, 0x48414E44)

    with pytest.raises(adapter.DirectPayloadContractError, match="SHA-256"):
        adapter.build_boot_adf(contract, payload_path, tmp_path / "direct.adf")


def test_entry_context_source_orders_data_then_address_registers() -> None:
    assert adapter.entry_context_source({"a1": 0x20000, "d7": 0xFFFFFFFF}) == (
        "; Generated direct-payload entry register context.\n"
        "    move.l #$FFFFFFFF,d7\n"
        "    movea.l #$00020000,a1\n"
    )


def test_direct_boot_shim_waits_for_the_shared_session_release_token() -> None:
    source = adapter.BOOT_SOURCE.read_text(encoding="ascii")

    assert "await_session_release:" in source
    assert "cmpi.l  #HANDOFF_RELEASE_VALUE,HANDOFF_MARKER" in source
    assert "move.l  #'FAIL',HANDOFF_MARKER" in source
    assert "failed_hold:" in source
    assert adapter.HANDOFF_RELEASE_VALUE == 0x474F2121


def test_load_contract_rejects_missing_entry_registers(tmp_path) -> None:
    (tmp_path / "test.json").write_text(
        """{"identifier":"test","target_id":"target","payload_sha256":"0000000000000000000000000000000000000000000000000000000000000000","load_address":"0x10000","entrypoint":"0x10000","handoff_marker_address":"0x7fff8","handoff_marker_value":"0x48414e44"}""",
        encoding="utf-8",
    )

    with pytest.raises(adapter.DirectPayloadContractError, match="entry_registers"):
        adapter.load_contract("test", directory=tmp_path)


def test_load_contract_preserves_explicit_entry_registers(tmp_path) -> None:
    (tmp_path / "test.json").write_text(
        """{"identifier":"test","target_id":"target","payload_sha256":"0000000000000000000000000000000000000000000000000000000000000000","load_address":"0x20000","entrypoint":"0x20000","entry_registers":{"a1":"0x20000"},"handoff_marker_address":"0x7fff8","handoff_marker_value":"0x48414e44"}""",
        encoding="utf-8",
    )

    contract = adapter.load_contract("test", directory=tmp_path)

    assert contract.entry_registers == {"a1": 0x20000}


@pytest.mark.parametrize('reservation', [(0xc7f001,128),(0xc7f000,127),(0xc7f000,0)])
def test_invalid_reservation_writes_no_boot_or_temporary_includes(tmp_path,reservation):
    from dataclasses import replace
    contract=replace(adapter.DirectPayloadContract('test','target','0'*64,0x20000,0x20000,{},0x7fff8,0x48414e44),reservations=(reservation,))
    with pytest.raises(adapter.DirectPayloadContractError,match='Invalid exact Exec reservation'):
        adapter.assemble_boot_code(contract,512,output_path=tmp_path/'boot.bin')
    assert not list(tmp_path.iterdir())


def test_reservation_boot_shim_assembles_and_cleans_includes(tmp_path):
    from dataclasses import replace
    if not adapter.VASM.exists():pytest.skip('Installed vasm required')
    contract=replace(adapter.DirectPayloadContract('test','target','0'*64,0x20000,0x20000,{},0x7fff8,0x48414e44),reservations=((0xc7f000,128),))
    code=adapter.assemble_boot_code(contract,512,output_path=tmp_path/'boot.bin')
    assert code and len(code)<=adapter.BOOT_BLOCK_SIZE-12
    assert not (tmp_path/'direct_payload_entry_context.i').exists()
    assert not (tmp_path/'direct_payload_reservations.i').exists()


def test_pre_read_reservations_union_input_and_destinations():
    from dataclasses import replace
    contract = adapter.load_contract('pandora')
    contract = replace(contract, reservations=((0x65400, 8), (0x7BFF8, 16)))
    assert adapter.reservation_plan(contract, 376832) == (
        (0x7FFF0, 16), (0x20000, 0x5C008)
    )


@pytest.mark.parametrize('changes', [
    {'reservations': ((0x7FFF0, 8),)},
    {'load_address': 0x7FE00},
    {'handoff_marker_address': 4},
    {'handoff_marker_address': 0xFFFFFE},
])
def test_pre_read_reservation_rejects_protocol_overlap_and_invalid_marker(changes):
    from dataclasses import replace
    contract = replace(adapter.load_contract('pandora'), **changes)
    with pytest.raises(adapter.DirectPayloadContractError, match='marker'):
        adapter.reservation_plan(contract, 512)


@pytest.mark.parametrize(('address', 'allowed'), [
    (0x65400, True), (0x75368, True), (0x75370, False),
    (0x7BFF8, False), (0x10000, False), (0x5DD00, False),
])
def test_derived_binding_only_reuses_consumed_input_and_rejects_game_overlap(tmp_path, monkeypatch, address, allowed):
    from types import SimpleNamespace
    from amiga_reversing.disasm import derived_artifact, c_backend
    payload = tmp_path / 'payload.bin'
    payload.write_bytes(bytes(376832))
    definition = {'runtime_address': 0x5DD00, 'size': 2}
    manifest = {'original_sha256': '0'*64, 'artifact_sha256': 'a'*64,
        'placement': {'runtime_address': address}, 'region': definition,
        'initialization': {'section_index': 0, 'source_offset': 0x4DD00, 'bytes': '0040'}}
    monkeypatch.setattr(derived_artifact, 'validate_manifest', lambda *_: (manifest, payload))
    monkeypatch.setattr(derived_artifact, 'verify_native_binding', lambda *_: None)
    monkeypatch.setattr(adapter, 'verify_materialization_binding', lambda *_: None)
    monkeypatch.setattr(c_backend, 'build_project_listing_artifact_profile', lambda *_: (None, None, SimpleNamespace(close=lambda: None)))
    from dataclasses import replace
    base = replace(adapter.load_contract('pandora'), payload_sha256='0'*64)
    if allowed:
        bound, _, _ = adapter.bind_derived_contract(base, tmp_path/'manifest.json')
        assert bound.reservations == ((address, 8),)
        assert bound.initialization == (address, b'\x00\x40')
    else:
        with pytest.raises(adapter.DirectPayloadContractError, match='overlaps'):
            adapter.bind_derived_contract(base, tmp_path/'manifest.json')


def test_materialization_binding_requires_native_view_and_exact_instruction(tmp_path):
    import json
    from dataclasses import replace
    from amiga_reversing.disasm.c_backend import build_flat_m68k_bytes_listing_artifact_profile
    path = tmp_path/'view.json'
    path.write_text(json.dumps({'execution_views': [{'source_start': 0, 'source_end': 10, 'base_addr': 0x10000}]}))
    _, _, artifact = build_flat_m68k_bytes_listing_artifact_profile(bytes.fromhex('343a00064e7500000040'), display_path='view', metadata_path=path)
    contract = replace(adapter.load_contract('pandora'), materialization={'source_offset': 0, 'size': 10,
        'runtime_address': 0x10000, 'entry_source_offset': 0, 'source_consumed_at_entry': True})
    try:
        adapter.verify_materialization_binding(contract, artifact)
        for change in [{'size': 8}, {'entry_source_offset': 1}, {'runtime_address': 0x20000}]:
            with pytest.raises(adapter.DirectPayloadContractError, match='native copy view and instruction'):
                adapter.verify_materialization_binding(replace(contract, materialization=contract.materialization | change), artifact)
    finally:
        artifact.close()

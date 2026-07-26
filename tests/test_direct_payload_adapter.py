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

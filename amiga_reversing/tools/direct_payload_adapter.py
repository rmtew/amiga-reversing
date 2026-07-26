"""Build a raw Amiga boot disk from a validated direct-payload contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.project_paths import resolve_project_paths

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIRECTORY = ROOT / "runtime" / "direct_payload_contracts"
BOOT_SOURCE = ROOT / "tools" / "amiga_direct_payload_bootblock.s"
VASM = ROOT / "tools" / "vasmm68k_mot.exe"
NDK_INCLUDE = ROOT / "ext" / "amiga_includes" / "ndk_2.0" / "include"
ADF_SIZE = 901_120
SECTOR_SIZE = 512
BOOT_BLOCK_SIZE = SECTOR_SIZE * 2
HANDOFF_RELEASE_VALUE = 0x474F2121  # "GO!!", the shared headless-session release token.
PAYLOAD_DISK_OFFSET = BOOT_BLOCK_SIZE


class DirectPayloadContractError(ValueError):
    """A direct-payload contract is incomplete, invalid, or mismatched."""


@dataclass(frozen=True, slots=True)
class DirectPayloadContract:
    identifier: str
    target_id: str
    payload_sha256: str
    load_address: int
    entrypoint: int
    entry_registers: dict[str, int]
    handoff_marker_address: int
    handoff_marker_value: int


def _integer(record: dict[str, object], name: str) -> int:
    value = record.get(name)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise DirectPayloadContractError(f"{name} must be an integer literal.") from exc
    raise DirectPayloadContractError(f"{name} must be an integer literal.")


def _entry_registers(record: dict[str, object]) -> dict[str, int]:
    raw = record.get("entry_registers")
    if not isinstance(raw, dict):
        raise DirectPayloadContractError("entry_registers must be an object.")
    valid_names = {f"d{index}" for index in range(8)} | {f"a{index}" for index in range(7)}
    registers: dict[str, int] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or name.lower() not in valid_names:
            raise DirectPayloadContractError("entry_registers contains an unsupported register.")
        if name.lower() in registers:
            raise DirectPayloadContractError("entry_registers contains a duplicate register.")
        registers[name.lower()] = _integer({"value": value}, "value")
    return registers


def entry_context_source(registers: dict[str, int]) -> str:
    """Render the explicit register state required by a direct-payload entry."""

    lines = ["; Generated direct-payload entry register context."]
    ordered_names = [f"d{index}" for index in range(8)] + [f"a{index}" for index in range(7)]
    for name in ordered_names:
        if name not in registers:
            continue
        opcode = "movea.l" if name.startswith("a") else "move.l"
        lines.append(f"    {opcode} #${registers[name] & 0xFFFFFFFF:08X},{name}")
    return "\n".join(lines) + "\n"


def load_contract(identifier: str, *, directory: Path = CONTRACT_DIRECTORY) -> DirectPayloadContract:
    if not identifier or Path(identifier).name != identifier:
        raise DirectPayloadContractError("Contract identifier must be a bare name.")
    path = directory / f"{identifier}.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DirectPayloadContractError(f"Direct-payload contract does not exist: {identifier}") from exc
    except json.JSONDecodeError as exc:
        raise DirectPayloadContractError(f"Direct-payload contract is invalid JSON: {identifier}") from exc
    if not isinstance(raw, dict):
        raise DirectPayloadContractError("Direct-payload contract must be a JSON object.")
    required_strings = ("identifier", "target_id", "payload_sha256")
    if not all(isinstance(raw.get(name), str) and raw[name] for name in required_strings):
        raise DirectPayloadContractError("Direct-payload contract has missing string fields.")
    contract = DirectPayloadContract(
        identifier=raw["identifier"],
        target_id=raw["target_id"],
        payload_sha256=raw["payload_sha256"].lower(),
        load_address=_integer(raw, "load_address"),
        entrypoint=_integer(raw, "entrypoint"),
        entry_registers=_entry_registers(raw),
        handoff_marker_address=_integer(raw, "handoff_marker_address"),
        handoff_marker_value=_integer(raw, "handoff_marker_value"),
    )
    if contract.identifier != identifier:
        raise DirectPayloadContractError("Contract identifier does not match its filename.")
    if len(contract.payload_sha256) != 64 or any(char not in "0123456789abcdef" for char in contract.payload_sha256):
        raise DirectPayloadContractError("payload_sha256 must be a lowercase SHA-256 digest.")
    if not all(0 <= value <= 0xFFFFFF for value in (contract.load_address, contract.entrypoint, contract.handoff_marker_address)):
        raise DirectPayloadContractError("Direct-payload addresses must be 24-bit Amiga addresses.")
    if not 0 <= contract.handoff_marker_value <= 0xFFFFFFFF:
        raise DirectPayloadContractError("handoff_marker_value must be a 32-bit value.")
    return contract


def boot_checksum(block: bytes) -> int:
    """Return the AmigaDOS boot-block checksum for a checksum-zeroed block."""

    if len(block) != BOOT_BLOCK_SIZE or int.from_bytes(block[4:8], "big") != 0:
        raise DirectPayloadContractError("Boot checksum requires a 1024-byte block with a zero checksum field.")
    total = 0
    for offset in range(0, BOOT_BLOCK_SIZE, 4):
        total += int.from_bytes(block[offset : offset + 4], "big")
        total = (total & 0xFFFFFFFF) + (total >> 32)
    return (~total) & 0xFFFFFFFF


def assemble_boot_code(contract: DirectPayloadContract, payload_size: int, *, output_path: Path) -> bytes:
    definitions = {
        "PAYLOAD_SIZE": payload_size,
        "PAYLOAD_ADDRESS": contract.load_address,
        "PAYLOAD_ENTRY": contract.entrypoint,
        "PAYLOAD_DISK_OFFSET": PAYLOAD_DISK_OFFSET,
        "HANDOFF_MARKER": contract.handoff_marker_address,
        "HANDOFF_VALUE": contract.handoff_marker_value,
        "HANDOFF_RELEASE_VALUE": HANDOFF_RELEASE_VALUE,
    }
    context_path = output_path.parent / "direct_payload_entry_context.i"
    context_path.write_text(entry_context_source(contract.entry_registers), encoding="ascii")
    command = [str(VASM), "-Fbin", "-m68000", "-I", str(output_path.parent), "-I", str(NDK_INCLUDE)]
    command.extend(f"-D{name}=${value:X}" for name, value in definitions.items())
    command.extend(("-o", str(output_path), str(BOOT_SOURCE)))
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise DirectPayloadContractError(completed.stderr.strip() or completed.stdout.strip() or "vasm failed")
        return output_path.read_bytes()
    finally:
        context_path.unlink(missing_ok=True)


def build_boot_adf(contract: DirectPayloadContract, payload_path: Path, output_path: Path) -> dict[str, object]:
    payload = payload_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != contract.payload_sha256:
        raise DirectPayloadContractError("Target payload SHA-256 does not match the direct-payload contract.")
    if not payload or len(payload) % SECTOR_SIZE:
        raise DirectPayloadContractError("Direct payload must be non-empty and sector-aligned.")
    if len(payload) > ADF_SIZE - BOOT_BLOCK_SIZE:
        raise DirectPayloadContractError("Direct payload does not fit on a DD ADF.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    code_path = output_path.with_suffix(".bootcode.bin")
    try:
        code = assemble_boot_code(contract, len(payload), output_path=code_path)
    finally:
        code_path.unlink(missing_ok=True)
    if len(code) > BOOT_BLOCK_SIZE - 12:
        raise DirectPayloadContractError("Direct boot shim exceeds the AmigaDOS boot-block code region.")
    block = bytearray(BOOT_BLOCK_SIZE)
    block[0:4] = b"DOS\0"
    block[12 : 12 + len(code)] = code
    block[4:8] = boot_checksum(block).to_bytes(4, "big")
    image = bytearray(ADF_SIZE)
    image[:BOOT_BLOCK_SIZE] = block
    image[PAYLOAD_DISK_OFFSET : PAYLOAD_DISK_OFFSET + len(payload)] = payload
    output_path.write_bytes(image)
    return {
        "status": "ok",
        "contract": contract.identifier,
        "target_id": contract.target_id,
        "payload": str(payload_path),
        "payload_sha256": digest,
        "floppy0": str(output_path),
        "load_address": f"0x{contract.load_address:08x}",
        "entrypoint": f"0x{contract.entrypoint:08x}",
        "handoff_marker_address": f"0x{contract.handoff_marker_address:08x}",
        "handoff_marker_value": f"{contract.handoff_marker_value:08x}",
    }


def build_for_target(contract_identifier: str, target_id: str, output_path: Path) -> dict[str, object]:
    contract = load_contract(contract_identifier)
    if contract.target_id != target_id:
        raise DirectPayloadContractError("Direct-payload contract is not for the requested target.")
    payload_path = resolve_project_paths(target_id).binary_source.path
    return build_boot_adf(contract, payload_path, output_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build_for_target(args.contract, args.target, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build a raw Amiga boot disk from a validated direct-payload contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

from amiga_reversing.disasm.project_paths import resolve_project_paths
from .runtime_allocation import allocation_backing, allocation_source, validate_payload as validate_allocation_payload, CPU_SCOPE, CPU_static_reservation_source

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
    reservations: tuple[tuple[int, int], ...] = ()
    materialization: dict[str, int | bool] | None = None
    initialization: tuple[int, bytes] | None = None
    # Original staged-file bytes copied by the guest shim before HAND/entry.
    # Each tuple is (file offset, destination, size), not a host memory patch.
    seed_copies: tuple[tuple[int, int, int], ...] = ()
    # Native typed allocation capsule, revalidated by the observing caller.
    runtime_allocation: dict | None = None


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


def _seed_copies(record):
    raw=record.get('seed_copies',[])
    if not isinstance(raw,list):raise DirectPayloadContractError('seed_copies must be an array')
    copies=[]
    for item in raw:
        if not isinstance(item,dict) or set(item)!={'source_offset','runtime_address','size'}:
            raise DirectPayloadContractError('Seed copies require explicit source/destination/size')
        copies.append(tuple(_integer(item,key) for key in ('source_offset','runtime_address','size')))
    return normalize_seed_copies(tuple(copies))


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
        materialization=raw.get("materialization"),
        seed_copies=_seed_copies(raw),
    )
    if contract.identifier != identifier:
        raise DirectPayloadContractError("Contract identifier does not match its filename.")
    if len(contract.payload_sha256) != 64 or any(char not in "0123456789abcdef" for char in contract.payload_sha256):
        raise DirectPayloadContractError("payload_sha256 must be a lowercase SHA-256 digest.")
    if not all(0 <= value <= 0xFFFFFF for value in (contract.load_address, contract.entrypoint, contract.handoff_marker_address)):
        raise DirectPayloadContractError("Direct-payload addresses must be 24-bit Amiga addresses.")
    if not 0 <= contract.handoff_marker_value <= 0xFFFFFFFF:
        raise DirectPayloadContractError("handoff_marker_value must be a 32-bit value.")
    validate_materialization(contract)
    return contract


def validate_materialization(contract: DirectPayloadContract, payload_size: int | None = None) -> None:
    normalize_seed_copies(contract.seed_copies, payload_size=payload_size, load_address=contract.load_address)
    m = contract.materialization
    if m is None:
        if contract.initialization is not None:
            raise DirectPayloadContractError("Initialization requires a materialization contract")
        return
    fields = {"source_offset", "size", "runtime_address", "entry_source_offset", "source_consumed_at_entry"}
    if (not isinstance(m, dict) or set(m) != fields
            or any(type(m[k]) is not int for k in fields - {"source_consumed_at_entry"})
            or m["source_consumed_at_entry"] is not True
            or m["source_offset"] < 0 or m["size"] <= 0
            or not m["source_offset"] <= m["entry_source_offset"] < m["source_offset"] + m["size"]
            or m["runtime_address"] < 0x1000
            or m["runtime_address"] + m["size"] > 0x1000000
            or (payload_size is not None and m["source_offset"] + m["size"] > payload_size)):
        raise DirectPayloadContractError("Invalid materialization/consumption contract")


def normalize_seed_copies(copies, *, payload_size=None, load_address=None):
    """Coalesce identical byte aliases; reject conflicting or live-input writes."""
    if not isinstance(copies, tuple) or len(copies)>16:
        raise DirectPayloadContractError('Seed copies require at most sixteen explicit intervals')
    ordered=[]
    for copy in copies:
        if (not isinstance(copy,tuple) or len(copy)!=3 or any(type(v) is not int for v in copy)):
            raise DirectPayloadContractError('Seed copy fields must be integers')
        source,address,size=copy
        if (source<0 or address<0x1000 or not 0<size<=0x10000 or address+size>0x1000000
                or (payload_size is not None and source+size>payload_size)):
            raise DirectPayloadContractError('Seed copy has invalid source/destination bounds')
        if payload_size is not None and load_address is not None:
            if address<load_address+payload_size and load_address<address+size and address!=load_address+source:
                raise DirectPayloadContractError('Seed copy would overwrite live input bytes')
        ordered.append((source,address,size))
    merged=[]
    for source,address,size in sorted(ordered,key=lambda c:c[1]):
        if merged and address<merged[-1][1]+merged[-1][2]:
            old_source,old_address,old_size=merged[-1]
            if source-address!=old_source-old_address:
                raise DirectPayloadContractError('Conflicting overlapping seed byte aliases')
            length=max(old_address+old_size,address+size)-old_address
            if length>0x10000:raise DirectPayloadContractError('Coalesced seed exceeds bounded copy loop')
            merged[-1]=(old_source,old_address,length)
        else:merged.append((source,address,size))
    if len(merged)>8:raise DirectPayloadContractError('Boot shim supports at most eight disjoint seed copies')
    return tuple(merged)


def rounded_reservation_span(address, size):
    """Exec ownership rounding, not a claim about padding byte purposes."""
    return address & ~7, ((address+size+7)&~7)-(address&~7)


def seed_reservation_spans(copies):
    """Exec ownership rounding is not an assertion about extra byte purposes."""
    return tuple(rounded_reservation_span(address,size)
                 for _,address,size in normalize_seed_copies(copies))


def boot_checksum(block: bytes) -> int:
    """Return the AmigaDOS boot-block checksum for a checksum-zeroed block."""

    if len(block) != BOOT_BLOCK_SIZE or int.from_bytes(block[4:8], "big") != 0:
        raise DirectPayloadContractError("Boot checksum requires a 1024-byte block with a zero checksum field.")
    total = 0
    for offset in range(0, BOOT_BLOCK_SIZE, 4):
        total += int.from_bytes(block[offset : offset + 4], "big")
        total = (total & 0xFFFFFFFF) + (total >> 32)
    return (~total) & 0xFFFFFFFF


def reservation_plan(contract: DirectPayloadContract, payload_size: int) -> tuple[tuple[int, int], ...]:
    """Own input and requested storage before I/O; overlapping claims share backing.

    Exec rounds allocations to eight-byte chunks. The input remains allocated
    through handoff and consumption: the shim never frees it or allocates again
    after reading. Containment is ownership only, not permission to initialize a
    destination while it still holds live input bytes.
    """
    marker = contract.handoff_marker_address
    if type(marker) is not int or marker < 0x1008 or marker > 0xFFFFFC or marker % 4:
        raise DirectPayloadContractError("Invalid handoff marker reservation")
    spans = []
    allocation_spans = ()
    if contract.runtime_allocation is not None:
        allocation_spans = allocation_backing(contract.runtime_allocation, marker)
    for address, size in (*contract.reservations, *seed_reservation_spans(contract.seed_copies), *allocation_spans):
        if (type(address) is not int or type(size) is not int or address % 8
                or size <= 0 or size % 8 or address < 0x1000
                or address + size > 0x1000000):
            raise DirectPayloadContractError("Invalid exact Exec reservation")
        if address < contract.handoff_marker_address + 4 and contract.handoff_marker_address - 8 < address + size:
            raise DirectPayloadContractError("Runtime reservation overlaps the handoff markers")
        spans.append((address, address + size))
    start, end = contract.load_address, contract.load_address + payload_size
    if (type(payload_size) is not int or payload_size <= 0 or start % 8
            or start < 0x1000 or end > 0x1000000):
        raise DirectPayloadContractError("Invalid payload backing reservation")
    if start < contract.handoff_marker_address + 4 and contract.handoff_marker_address - 8 < end:
        raise DirectPayloadContractError("Loaded payload overlaps the handoff markers")
    spans.append((start, (end + 7) & ~7))
    # Own marker storage first, so later allocation failures can safely publish
    # FAIL. Failure of this first allocation must not write an unowned marker.
    marker_span = ((marker - 8) & ~7, (marker + 11) & ~7)
    if any(start < marker_span[1] and marker_span[0] < end for start, end in spans):
        raise DirectPayloadContractError("Reservation overlaps the handoff marker envelope")
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return ((marker_span[0], marker_span[1]-marker_span[0]),) + tuple((start, end - start) for start, end in merged)


def seed_copy_source(contract, payload_size):
    lines=[]
    for index,(source,address,size) in enumerate(normalize_seed_copies(contract.seed_copies,
            payload_size=payload_size,load_address=contract.load_address)):
        lines.extend((f"    movea.l #${contract.load_address+source:X},a0",f"    movea.l #${address:X},a1",
            f"    move.l #${size-1:X},d0",f"loader_seed_copy_{index}:","    move.b (a0)+,(a1)+",
            f"    dbra.w d0,loader_seed_copy_{index}"))
    return '\n'.join(lines)+'\n'


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
    reservation_path = output_path.parent / "direct_payload_reservations.i"
    seed_path = output_path.parent / "direct_payload_seed_copies.i"
    reservation_lines=[]
    spans=reservation_plan(contract,payload_size)
    if contract.runtime_allocation is not None:reservation_lines.append('    moveq #0,d4')
    for index,(address,size) in enumerate(spans):
        reservation_lines.extend((f"    move.l #${size:X},d0", f"    movea.l #${address:X},a1",
            "    jsr _LVOAllocAbs(a6)", f"    cmpi.l #${address:X},d0", "    bne.w reservation_unowned" if index == 0 else "    bne.w failed"))
        if contract.runtime_allocation is not None:
            reservation_lines.extend(('    addq.l #1,d4',f'    move.l d4,${contract.handoff_marker_address-4:X}'))
            if index==0:
                reservation_lines.extend(('    lea start(pc),a0',f'    move.l a0,${contract.handoff_marker_address-8:X}'))
    if contract.runtime_allocation is not None and contract.runtime_allocation['plan']['scope']==CPU_SCOPE:
        reservation_lines=CPU_static_reservation_source(contract.runtime_allocation,spans,contract.handoff_marker_address)
    command = [str(VASM), "-Fbin", "-m68000", "-I", str(output_path.parent), "-I", str(NDK_INCLUDE)]
    command.extend(f"-D{name}=${value:X}" for name, value in definitions.items())
    allocation_files=[]
    listing_path=output_path.with_suffix('.allocation.lst')
    if contract.runtime_allocation is not None:
        generated,constants=allocation_source(contract.runtime_allocation,contract,payload_size,spans)
        for name,text in generated.items():
            path=output_path.parent/name;path.write_text(text,encoding='ascii');allocation_files.append(path)
        command.extend('-D'+key+'='+str(value) for key,value in constants.items())
        command.extend(('-I',str(ROOT/'tools'),'-L',str(listing_path)))
    command.extend(("-o", str(output_path), str(BOOT_SOURCE)))
    try:
        context_path.write_text(entry_context_source(contract.entry_registers), encoding="ascii")
        reservation_path.write_text("\n".join(reservation_lines)+"\n", encoding="ascii")
        seed_path.write_text(seed_copy_source(contract,payload_size), encoding="ascii")
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise DirectPayloadContractError(completed.stderr.strip() or completed.stdout.strip() or "vasm failed")
        return output_path.read_bytes()
    finally:
        context_path.unlink(missing_ok=True)
        reservation_path.unlink(missing_ok=True)
        seed_path.unlink(missing_ok=True)
        for path in allocation_files:path.unlink(missing_ok=True)


def build_boot_adf(contract: DirectPayloadContract, payload_path: Path, output_path: Path) -> dict[str, object]:
    payload = payload_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != contract.payload_sha256:
        raise DirectPayloadContractError("Target payload SHA-256 does not match the direct-payload contract.")
    if not payload or len(payload) % SECTOR_SIZE:
        raise DirectPayloadContractError("Direct payload must be non-empty and sector-aligned.")
    if len(payload) > ADF_SIZE - BOOT_BLOCK_SIZE:
        raise DirectPayloadContractError("Direct payload does not fit on a DD ADF.")
    validate_materialization(contract, len(payload))
    if contract.runtime_allocation is not None:
        validate_allocation_payload(contract.runtime_allocation,payload,contract.load_address,
            contract.handoff_marker_address,contract.seed_copies)
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
    report = {
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
    if contract.seed_copies:
        report['seed_copies']=[dict(source_offset=s,runtime_address=a,size=n,
            staging_address=contract.load_address+s,source_sha256=hashlib.sha256(payload[s:s+n]).hexdigest(),
            phase='guest_shim_before_handoff') for s,a,n in normalize_seed_copies(contract.seed_copies,
                payload_size=len(payload),load_address=contract.load_address)]
    if contract.runtime_allocation is not None:
        import re
        listing=code_path.with_suffix('.allocation.lst').read_text()
        wanted={'allocation_abort_publish','allocation_abort_wait','allocation_closed'}
        symbols={name:int(address,16) for address,name in re.findall(r'^([0-9A-Fa-f]{8}) (allocation_[A-Za-z_]+)$',listing,re.M) if name in wanted}
        if set(symbols)!=wanted:raise DirectPayloadContractError('Missing exact allocation debug symbols')
        report['allocation_boot_symbols']=symbols
        report['allocation_boot_code_size']=len(code)
        report['allocation_boot_code_sha256']=hashlib.sha256(code).hexdigest()
    return report


def bind_derived_contract(contract: DirectPayloadContract, manifest_path: Path) -> tuple[DirectPayloadContract, Path, dict]:
    from amiga_reversing.tools.runtime_analysis import build_project_listing_artifact_profile
    from amiga_reversing.disasm.derived_artifact import validate_manifest, verify_native_binding
    manifest,payload_path=validate_manifest(manifest_path,contract.target_id)
    if manifest["original_sha256"]!=contract.payload_sha256:
        raise DirectPayloadContractError("Derived artifact base does not match the direct contract")
    _,_,artifact=build_project_listing_artifact_profile(contract.target_id)
    try:
        verify_native_binding(manifest,artifact)
        if manifest.get("initialization") is not None:
            verify_materialization_binding(contract, artifact)
    finally:
        artifact.close()
    if manifest.get('kind') == 'fixed_size_optional_patch':
        validate_materialization(contract, payload_path.stat().st_size)
        return replace(contract, payload_sha256=manifest['output_sha256']), payload_path, manifest
    placement=manifest["placement"]
    address,size=placement["runtime_address"],manifest["region"]["size"]
    reservation_size=(size+7)&~7
    payload_end=contract.load_address+payload_path.stat().st_size
    initialization = manifest.get("initialization")
    validate_materialization(contract, payload_path.stat().st_size)
    if initialization is not None:
        m = contract.materialization
        if m is None:
            raise DirectPayloadContractError("Mapped initialization requires a materialization contract")
        source = initialization["source_offset"]
        if (initialization["section_index"] != 0 or source < m["source_offset"]
                or source + size > m["source_offset"] + m["size"]
                or manifest["region"]["runtime_address"] != m["runtime_address"] + source - m["source_offset"]):
            raise DirectPayloadContractError("Initialization does not belong to the copied source view")
        if address < m["runtime_address"] + m["size"] and m["runtime_address"] < address + reservation_size:
            raise DirectPayloadContractError("Runtime reservation overlaps materialized game storage")
    if address < payload_end and contract.load_address < address+reservation_size:
        m = contract.materialization
        if (initialization is None or m is None
                or address < contract.load_address + m["source_offset"]
                or address + reservation_size > contract.load_address + m["source_offset"] + m["size"]):
            raise DirectPayloadContractError("Runtime reservation overlaps unconsumed loaded payload")
    if address < contract.handoff_marker_address+4 and contract.handoff_marker_address-8 < address+size:
        raise DirectPayloadContractError("Runtime reservation overlaps the handoff markers")
    return replace(contract,payload_sha256=manifest["artifact_sha256"],reservations=((address,reservation_size),),
        initialization=(address,bytes.fromhex(initialization["bytes"])) if initialization is not None else None),payload_path,manifest


def verify_materialization_binding(contract: DirectPayloadContract, artifact) -> None:
    """Bind a declared consumption boundary to the canonical native copy view.

    Consumption after that entry is an explicit loader contract, not a claim
    inferred from absence of reads or from an observational mapping.
    """
    validate_materialization(contract)
    m = contract.materialization
    if m is None:
        raise DirectPayloadContractError("Mapped initialization requires a materialization contract")
    analysis, _ = artifact.analysis_payload()
    views = [v for s in analysis["sections"] if s["section_index"] == 0
        for v in s.get("runtime_views", [])
        if v.get("materialized") and v.get("storage_offset") == m["source_offset"]
        and v.get("size") == m["size"] and v.get("runtime_address") == m["runtime_address"]]
    entry = m["runtime_address"] + m["entry_source_offset"] - m["source_offset"]
    resolved = artifact.source_for_runtime_address(address=entry)
    instructions = artifact.query_payload("instructions", section_index=0,
        source_offset=m["entry_source_offset"], limit=2)
    if (len(views) != 1 or resolved.get("status") != "resolved"
            or resolved.get("section_index") != 0 or resolved.get("source_offset") != m["entry_source_offset"]
            or not any(i.get("source_offset") == m["entry_source_offset"] for i in instructions["items"])):
        raise DirectPayloadContractError("Materialization boundary is not a unique native copy view and instruction")


def build_for_target(contract_identifier: str, target_id: str, output_path: Path, *, derived_manifest: Path | None = None) -> dict[str, object]:
    contract = load_contract(contract_identifier)
    if contract.target_id != target_id:
        raise DirectPayloadContractError("Direct-payload contract is not for the requested target.")
    payload_path = resolve_project_paths(target_id).binary_source.path
    manifest=None
    if derived_manifest is not None:
        contract,payload_path,manifest=bind_derived_contract(contract,derived_manifest)
    result=build_boot_adf(contract, payload_path, output_path)
    if manifest is not None:
        result["derived_manifest"]=str(derived_manifest.resolve())
        result["original_sha256"]=manifest["original_sha256"]
        if manifest.get('kind') == 'fixed_size_optional_patch':
            result['optional_patches'] = manifest['enabled']
        else:
            result["reservation"]=manifest["placement"] | {"size":manifest["region"]["size"]}
    return result


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

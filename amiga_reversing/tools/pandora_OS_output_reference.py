"""Build a bounded native-ASM output control at observed DOS allocator bases.

This is a temporary configuration of the existing native renderer, not a new
saved layout, placement solver, source patcher or original-vs-restored proof.
The reference tests runtime fixups against assembly-time bindings under the same
OS wrapper; shared wrapper behaviour needs separate evidence.
"""

import hashlib
import json
import subprocess
import time
from pathlib import Path
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import resolve_project_paths, PROJECT_ROOT
from amiga_reversing.disasm.c_backend import (
    build_listing_artifact_profile_from_binary_source,
    assemble_platform_source_path_with_c_backend,
)
from amiga_reversing.disasm.source_rendering import render_source_from_binary_source
from amiga_reversing.disasm.hosted_application_export import native_contract
from amiga_reversing.tools.pandora_layout_walkthrough import TARGET
from amiga_reversing.tools.pandora_OS_application import application_sources,OWNERS,IMAGE_OWNER
from amiga_reversing.disasm.effective_metadata import effective_metadata_hash
from amiga_reversing.disasm.behaviour_validation import LoadedSource

LOADED_SOURCE = LoadedSource(__file__)


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_reference_bytes(data, runtime_payload, imported):
    require(
        imported.get("width") == 4
        and imported.get("role") == "host_mission_restart_dispatch",
        "Only the native typed HUNK import may be normalized",
    )
    offset, value = imported["source_offset"], imported["staged_value"]
    require(
        type(offset) is int
        and 0 <= offset <= len(data) - 4
        and type(value) is int
        and 0 <= value <= 0xFFFFFFFF,
        "Invalid typed import coordinates",
    )
    require(
        len(data) == len(runtime_payload), "Reference/runtime payload lengths differ"
    )
    expected = bytearray(runtime_payload)
    expected[offset : offset + 4] = value.to_bytes(4, "big")
    if data != expected:
        differences = [i for i, (a, b) in enumerate(zip(expected, data)) if a != b]
        raise ValueError(
            "Native ASM/runtime bytes differ outside import: " + str(differences[:32])
        )


def audit_assets_dma(native, payload, asset_manifest, directories, *, original=None):
    """Use canonical asset spans and the existing bus parser; two-frame scope."""
    from collections import Counter
    from amiga_reversing.tools.copperline_bus_trace import read_bus_profile, SLOT, KINDS
    from amiga_reversing.tools.pandora_rebase_output_compare import (
        display_ranges,
        cursor_range,
    )

    if original is None:
        from amiga_reversing.disasm.binary_source import read_binary_source_bytes

        original = read_binary_source_bytes(resolve_project_paths(TARGET).binary_source)
    require(
        hashlib.sha256(original).hexdigest()
        == asset_manifest["manifest"]["target_identity_sha256"],
        "Asset manifest belongs to a different original binary",
    )
    assets = [r for r in asset_manifest["manifest"]["files"] if r["kind"] == "asset"]
    for item in assets:
        start, size = item["source_offset"], item["size"]
        require(
            item["source_section_index"] == 0
            and start + size <= len(payload)
            and original[start : start + size] == payload[start : start + size]
            and hashlib.sha256(payload[start : start + size]).hexdigest()
            == item["sha256"],
            "Canonical asset bytes differ: " + item["path"],
        )
    # Same eleven original length/divisor/payload records used by the existing
    # rebase-output comparator, followed by the declared silence/secondary bank.
    audio, position = [], 0x4EAD8
    for _ in range(11):
        length = int.from_bytes(payload[position : position + 4], "big")
        divisor = int.from_bytes(payload[position + 4 : position + 6], "big")
        start = position + 6
        require(
            0 < length < 0x10000 and divisor > 0 and start + length <= 0x55370,
            "Invalid original audio record",
        )
        audio.append((start, start + length))
        position = start + length
    require(position == 0x5500A, "Original audio-bank extent differs")
    require(
        original[0x4EAD8:0x552CA] == payload[0x4EAD8:0x552CA],
        "Primary headers/samples, silence or secondary audio bank changed",
    )
    require(
        original[0x4D5DE:0x4D7DE] == payload[0x4D5DE:0x4D7DE],
        "Blank sprite bytes changed",
    )
    audio += [(0x5500A, 0x5504A), (0x5504A, 0x552CA)]
    plan = native["layout"]["items"][0]
    image = next(r for r in plan["regions"] if r["region_kind"] == "image")
    base = image["runtime_address"]
    adapter = dict(config=dict(normal_layout_export=True, layout_plan=plan))
    bounds = dict(
        audio=[(base + a, base + b) for a, b in audio],
        copper=[(base, base + image["size"])],
        bitplane=[(a, b) for _, a, b in display_ranges(adapter)],
        sprite=[(base + 0x4D5DE, base + 0x4D7DE), cursor_range(adapter)],
    )
    observations = []
    for directory in directories:
        checked = read_bus_profile(directory, [], 3)
        complete = [f for f in checked["frames"] if not f.get("partial")][-2:]
        require(len(complete) == 2, "Missing complete title DMA frames")
        wanted = {f["frame"] for f in complete}
        counts, exceptions = Counter(), []
        for frame in map(
            json.loads, directory.joinpath("profile.jsonl").read_text().splitlines()
        ):
            if frame["frame"] not in wanted:
                continue
            for (
                reg,
                kind,
                subtype,
                size,
                ipl,
                flags,
                address,
                data,
                events,
            ) in SLOT.iter_unpack((directory / frame["slots_file"]).read_bytes()):
                engine = KINDS.get(kind)
                if engine not in (*bounds, "blitter") or not 1 <= size <= 8:
                    continue
                counts[engine] += 1
                if engine not in bounds:
                    continue  # Recorded, but blitter object bounds are not admitted here.
                if engine == "sprite" and address in (2, 6) and size == 2:
                    exceptions.append(dict(engine=engine, address=address, width=size))
                    continue
                require(
                    any(
                        lo <= address and address + size <= hi
                        for lo, hi in bounds[engine]
                    ),
                    f"DMA outside declared {engine} bounds: {address:#x}+{size}",
                )
        require(all(counts[name] > 0 for name in ("audio", "bitplane", "copper")),
                "Required title audio/display/Copper transfers were not observed")
        observations.append(
            dict(
                complete_frames=sorted(wanted),
                transfers=dict(counts),
                explicit_null_sprite_exceptions=exceptions,
                unobserved_engines=[
                    name for name in ("sprite", "blitter") if not counts[name]
                ],
                slots_sha256=[f["slots_sha256"] for f in complete],
            )
        )
    return dict(
        status="pass_scoped_asset_integrity_and_sampled_DMA_bounds",
        unchanged_asset_spans=len(assets),
        unchanged_asset_bytes=sum(r["size"] for r in assets),
        eleven_primary_audio_records=True,
        bounds=bounds,
        observations=observations,
        limits=[
            "Canonical asset spans only, not semantic identification of every remaining byte.",
            "Two complete title frames per capture; not whole-route DMA coverage.",
            "Copper bounds are the moved image, not a separate per-list execution proof.",
            "Blitter object/alias bounds and unobserved sprites are not qualified here.",
            "Historical null sprite0/2 behaviour remains an explicit exception, not a moved asset claim.",
        ],
    )


def build(output, runtime_payload, owners_receipt):
    LOADED_SOURCE.require_current()
    out = output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    paths = resolve_project_paths(TARGET)
    layout = "pandora_OS_hosted_ecs1m"
    receipt = owners_receipt
    owners = json.loads(receipt.read_text())["actual_owners"]
    require(set(owners) in (set(OWNERS),set((*OWNERS,IMAGE_OWNER))),
        "Unsupported hosted reference owner set")
    canonical = effective_metadata_hash(paths.target_dir)
    with effective_metadata_file(paths.target_dir, layout_id=layout) as original:
        metadata = json.loads(original.read_text())
        config = next(v for v in metadata["memory_layouts"] if v["layout_id"] == layout)
        indexed = {v["region_id"]: v for v in config["placements"]}
        for name, address in owners.items():
            if name in indexed:
                indexed[name]["runtime_address"] = address
            else:
                config["placements"].append(
                    dict(region_id=name, runtime_address=address)
                )
        local = out / "reference-metadata.json"
        local.write_text(json.dumps(metadata, sort_keys=True) + "\n")
        print("BUILD_NATIVE_REFERENCE", flush=True)
        start = time.monotonic()
        artifact = build_listing_artifact_profile_from_binary_source(
            paths.binary_source, metadata_path=local, project_root=PROJECT_ROOT
        )[2]
        try:
            contract = native_contract(artifact, TARGET, layout,
                allocate_image=IMAGE_OWNER in owners)
            rendering = render_source_from_binary_source(
                target_id=TARGET,
                binary_source=paths.binary_source,
                target_dir=paths.target_dir,
                metadata_path=local,
                project_root=PROJECT_ROOT,
                workflow_id="source_export",
                use_persisted_policy=False,
                artifact=artifact,
            )
            require(not rendering.refused, "Native reference source refused")
            source = out / "game.s"
            source.write_text(rendering.source_text)
            data, _ = assemble_platform_source_path_with_c_backend(
                "amiga-raw",
                source,
                include_dir=PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include",
                target_cpu="68000",
                project_root=PROJECT_ROOT,
            )
            (out / "Pandora.payload").write_bytes(data)
            subprocess.run(
                [
                    str(PROJECT_ROOT / "tools/vasmm68k_mot.exe"),
                    "-Fbin",
                    "-m68000",
                    "-no-opt",
                    "-I" + str(PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include"),
                    "-o",
                    str(out / "vasm.bin"),
                    str(source),
                ],
                check=True,
                capture_output=True,
            )
            require(
                (out / "vasm.bin").read_bytes() == data,
                "Native C/vasm reference mismatch",
            )
            imported = contract["template_geometry"]["layout"]["items"][0]["bootstrap"][
                "exit_dispatch_import"
            ]
            verify_reference_bytes(data, runtime_payload.read_bytes(), imported)
            files, _ = application_sources(
                data,
                contract,
                game=True,
                expected_payload_sha256=hashlib.sha256(data).hexdigest(),
            )
            for name, contents in files.items():
                (out / name).write_bytes(contents)
            subprocess.run(
                [
                    str(PROJECT_ROOT / "tools/vasmm68k_mot.exe"),
                    "-Fhunkexe",
                    "-m68000",
                    "-no-opt",
                    "-I" + str(out),
                    "-I" + str(PROJECT_ROOT / "ext/amiga_includes/ndk_2.0/include"),
                    "-L",
                    str(out / "Pandora.list"),
                    "-o",
                    str(out / "Pandora"),
                    str(out / "amiga_pandora_OS.s"),
                ],
                check=True,
                capture_output=True,
            )
            (out / "native-contract.json").write_text(
                json.dumps(contract, indent=2) + "\n"
            )
            require(
                effective_metadata_hash(paths.target_dir) == canonical,
                "Canonical model changed during reference build",
            )
            LOADED_SOURCE.require_current()
            result = dict(
                canonical_metadata_hash=canonical,
                runtime_payload_sha256=hashlib.sha256(
                    runtime_payload.read_bytes()
                ).hexdigest(),
                native_contract_sha256=hashlib.sha256(
                    (out / "native-contract.json").read_bytes()
                ).hexdigest(),
                status="native_ASM_reference_matches_all_runtime_fixed_bytes_except_typed_HUNK_import",
                metadata_sha256=hashlib.sha256(local.read_bytes()).hexdigest(),
                observed_receipt_sha256=hashlib.sha256(
                    receipt.read_bytes()
                ).hexdigest(),
                payload_sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data),
                backend=artifact.loaded_backend_identity(),
                wall_seconds=time.monotonic() - start,
                temporary_configuration_only=True,
            )
            (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result), flush=True)
        finally:
            artifact.close()
    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--runtime-payload",
        type=Path,
        required=True,
        help="Private complete input snapshot after the observed runtime fixes/import",
    )
    parser.add_argument(
        "--owners-receipt",
        type=Path,
        default=PROJECT_ROOT
        / "runtime/observations/pandora-normal-HUNK-game-lifecycle.json",
    )
    args = parser.parse_args()
    build(args.output, args.runtime_payload, args.owners_receipt)


if __name__ == "__main__":
    main()

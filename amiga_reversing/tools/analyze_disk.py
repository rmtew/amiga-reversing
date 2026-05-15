"""Analyze Amiga ADF disk images."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from amiga_reversing.amiga_disk.adf import DiskAnalysisError, analyze_adf
from amiga_reversing.amiga_disk.models import AdfAnalysis, BootloaderTransferKind


def print_summary(result: AdfAnalysis) -> None:
    info = result.disk_info
    boot = result.boot_block
    if result.bootloader_analysis is None:
        raise DiskAnalysisError("ADF analysis is missing bootloader_analysis")
    if result.track_analysis is not None and result.trackloader_analysis is None:
        raise DiskAnalysisError("ADF analysis is missing trackloader_analysis for track analysis")
    print(f"=== {info.path} ===")
    print(f"  Size: {info.size} bytes ({info.variant})")
    print(f"  Sectors: {info.total_sectors}")
    print(
        f"  Boot: {'DOS' if info.is_dos else 'Non-DOS'} "
        f"(checksum {'OK' if boot.checksum_valid else 'FAIL'})"
    )
    if boot.fs_description:
        print(f"  Filesystem: {boot.fs_description}")
    if boot.bootcode_has_code:
        print(f"  Boot code: yes (entropy: {boot.bootcode_entropy})")
    if result.filesystem is not None and result.bitmap is not None:
        filesystem = result.filesystem
        bitmap = result.bitmap
        print(f"\n  Volume: {filesystem.volume_name}")
        print(f"  Files: {filesystem.files}, Directories: {filesystem.directories}")
        print(f"  Total file data: {filesystem.total_file_size:,} bytes")
        print(
            f"  Blocks: {bitmap.allocated_blocks} allocated, "
            f"{bitmap.free_blocks} free ({bitmap.percent_used}% used)"
        )
        imported_candidates = [
            entry for entry in (result.files or [])
            if entry.content is not None and entry.content.is_executable is True
        ]
        if imported_candidates:
            print(f"  Hunk executables: {len(imported_candidates)}")
    if result.track_analysis is not None:
        track_analysis = result.track_analysis
        print(
            f"\n  Tracks: {track_analysis.total_tracks} total, "
            f"{track_analysis.non_empty_tracks} non-empty"
        )
    if result.trackloader_analysis is not None:
        trackloader = result.trackloader_analysis
        if trackloader.boot_ascii_strings:
            print(f"  Boot strings: {len(trackloader.boot_ascii_strings)}")
        if trackloader.candidate_code_tracks:
            print(f"  Candidate code tracks: {', '.join(str(track) for track in trackloader.candidate_code_tracks[:12])}")
        if trackloader.nonempty_track_spans:
            spans = ", ".join(
                f"{span.start_track}-{span.end_track}" if span.start_track != span.end_track else str(span.start_track)
                for span in trackloader.nonempty_track_spans[:8]
            )
            print(f"  Non-empty spans: {spans}")
    if result.bootloader_analysis.stages:
        print("  Memory regions:")
        for region in result.bootloader_analysis.memory_regions[:12]:
            print(
                f"    {region.stage_name} {region.region_kind}: "
                f"{region.base_addr:#x}..{region.base_addr + region.byte_length - 1:#x} "
                f"materialized={region.materialized}"
            )
        print("  Transfers:")
        for transfer in result.bootloader_analysis.transfers[:16]:
            if transfer.transfer_kind is BootloaderTransferKind.DISK_READ:
                print(
                    f"    {transfer.stage_name}: disk {transfer.disk_offset:#x} -> "
                    f"{transfer.destination_addr:#x} bytes={transfer.byte_length:#x}"
                )
                continue
            if transfer.transfer_kind is BootloaderTransferKind.MEMORY_COPY:
                print(
                    f"    {transfer.stage_name}: copy {transfer.source_addr:#x} -> "
                    f"{transfer.destination_addr:#x} bytes={transfer.byte_length:#x}"
                )
                continue
            if transfer.transfer_kind is BootloaderTransferKind.DECODE:
                parts = [
                    f"{transfer.stage_name}: decode",
                    f"input={transfer.input_buffer_addr:#x}" if transfer.input_buffer_addr is not None else "input=?",
                    f"output={transfer.destination_addr:#x}" if transfer.destination_addr is not None else "output=?",
                ]
                if transfer.byte_length is not None:
                    parts.append(f"bytes={transfer.byte_length:#x}")
                if transfer.start_track is not None:
                    span = (
                        f"{transfer.start_track}-{transfer.end_track}"
                        if transfer.end_track is not None and transfer.end_track != transfer.start_track
                        else str(transfer.start_track)
                    )
                    parts.append(f"track_span={span}")
                if transfer.start_byte_offset is not None:
                    parts.append(f"disk_byte={transfer.start_byte_offset:#x}")
                if transfer.checksum_gate_kind is not None:
                    parts.append(f"gate={transfer.checksum_gate_kind}@{transfer.checksum_gate_addr:#x}")
                print(f"    {' '.join(parts)}")
                continue
            if transfer.transfer_kind is BootloaderTransferKind.HANDOFF:
                print(f"    {transfer.stage_name}: jump -> {transfer.target_addr:#x} ({transfer.source_kind})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Amiga ADF disk images")
    parser.add_argument("adf_file", help="Path to ADF file")
    parser.add_argument(
        "-o",
        "--output",
        choices=["json", "summary"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument("--outfile", help="Write JSON output to file")
    parser.add_argument(
        "--extract",
        metavar="DIR",
        help="Extract files to directory (AmigaDOS disks only)",
    )
    parser.add_argument(
        "--tracks",
        action="store_true",
        help="Include per-track analysis",
    )
    args = parser.parse_args()

    try:
        result = analyze_adf(
            args.adf_file,
            extract_dir=args.extract,
            include_tracks=args.tracks,
        )
    except DiskAnalysisError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output == "json" or args.outfile:
        json_text = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        if args.outfile:
            Path(args.outfile).write_text(json_text, encoding="utf-8")
        else:
            print(json_text)
        return 0

    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

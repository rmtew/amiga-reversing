from __future__ import annotations

import argparse
import faulthandler
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.c_backend import render_binary_source_with_c_backend


class StageTimer:
    """Optional wall-clock timing for coarse generator stages."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.samples: list[tuple[str, float]] = []

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            if self.enabled:
                self.samples.append((name, time.perf_counter() - start))

    def format_lines(self) -> list[str]:
        if not self.enabled:
            return []
        return [f"  timing {name}: {elapsed:.3f}s"
                for name, elapsed in self.samples]


def gen_disasm(binary_path: str, entities_path: str, output_path: str,
               base_addr: int = 0, code_start: int = 0,
               assembler_profile_name: str = "vasm",
               profile_stages: bool = False,
               stall_timeout: float | None = None) -> None:
    """Generate assembler-profiled .s output through the canonical row pipeline."""
    stage_timer = StageTimer(enabled=profile_stages)
    if stall_timeout:
        faulthandler.dump_traceback_later(stall_timeout, repeat=True)

    try:
        print(f"Rendering {output_path}...")
        with stage_timer.measure("render_text"):
            text = render_binary_source_with_c_backend(binary_path)
        assembler_profile = load_assembler_profile(assembler_profile_name)
        newline = "\n" if assembler_profile.render.line_ending == "lf" else "\r\n"

        tmp_output = Path(str(output_path) + ".tmp")
        with stage_timer.measure("write_output"):
            tmp_output.write_text(text, encoding="utf-8", newline=newline)
            tmp_output.replace(output_path)

        for line in stage_timer.format_lines():
            print(line)
        print(f"\nDone: {output_path}")
    finally:
        if stall_timeout:
            faulthandler.cancel_dump_traceback_later()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate assembler-profiled .s file from binary analysis")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--entities", "-e",
                        help="Legacy override path; ignored by current C analysis rendering")
    parser.add_argument("--output", "-o",
                        help="Output .s file path")
    parser.add_argument("--target-dir", "-t",
                        help="Target output directory (e.g. targets/amiga_hunk_genam)")
    parser.add_argument("--base-addr", type=lambda x: int(x, 0),
                        default=0,
                        help="Runtime base address (e.g. 0x400)")
    parser.add_argument("--code-start", type=lambda x: int(x, 0),
                        default=0,
                        help="Byte offset where code begins (skips bootstrap)")
    parser.add_argument("--profile-stages", action="store_true",
                        help="Print coarse wall-clock timing for major stages")
    parser.add_argument(
        "--assembler-profile",
        choices=("vasm", "devpac"),
        default="vasm",
        help="Assembler render profile to use for emitted source",
    )
    parser.add_argument("--stall-timeout", type=float,
                        help="Dump Python traceback every N seconds while running")
    args = parser.parse_args(argv)

    target_dir = args.target_dir
    entities = args.entities or (str(Path(target_dir) / "entities.jsonl") if target_dir else "entities.jsonl")
    output = args.output or (str(Path(target_dir) / (Path(args.binary).stem + ".s")) if target_dir else "amiga_reversing.disasm.s")

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    gen_disasm(args.binary, entities, output,
               base_addr=args.base_addr,
               code_start=args.code_start,
               assembler_profile_name=args.assembler_profile,
               profile_stages=args.profile_stages,
               stall_timeout=args.stall_timeout)

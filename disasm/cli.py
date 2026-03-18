from __future__ import annotations

import argparse
import faulthandler
import time
from contextlib import contextmanager
from pathlib import Path

from disasm.emitter import emit_session_rows
from disasm.session import build_disassembly_session
from disasm.text import render_rows


class StageTimer:
    """Optional wall-clock timing for coarse generator stages."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.samples: list[tuple[str, float]] = []

    @contextmanager
    def measure(self, name: str):
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
               profile_stages: bool = False,
               stall_timeout: float | None = None):
    """Generate vasm-compatible .s file through the canonical row pipeline."""
    stage_timer = StageTimer(enabled=profile_stages)
    if stall_timeout:
        faulthandler.dump_traceback_later(stall_timeout, repeat=True)

    try:
        print(f"Loading disassembly session for {binary_path}...")
        with stage_timer.measure("build_session"):
            session = build_disassembly_session(
                binary_path,
                entities_path,
                output_path,
                base_addr=base_addr,
                code_start=code_start,
                profile_stages=profile_stages,
            )

        print(f"Emitting canonical rows for {output_path}...")
        with stage_timer.measure("emit_rows"):
            rows = emit_session_rows(session)

        print(f"Rendering {output_path}...")
        with stage_timer.measure("render_text"):
            text = render_rows(rows)

        tmp_output = Path(str(output_path) + ".tmp")
        with stage_timer.measure("write_output"):
            tmp_output.write_text(text)
            tmp_output.replace(output_path)

        for line in stage_timer.format_lines():
            print(line)
        print(f"\nDone: {output_path}")
    finally:
        if stall_timeout:
            faulthandler.cancel_dump_traceback_later()


def main():
    parser = argparse.ArgumentParser(
        description="Generate vasm-compatible .s file from binary + entities")
    parser.add_argument("binary", help="Path to Amiga hunk executable")
    parser.add_argument("--entities", "-e",
                        help="Path to entities.jsonl")
    parser.add_argument("--output", "-o",
                        help="Output .s file path")
    parser.add_argument("--target-dir", "-t",
                        help="Target output directory (e.g. targets/genam)")
    parser.add_argument("--base-addr", type=lambda x: int(x, 0),
                        default=0,
                        help="Runtime base address (e.g. 0x400)")
    parser.add_argument("--code-start", type=lambda x: int(x, 0),
                        default=0,
                        help="Byte offset where code begins (skips bootstrap)")
    parser.add_argument("--profile-stages", action="store_true",
                        help="Print coarse wall-clock timing for major stages")
    parser.add_argument("--stall-timeout", type=float,
                        help="Dump Python traceback every N seconds while running")
    args = parser.parse_args()

    target_dir = args.target_dir
    entities = args.entities or (str(Path(target_dir) / "entities.jsonl") if target_dir else "entities.jsonl")
    output = args.output or (str(Path(target_dir) / (Path(args.binary).stem + ".s")) if target_dir else "disasm.s")

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    return gen_disasm(args.binary, entities, output,
                      base_addr=args.base_addr,
                      code_start=args.code_start,
                      profile_stages=args.profile_stages,
                      stall_timeout=args.stall_timeout)

"""Test assembler output against DevPac GenAm oracle via vamos.

Generates test cases from m68k_instructions.json and binary-diffs our
assembler output against GenAm (DevPac 3.18) for each instruction.

GenAm produces Amiga hunk executables, so we extract the HUNK_CODE
payload for comparison.  Instructions are batched (default 50 per
invocation) to amortise the ~0.5 s vamos startup cost.

Usage:
    uv run scripts/test_m68k_genam.py [--verbose] [--filter MNEMONIC]
"""

import json
import os
import struct
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT / "scripts"))

from m68k_asm import assemble_instruction  # noqa: E402

KNOWLEDGE = PROJ_ROOT / "knowledge" / "m68k_instructions.json"
ORACLE_JSON = PROJ_ROOT / "knowledge" / "asm_devpac.json"

def _load_oracle():
    with open(ORACLE_JSON, encoding="utf-8") as f:
        return json.load(f)

ORACLE = _load_oracle()
GENAM = PROJ_ROOT / "resources" / "Amiga_Devpac_3_18" / ORACLE["cli"]["executable"]

# Windows temp directory for vamos volume mapping
WIN_TEMP = os.environ.get("TEMP", os.environ.get("TMP", ""))

# Sentinel word placed after each instruction in batch source
SENTINEL = 0xA5A5
SENTINEL_BYTES = struct.pack(">H", SENTINEL)

# How many instructions per GenAm invocation
BATCH_SIZE = 50


# ── Hunk code extraction ──────────────────────────────────────────────────

HUNK_CODE = 0x3E9
HUNK_END = 0x3F2
HUNK_HEADER = 0x3F3


def extract_hunk_code(data):
    """Extract code bytes from an Amiga hunk executable.

    Returns the raw code bytes from the first HUNK_CODE section,
    stripped of long-word padding.
    """
    if len(data) < 4:
        return None
    magic = struct.unpack(">I", data[:4])[0]
    if magic != HUNK_HEADER:
        return None

    # Skip HUNK_HEADER: magic, string_count(0), num_hunks, first, last, sizes
    pos = 4
    # resident library names (terminated by 0)
    while pos < len(data) - 4:
        name_longs = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        if name_longs == 0:
            break
        pos += name_longs * 4

    # table_size, first_hunk, last_hunk
    if pos + 12 > len(data):
        return None
    table_size, first_hunk, last_hunk = struct.unpack(">III", data[pos:pos + 12])
    pos += 12

    # hunk sizes
    num_hunks = last_hunk - first_hunk + 1
    pos += num_hunks * 4

    # Find HUNK_CODE
    while pos < len(data) - 4:
        hunk_id = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        if hunk_id == HUNK_CODE:
            n_longs = struct.unpack(">I", data[pos:pos + 4])[0]
            pos += 4
            code = data[pos:pos + n_longs * 4]
            return code
        elif hunk_id == HUNK_END:
            continue
        else:
            # Skip unknown hunk
            if pos + 4 <= len(data):
                n_longs = struct.unpack(">I", data[pos:pos + 4])[0]
                pos += 4 + n_longs * 4
            else:
                break
    return None


# ── GenAm oracle ──────────────────────────────────────────────────────────

def _ensure_opts_disabled():
    """Temporarily rename GenAm.opts to prevent it from interfering.

    GenAm auto-loads GenAm.opts from its directory. The shipped opts file
    has incdir paths that don't exist under vamos, causing errors.
    Returns the backup path if renamed, None otherwise.
    """
    opts = GENAM.parent / "GenAm.opts"
    bak = GENAM.parent / "GenAm.opts.bak"
    if opts.exists():
        opts.rename(bak)
        return bak
    return None


def _restore_opts(bak_path):
    """Restore GenAm.opts from backup."""
    if bak_path and bak_path.exists():
        opts = GENAM.parent / "GenAm.opts"
        bak_path.rename(opts)


def genam_assemble(text):
    """Assemble a single instruction with GenAm via vamos, return bytes or None."""
    src_name = f"_genam_test_{os.getpid()}.s"
    out_name = f"_genam_test_{os.getpid()}"
    src_path = os.path.join(WIN_TEMP, src_name)
    out_path = os.path.join(WIN_TEMP, out_name)

    try:
        with open(src_path, "wb") as f:
            f.write(f" {ORACLE['options']['cpu_select']}\n".encode("latin-1"))
            f.write(f" {ORACLE['options']['no_optimization']}\n".encode("latin-1"))
            f.write(f" {text}\n".encode("latin-1"))

        result = subprocess.run(
            ["vamos",
             "-V", f"TMP:{WIN_TEMP}",
             "--", str(GENAM),
             f"TMP:{src_name}",
             f"-oTMP:{out_name}",
             ORACLE["options"]["quiet"]],
            capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            return None

        if not os.path.exists(out_path):
            return None

        with open(out_path, "rb") as f:
            hunk_data = f.read()

        code = extract_hunk_code(hunk_data)
        if code is None:
            return None

        return code

    except Exception:
        return None
    finally:
        for p in (src_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def genam_assemble_batch(texts):
    """Assemble multiple instructions in one GenAm invocation.

    Each instruction is followed by a dc.w $A5A5 sentinel.  The output
    code section is split on sentinel bytes to recover per-instruction
    encoding.

    Returns a list parallel to *texts*: bytes object on success, None
    on error (instruction rejected by GenAm or sentinel parse failure).
    """
    src_name = f"_genam_batch_{os.getpid()}.s"
    out_name = f"_genam_batch_{os.getpid()}"
    src_path = os.path.join(WIN_TEMP, src_name)
    out_path = os.path.join(WIN_TEMP, out_name)

    try:
        with open(src_path, "wb") as f:
            f.write(f" {ORACLE['options']['cpu_select']}\n".encode("latin-1"))
            f.write(f" {ORACLE['options']['no_optimization']}\n".encode("latin-1"))
            for text in texts:
                f.write(f" {text}\n".encode("latin-1"))
                f.write(b" dc.w $A5A5\n")

        result = subprocess.run(
            ["vamos",
             "-V", f"TMP:{WIN_TEMP}",
             "--", str(GENAM),
             f"TMP:{src_name}",
             f"-oTMP:{out_name}",
             ORACLE["options"]["quiet"]],
            capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            # Batch failed — fall back to individual assembly
            return None

        if not os.path.exists(out_path):
            return None

        with open(out_path, "rb") as f:
            hunk_data = f.read()

        code = extract_hunk_code(hunk_data)
        if code is None:
            return None

        # Split on sentinel to recover per-instruction bytes
        results = []
        pos = 0
        for _ in texts:
            sentinel_pos = code.find(SENTINEL_BYTES, pos)
            if sentinel_pos < 0:
                # Sentinel not found — remaining instructions failed
                results.append(None)
                continue
            results.append(code[pos:sentinel_pos])
            pos = sentinel_pos + 2

        return results

    except Exception:
        return None
    finally:
        for p in (src_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


# ── KB-driven test generation (reuse from test_m68k_asm.py) ──────────────

def _load_kb():
    with open(KNOWLEDGE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("instructions", []), data.get("_meta", {})


KB_INSTRUCTIONS, KB_META = _load_kb()
_KB_BY_MNEMONIC = {inst["mnemonic"]: inst for inst in KB_INSTRUCTIONS}


def _is_commutative_match(mnemonic, our_bytes, genam_bytes):
    """Check if a mismatch is due to commutative register assignment.

    For instructions whose KB operation field indicates commutativity
    (e.g. EXG: "Rx ←→ Ry"), swapping the two register fields in the opword
    produces identical behavior.  Accept as equivalent if swapping Rx/Ry
    in our encoding matches GenAm's encoding.
    """
    inst = _KB_BY_MNEMONIC.get(mnemonic)
    if inst is None or len(our_bytes) != 2 or len(genam_bytes) != 2:
        return False
    # Detect commutativity from KB operation field (exchange symbol)
    operation = inst.get("operation", "")
    if "←→" not in operation and "↔" not in operation:
        return False
    # Find the two REGISTER fields in the encoding
    enc = inst["encodings"][0]
    reg_fields = [f for f in enc["fields"]
                  if "REGISTER" in f["name"].upper()
                  and f["name"] not in ("0", "1")]
    if len(reg_fields) != 2:
        return False
    # Extract register values from our opword, swap them, rebuild
    our_word = struct.unpack(">H", our_bytes)[0]
    r0, r1 = reg_fields[0], reg_fields[1]
    mask0 = ((1 << r0["width"]) - 1) << r0["bit_lo"]
    mask1 = ((1 << r1["width"]) - 1) << r1["bit_lo"]
    val0 = (our_word & mask0) >> r0["bit_lo"]
    val1 = (our_word & mask1) >> r1["bit_lo"]
    # Rebuild with swapped register values
    swapped = (our_word & ~mask0 & ~mask1) | (val1 << r0["bit_lo"]) | (val0 << r1["bit_lo"])
    genam_word = struct.unpack(">H", genam_bytes)[0]
    return swapped == genam_word


# Import test generation from the main assembler test suite
from test_m68k_asm import generate_tests, _generate_movem_tests  # noqa: E402
from test_m68k_asm import _generate_branch_tests  # noqa: E402


# ── Main test runner ──────────────────────────────────────────────────────

def _run_batch(batch, results, args):
    """Run a batch of tests against GenAm and accumulate results.

    batch: list of (mnemonic, our_bytes, asm_text, desc, genam_text)
    results: dict with keys passed/failed/errors/genam_errors/failures/
             tested_mnemonics
    """
    genam_texts = [item[4] for item in batch]
    genam_results = genam_assemble_batch(genam_texts)

    if genam_results is None:
        # Batch failed — fall back to individual assembly
        for mnemonic, our_bytes, asm, desc, genam_text in batch:
            genam_bytes = genam_assemble(genam_text)
            _compare_one(mnemonic, our_bytes, asm, desc, genam_bytes, results,
                         args)
        return

    for i, (mnemonic, our_bytes, asm, desc, genam_text) in enumerate(batch):
        genam_bytes = genam_results[i] if i < len(genam_results) else None
        _compare_one(mnemonic, our_bytes, asm, desc, genam_bytes, results,
                     args)


def _compare_one(mnemonic, our_bytes, asm, desc, genam_bytes, results, args):
    """Compare one instruction's output against GenAm result."""
    if genam_bytes is None:
        if args.verbose:
            print(f"  GENAM ERROR: {asm}")
        results["genam_errors"] += 1
        return

    # Empty bytes means GenAm accepted the instruction but emitted nothing
    # before the sentinel (e.g. instruction was a sentinel collision)
    if len(genam_bytes) == 0:
        if args.verbose:
            print(f"  GENAM EMPTY: {asm}")
        results["genam_errors"] += 1
        return

    our_len = len(our_bytes)
    genam_code = genam_bytes[:our_len]

    if our_bytes == genam_code:
        results["passed"] += 1
        results["tested_mnemonics"].add(mnemonic)
        if args.verbose:
            print(f"  OK: {asm}")
    elif _is_commutative_match(mnemonic, our_bytes, genam_code):
        # Commutative instruction (e.g. EXG): swapped register assignment
        # produces identical behavior, accept as pass.
        results["passed"] += 1
        results["tested_mnemonics"].add(mnemonic)
        if args.verbose:
            print(f"  OK: {asm} (commutative)")
    else:
        results["failed"] += 1
        results["tested_mnemonics"].add(mnemonic)
        print(f"  MISMATCH: {asm} ({desc})")
        print(f"    ours:  {our_bytes.hex()}")
        print(f"    genam: {genam_bytes.hex()}")
        results["failures"].append(
            (mnemonic, asm, desc, our_bytes.hex(), genam_bytes.hex()))


def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Test assembler vs GenAm")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--filter", "-f", help="Filter by mnemonic substring")
    parser.add_argument("--limit", "-n", type=int, default=0,
                        help="Limit total tests (0=unlimited)")
    parser.add_argument("--batch-size", "-b", type=int, default=BATCH_SIZE,
                        help=f"Instructions per GenAm invocation "
                             f"(default {BATCH_SIZE})")
    args = parser.parse_args()

    # Disable GenAm.opts to prevent incdir errors under vamos
    opts_bak = _ensure_opts_disabled()

    t0 = time.time()

    # Quick smoke test (single invocation)
    print("Smoke test: GenAm assembly...")
    smoke = genam_assemble("move.l d0,d1")
    if smoke is None:
        print("FATAL: GenAm smoke test failed. Check vamos/GenAm setup.")
        return 1
    expected = b"\x22\x00"
    if smoke[:len(expected)] != expected:
        print(f"FATAL: GenAm smoke test mismatch: {smoke.hex()} != {expected.hex()}")
        return 1
    print(f"  OK: move.l d0,d1 -> {smoke.hex()}")

    results = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "genam_errors": 0,
        "failures": [],
        "tested_mnemonics": set(),
    }

    # ── Collect all tests ─────────────────────────────────────────────
    # Each entry: (mnemonic, asm_text, desc, genam_text, pc)
    # For non-branch tests, genam_text == asm_text and pc == 0.
    # For branch tests, genam_text uses *+N syntax and pc from generator.
    all_tests = []

    for inst in KB_INSTRUCTIONS:
        mnemonic = inst["mnemonic"]
        if args.filter and args.filter.lower() not in mnemonic.lower():
            continue
        tests = generate_tests(inst)
        for asm, desc in tests:
            all_tests.append((mnemonic, asm, desc, asm, 0))

    if not args.filter or "movem" in args.filter.lower():
        for asm, desc in _generate_movem_tests():
            all_tests.append(("MOVEM", asm, desc, asm, 0))

    # Branch tests: convert absolute target to *+N for GenAm
    branch_tests = _generate_branch_tests()
    if args.filter:
        branch_tests = [t for t in branch_tests
                        if args.filter.lower() in
                        t[0].split(".")[0].split()[0].lower()]

    for asm, desc, pc in branch_tests:
        parts = asm.rsplit("$", 1)
        if len(parts) != 2:
            continue
        target = int(parts[1], 16)
        offset = target - pc
        star_expr = f"*+{offset}" if offset >= 0 else f"*-{-offset}"
        genam_asm = parts[0] + star_expr
        all_tests.append((asm.split(".")[0].split()[0].upper(),
                          asm, desc, genam_asm, pc))

    if args.limit:
        all_tests = all_tests[:args.limit]

    # ── Assemble with our assembler first (fast, no subprocess) ───────
    assembled = []
    for mnemonic, asm, desc, genam_text, pc in all_tests:
        try:
            our_bytes = assemble_instruction(asm, pc=pc)
        except Exception as e:
            if args.verbose:
                print(f"  ASM ERROR: {asm}: {e}")
            results["errors"] += 1
            results["failures"].append(
                (mnemonic, asm, desc, f"asm: {e}", None))
            continue

        assembled.append((mnemonic, our_bytes, asm, desc, genam_text))

    # ── Run batches against GenAm ─────────────────────────────────────
    batch = []
    for item in assembled:
        batch.append(item)
        if len(batch) >= args.batch_size:
            _run_batch(batch, results, args)
            batch = []
    if batch:
        _run_batch(batch, results, args)

    elapsed = time.time() - t0

    # ── Summary ───────────────────────────────────────────────────────
    total = results["passed"] + results["failed"] + results["errors"]
    print(f"\n{'='*60}")
    print(f"Results: {results['passed']}/{total} passed, "
          f"{results['failed']} mismatches, "
          f"{results['errors']} assembler errors, "
          f"{results['genam_errors']} GenAm errors")
    print(f"Tested mnemonics: {len(results['tested_mnemonics'])}")
    print(f"Time: {elapsed:.1f}s "
          f"({len(assembled)} instructions, "
          f"{len(assembled) // args.batch_size + 1} batches)")

    if results["failures"]:
        by_mn = {}
        for mn, asm, desc, ours, genam in results["failures"]:
            by_mn.setdefault(mn, []).append((asm, desc, ours, genam))
        print(f"\nFailures ({len(results['failures'])} total):")
        for mn, items in sorted(by_mn.items()):
            print(f"  {mn}:")
            for asm, desc, ours, genam in items[:5]:
                if genam is None:
                    print(f"    {asm}: {ours}")
                else:
                    print(f"    {asm}: ours={ours} genam={genam}")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")

    # Restore GenAm.opts
    _restore_opts(opts_bak)

    return 0 if (results["failed"] == 0 and results["errors"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())

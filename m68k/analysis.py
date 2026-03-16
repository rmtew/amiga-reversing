"""Shared binary analysis pipeline for M68K Amiga executables.

Runs the complete analysis: hunk parse -> init discovery -> core analysis
with jump table/indirect resolution -> store passes -> hint scan -> OS calls.

Both build_entities and gen_disasm call analyze_hunk() and use the result.
Supports caching via save/load for instant reuse.
"""

import pickle
import struct
from dataclasses import dataclass, field
from pathlib import Path

from .hunk_parser import parse_file, HunkType, _HUNK_KB
from .m68k_executor import analyze, BasicBlock, _extract_mnemonic
from .jump_tables import (detect_jump_tables, resolve_indirect_targets,
                          resolve_per_caller, resolve_backward_slice)
from .os_calls import (load_os_kb, get_platform_config,
                       identify_library_calls, _SENTINEL_ALLOC_BASE)
from .subroutine_scan import scan_and_score
from .kb_util import KB


# ── Relocation helpers ───────────────────────────────────────────────────

_RELOC_INFO = {}
for _name, _sem in _HUNK_KB.get("relocation_semantics", {}).items():
    if _name in HunkType.__members__:
        _RELOC_INFO[HunkType[_name]] = {
            "bytes": _sem["bytes"],
            "mode": _sem["mode"],
        }

_RELOC_ABS_FMT = {4: ">I", 2: ">H"}
_RELOC_REL_FMT = {4: ">i", 2: ">h", 1: ">b"}


def resolve_reloc_target(reloc, offset: int, data: bytes) -> int | None:
    """Resolve a relocation offset to its target address."""
    info = _RELOC_INFO.get(reloc.reloc_type)
    if info is None:
        return None
    nbytes = info["bytes"]
    mode = info["mode"]
    if offset + nbytes > len(data):
        return None
    if mode == "absolute":
        fmt = _RELOC_ABS_FMT.get(nbytes)
        if fmt is None:
            return None
        return struct.unpack_from(fmt, data, offset)[0]
    if mode == "pc_relative":
        fmt = _RELOC_REL_FMT.get(nbytes)
        if fmt is None:
            return None
        disp = struct.unpack_from(fmt, data, offset)[0]
        return offset + disp
    return None


# ── Analysis result ──────────────────────────────────────────────────────

_CACHE_VERSION = 1  # bump when HunkAnalysis fields change

# Platform dict keys that are not serializable (lambdas, resolvers)
_PLATFORM_TRANSIENT_KEYS = {
    "_os_call_resolver", "_pending_call_effect", "_summary_cache",
}


@dataclass
class HunkAnalysis:
    """Complete analysis result for one code hunk."""
    code: bytes
    hunk_index: int
    blocks: dict                  # addr -> BasicBlock (core)
    exit_states: dict             # addr -> (cpu, mem)
    xrefs: list                   # XRef list
    call_targets: set             # subroutine entry addresses
    branch_targets: set           # branch target addresses
    jump_tables: list             # detect_jump_tables results
    hint_blocks: dict             # addr -> BasicBlock (hints)
    hint_reasons: dict            # entry -> {source, referenced_from}
    lib_calls: list               # identify_library_calls results
    platform: dict                # platform config (base reg, init mem, etc.)
    reloc_targets: set            # reloc-derived target addresses
    reloc_refs: dict              # target -> [referencing offsets]
    os_kb: dict                   # OS knowledge base (not cached)

    def save(self, path: str | Path):
        """Serialize analysis to disk (excluding os_kb and transient state)."""
        # Strip non-serializable items
        saved_os_kb = self.os_kb
        saved_platform = self.platform
        self.os_kb = None
        clean_platform = {k: v for k, v in saved_platform.items()
                          if k not in _PLATFORM_TRANSIENT_KEYS
                          and not callable(v)}
        self.platform = clean_platform
        try:
            with open(path, "wb") as f:
                pickle.dump((_CACHE_VERSION, self), f,
                            protocol=pickle.HIGHEST_PROTOCOL)
        finally:
            self.os_kb = saved_os_kb
            self.platform = saved_platform

    @staticmethod
    def load(path: str | Path, os_kb: dict) -> "HunkAnalysis":
        """Load cached analysis, re-attaching the OS KB."""
        with open(path, "rb") as f:
            version, ha = pickle.load(f)
        if version != _CACHE_VERSION:
            raise ValueError(
                f"Cache version mismatch: file={version}, "
                f"expected={_CACHE_VERSION}")
        ha.os_kb = os_kb
        return ha


# ── Relocated segment detection ───────────────────────────────────────

def detect_relocated_segments(code: bytes) -> list[dict]:
    """Detect copy-and-jump patterns that relocate code to fixed addresses.

    Common in Amiga game executables: bootstrap code copies the payload
    to an absolute address and jumps to it.  Pattern:
        LEA source,An
        LEA dest,Am
        copy loop: move.b/w/l (An)+,(Am)+
        JMP dest

    Returns list of segments:
        [{"file_offset": int, "base_addr": int, "size": int,
          "entry_points": [int]}]
    Entry points include secondary code (e.g. copy stubs reached via TRAP).
    """
    kb = KB()

    code_size = len(code)

    # Run entry-0 propagation to get concrete register values.
    # Also follow copied code: if the bootstrap copies code within
    # the hunk and jumps to it (via TRAP or JMP), analyze the copy
    # source as a secondary entry point.
    result = analyze(code, base_addr=0, entry_points=[0], propagate=True)
    blocks = result["blocks"]
    exit_states = result.get("exit_states", {})

    # Detect first-stage copies (small stubs copied to low memory).
    # The stub source bytes are still in the hunk at their original
    # offset.  Analyze them as secondary entry points, then look for
    # copy-and-jump patterns in the combined block set.
    import re
    secondary_entries = set()
    for addr in sorted(blocks):
        blk = blocks[addr]
        for inst in blk.instructions:
            m = re.match(
                r'move\.[bwl]\s+\(a(\d)\)\+\s*,\s*\(a(\d)\)\+',
                inst.text.lower())
            if m:
                src_reg = int(m.group(1))
                for pred_addr in sorted(blocks):
                    if pred_addr >= addr:
                        break
                    if pred_addr in exit_states:
                        cpu, _ = exit_states[pred_addr]
                        src_val = cpu.a[src_reg]
                        if (src_val.is_known
                                and 0 < src_val.concrete < code_size):
                            secondary_entries.add(src_val.concrete)
                break

    if secondary_entries:
        # Collect all register values from the bootstrap's exit states
        # to carry into the secondary analysis.  This preserves values
        # like A6 (payload source) set before TRAP.
        bootstrap_regs = {}
        for addr in sorted(exit_states, reverse=True):
            cpu, _ = exit_states[addr]
            for i in range(len(cpu.a)):
                if cpu.a[i].is_known and i not in bootstrap_regs:
                    bootstrap_regs[i] = cpu.a[i].concrete
            break  # use last block's state

        result2 = analyze(code, base_addr=0,
                          entry_points=sorted(secondary_entries),
                          propagate=True)
        # Merge bootstrap register knowledge into secondary exit states
        for addr in result2.get("exit_states", {}):
            cpu, mem = result2["exit_states"][addr]
            for i, val in bootstrap_regs.items():
                if not cpu.a[i].is_known:
                    from .m68k_executor import _concrete
                    cpu.set_reg("an", i, _concrete(val))
        blocks.update(result2["blocks"])
        exit_states.update(result2.get("exit_states", {}))

    segments = []
    all_entries = {0} | secondary_entries

    # Find blocks ending with JMP to an absolute address
    for addr in sorted(blocks):
        blk = blocks[addr]
        if not blk.instructions:
            continue
        last = blk.instructions[-1]
        ft, _ = kb.flow_type(last)
        if ft != "jump":
            continue

        # Extract JMP target from xrefs
        jmp_target = None
        for xref in blk.xrefs:
            if xref.type == "jump":
                jmp_target = xref.dst
                break
        if jmp_target is None:
            continue

        # Check: is there a copy loop in the blocks before this JMP?
        # Walk predecessor chain looking for postincrement move pattern
        _find_copy_segment(
            jmp_target, blocks, exit_states, code_size, kb, segments,
            all_entries)

    return segments


def _find_copy_segment(jmp_target: int, blocks: dict, exit_states: dict,
                       code_size: int, kb: KB,
                       segments: list[dict],
                       all_entries: set[int] = None):
    """Check if blocks before a JMP contain a copy loop targeting jmp_target.

    Looks for postincrement move patterns (move.b/w/l (An)+,(Am)+)
    where Am's initial value equals jmp_target (the copy destination).
    The source register's initial value gives the file offset.
    If the source register is unknown (set in a prior stage), checks
    all registers in the setup block for a file-offset-like value.
    """
    import re

    for addr in sorted(blocks):
        blk = blocks[addr]
        for inst in blk.instructions:
            text = inst.text.lower()
            m = re.match(
                r'move\.[bwl]\s+\(a(\d)\)\+\s*,\s*\(a(\d)\)\+', text)
            if not m:
                continue

            src_reg = int(m.group(1))
            dst_reg = int(m.group(2))

            # Find the setup block before the copy loop
            for pred_addr in sorted(blocks):
                if pred_addr >= addr:
                    break
                if pred_addr not in exit_states:
                    continue
                cpu, _ = exit_states[pred_addr]
                dst_val = cpu.a[dst_reg]

                if not (dst_val.is_known
                        and dst_val.concrete == jmp_target):
                    continue

                # Destination matches JMP target.
                # Find source: check the source register first,
                # then try all address registers for file offsets.
                src_val = cpu.a[src_reg]
                file_offset = None
                if (src_val.is_known
                        and 0 < src_val.concrete < code_size):
                    file_offset = src_val.concrete
                else:
                    # Source register unknown (set in prior stage).
                    # Look for any register with a plausible file offset
                    # that's between the bootstrap and the JMP target.
                    for i in range(len(cpu.a)):
                        v = cpu.a[i]
                        if (v.is_known and 0 < v.concrete < code_size
                                and v.concrete > addr
                                and i != dst_reg):
                            file_offset = v.concrete
                            break

                if file_offset is not None:
                    seg = {
                        "file_offset": file_offset,
                        "base_addr": jmp_target,
                        "entry_points": sorted(all_entries or {0}),
                    }
                    for i in range(len(cpu.d)):
                        d_val = cpu.d[i]
                        if d_val.is_known and d_val.concrete > 0:
                            seg["size"] = d_val.concrete
                            break
                    if seg not in segments:
                        segments.append(seg)
                    return


# ── Pipeline ─────────────────────────────────────────────────────────────

def analyze_hunk(code: bytes, relocs: list, hunk_index: int = 0,
                 print_fn=print,
                 base_addr: int = 0,
                 code_start: int = 0) -> HunkAnalysis:
    """Run the complete analysis pipeline on a code hunk.

    Args:
        code: raw hunk data bytes
        relocs: relocation entries
        base_addr: runtime base address of the code section (default 0)
        code_start: byte offset within code where the real code begins
            (skips bootstrap prefix like copy loops)

    Phases:
        0. Init discovery (entry point only) -- base register, init memory
        1. Core analysis with resolution loop -- jump tables, indirect,
           per-caller, backward slice, store passes
        2. Hint discovery -- reloc targets + heuristic scan
        3. OS call identification

    Returns HunkAnalysis with all results.
    """
    # Auto-detect relocated code: if the bootstrap copies code to a
    # higher address and jumps to it, build a flat runtime memory image
    # with the copy applied, then analyze from entry 0.  This handles
    # the common Amiga game pattern of: bootstrap -> copy payload ->
    # JMP to payload.  The flat image lets block discovery decode the
    # correct (copied) bytes at the target address.
    extra_entries = set()
    if base_addr == 0 and code_start == 0:
        segments = detect_relocated_segments(code)
        if segments:
            seg = segments[0]
            src = seg["file_offset"]
            dst = seg["base_addr"]
            payload_size = len(code) - src
            flat_size = dst + payload_size
            flat = bytearray(flat_size)
            flat[0:len(code)] = code  # bootstrap at original offsets
            flat[dst:dst + payload_size] = code[src:]  # payload at runtime addr
            code = bytes(flat)
            # Collect all entry points (bootstrap + copy stubs)
            extra_entries = set(seg.get("entry_points", []))
            print_fn(f"  Relocated: file ${src:X} -> addr ${dst:X} "
                     f"({payload_size} bytes, flat image {flat_size})")

    if code_start > 0:
        code = code[code_start:]
    code_size = len(code)
    kb = KB()

    # Collect reloc targets
    reloc_targets = set()
    reloc_refs: dict[int, list[int]] = {}
    for reloc in relocs:
        for offset in reloc.offsets:
            target = resolve_reloc_target(reloc, offset, code)
            if target is not None and 0 <= target < code_size:
                reloc_targets.add(target)
                reloc_refs.setdefault(target, []).append(offset)

    platform = get_platform_config()

    # ── Phase 0: Init discovery ──────────────────────────────────────
    base_reg_num = platform["_base_reg_num"]
    init_result = analyze(code, base_addr=base_addr,
                          entry_points=[base_addr],
                          propagate=True, platform=platform)
    alloc_base = _SENTINEL_ALLOC_BASE
    alloc_limit = platform["_next_alloc_sentinel"]
    discovered_base = None
    best_addr = None
    best_slots = 0
    for addr, (cpu, mem) in init_result.get("exit_states", {}).items():
        val = cpu.a[base_reg_num]
        if val.is_known and alloc_base <= val.concrete < alloc_limit:
            if discovered_base is None:
                discovered_base = val.concrete
            slots = sum(1 for a in mem._bytes
                        if alloc_base <= a < alloc_limit)
            if slots > best_slots:
                best_slots = slots
                best_addr = addr
    if discovered_base is not None:
        print_fn(f"  Base register A{base_reg_num} "
                 f"= ${discovered_base:08X} (from init"
                 f", {best_slots} memory bytes)")
        platform["initial_base_reg"] = (base_reg_num, discovered_base)
        if best_addr is not None:
            _, init_mem = init_result["exit_states"][best_addr]
            platform["_initial_mem"] = init_mem

    # ── Phase 1: Core analysis with resolution loop ──────────────────
    core_entries = {base_addr} | extra_entries
    jt_call_targets = set()
    jt_list = []  # final jump table list (for gen_disasm)

    def _resolve_and_expand():
        """Run all resolution passes, return number of new entries."""
        nonlocal jt_list
        added = 0
        jt_list = detect_jump_tables(result["blocks"], code,
                                        base_addr=base_addr)
        for t in jt_list:
            for tgt in t["targets"]:
                if tgt not in core_entries:
                    core_entries.add(tgt)
                    added += 1
            dblk = result["blocks"].get(t["dispatch_block"])
            if dblk and dblk.instructions:
                ft, _ = kb.flow_type(dblk.instructions[-1])
                if ft == "call":
                    jt_call_targets.update(t["targets"])
        for r in resolve_indirect_targets(
                result["blocks"],
                result.get("exit_states", {}),
                code_size):
            if r["target"] not in core_entries:
                core_entries.add(r["target"])
                added += 1
        for r in resolve_per_caller(
                result["blocks"],
                result.get("exit_states", {}),
                code, code_size,
                platform=platform):
            if r["target"] not in core_entries:
                core_entries.add(r["target"])
                added += 1
        for r in resolve_backward_slice(
                result["blocks"],
                result.get("exit_states", {}),
                code, code_size,
                platform=platform):
            if r["target"] not in core_entries:
                core_entries.add(r["target"])
                added += 1
        return added

    entries_converged = False
    result = None
    for store_pass in range(5):
        for _ in range(10):
            result = analyze(code, base_addr=base_addr,
                             entry_points=sorted(core_entries),
                             propagate=True, platform=platform)
            if entries_converged:
                break  # just re-analyzed with new memory
            if not _resolve_and_expand():
                entries_converged = True
                break

        # Store pass: scan exit states for concrete stores to app memory
        if not platform.get("initial_base_reg"):
            break
        breg_num, breg_val = platform["initial_base_reg"]
        init_mem = platform.get("_initial_mem")
        if init_mem is None:
            break

        new_stores = 0
        for addr, (cpu, mem) in result.get("exit_states", {}).items():
            for mem_addr, val in mem._bytes.items():
                if not (alloc_base <= mem_addr < alloc_limit):
                    continue
                if mem_addr in init_mem._bytes:
                    continue
                if val.concrete is None:
                    continue
                init_mem._bytes[mem_addr] = val
                new_stores += 1
            for key, tag in mem._tags.items():
                if key not in init_mem._tags:
                    init_mem._tags[key] = tag

        if new_stores == 0:
            break
        disp_example = ""
        for mem_addr in sorted(init_mem._bytes):
            if (alloc_base <= mem_addr < alloc_limit
                    and init_mem._bytes[mem_addr].concrete is not None
                    and 0 <= init_mem._bytes[mem_addr].concrete < code_size):
                disp_example = f" (e.g. d({mem_addr - breg_val}))"
                break
        print_fn(f"  Store pass {store_pass + 1}: "
                 f"{new_stores} new memory values{disp_example}")

    blocks = result["blocks"]
    xrefs = result["xrefs"]
    call_targets = result["call_targets"] | jt_call_targets
    exit_states = result.get("exit_states", {})

    def _stats(blks):
        covered = sum(b.end - b.start for b in blks.values())
        n = sum(len(b.instructions) for b in blks.values())
        return (f"{len(blks)} blocks, {n} instructions, "
                f"{covered}/{code_size} ({100*covered/code_size:.1f}%)")

    print_fn(f"  Core: {_stats(blocks)}")

    # ── Phase 2: Hint discovery ──────────────────────────────────────
    core_addrs = set()
    for blk in blocks.values():
        for a in range(blk.start, blk.end):
            core_addrs.add(a)

    hint_entries = reloc_targets - set(blocks.keys())
    hint_blocks: dict[int, BasicBlock] = {}
    hint_source: dict[int, str] = {}
    if hint_entries:
        hint_result = analyze(code, base_addr=base_addr,
                              entry_points=sorted(hint_entries),
                              propagate=False)
        for a, b in hint_result["blocks"].items():
            if a not in blocks:
                hint_blocks[a] = b
        for e in hint_entries:
            hint_source[e] = "reloc"

    # Pass combined core + hint blocks so the scanner's gap computation
    # respects already-discovered hint regions.  Without this, a large
    # gap containing a hint block gets scanned from the gap start and
    # a bigger candidate can consume code that should be a separate sub.
    scan_blocks = dict(blocks)
    scan_blocks.update(hint_blocks)
    scan_candidates = scan_and_score(scan_blocks, code, reloc_targets,
                                     call_targets)
    scan_entries = {c["addr"] for c in scan_candidates
                    if c["addr"] not in blocks
                    and c["addr"] not in hint_blocks}
    if scan_entries:
        scan_result = analyze(code, base_addr=base_addr,
                              entry_points=sorted(scan_entries),
                              propagate=False)
        for a, b in scan_result["blocks"].items():
            if a not in blocks and a not in hint_blocks:
                hint_blocks[a] = b
        for e in scan_entries:
            hint_source[e] = "scan"

    # Post-scan: seed at addresses immediately after each hint block
    # that ends with a flow-terminating instruction (RTS, BRA, JMP).
    # These are adjacent code regions that the main scanner missed
    # because they were consumed by larger candidates or not reachable
    # from any branch target.
    post_scan_entries = set()
    all_known = set(blocks) | set(hint_blocks)
    for hb in hint_blocks.values():
        if not hb.instructions:
            continue
        last = hb.instructions[-1]
        ft, conditional = kb.flow_type(last)
        if ft in ("return", "jump") or (ft == "branch"
                                         and not conditional):
            next_addr = hb.end
            if (next_addr < code_size
                    and next_addr not in all_known
                    and next_addr not in post_scan_entries):
                post_scan_entries.add(next_addr)
    if post_scan_entries:
        post_result = analyze(code, base_addr=base_addr,
                              entry_points=sorted(post_scan_entries),
                              propagate=False)
        added = 0
        for a, b in post_result["blocks"].items():
            if a not in blocks and a not in hint_blocks:
                hint_blocks[a] = b
                added += 1
        for e in post_scan_entries:
            if e in hint_blocks:
                hint_source[e] = "scan"
                scan_entries.add(e)

    hint_reasons: dict[int, dict] = {}
    for entry in sorted(set(hint_entries) | scan_entries):
        reason = {"source": hint_source.get(entry, "scan")}
        if entry in reloc_refs:
            refs = reloc_refs[entry]
            core_refs = [r for r in refs if r in core_addrs]
            if core_refs:
                reason["source"] = "reloc_from_core"
                reason["referenced_from"] = core_refs
            else:
                reason["source"] = "reloc_from_hint"
                reason["referenced_from"] = refs
        hint_reasons[entry] = reason

    if hint_blocks:
        from collections import Counter
        by_reason = Counter(r["source"] for r in hint_reasons.values())
        reason_str = ", ".join(f"{c} {s}"
                               for s, c in sorted(by_reason.items()))
        print_fn(f"  Hints: {_stats(hint_blocks)} ({reason_str})")

    print_fn(f"  {len(xrefs)} xrefs, "
             f"{len(call_targets)} call targets, "
             f"{len(result['branch_targets'])} branch targets")

    # ── Phase 3: OS call identification ──────────────────────────────
    os_kb = load_os_kb()
    lib_calls = identify_library_calls(
        blocks, code, os_kb, exit_states, call_targets, platform)

    if lib_calls:
        resolved = [c for c in lib_calls if c.get("function")]
        libs = set(c.get("library", "?") for c in resolved)
        print_fn(f"  {len(lib_calls)} library calls identified "
                 f"({len(resolved)} resolved"
                 f", libraries: {', '.join(sorted(libs))})")

    return HunkAnalysis(
        code=code,
        hunk_index=hunk_index,
        blocks=blocks,
        exit_states=exit_states,
        xrefs=xrefs,
        call_targets=call_targets,
        branch_targets=result["branch_targets"],
        jump_tables=jt_list,
        hint_blocks=hint_blocks,
        hint_reasons=hint_reasons,
        lib_calls=lib_calls,
        platform=platform,
        reloc_targets=reloc_targets,
        reloc_refs=reloc_refs,
        os_kb=os_kb,
    )

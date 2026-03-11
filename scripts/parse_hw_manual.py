#!/usr/bin/env py.exe
"""Parse Amiga Hardware Reference Manual HTML files into structured data.

Extracts:
1. Complete register map from address-order summary (node0060.html)
2. Per-register bit field definitions from individual register pages
3. Chapter/topic index for the full manual

Usage:
    python scripts/parse_hw_manual.py resources/Hardware_Manual.html
    python scripts/parse_hw_manual.py resources/Hardware_Manual.html --output json --outfile knowledge/amiga_hw_registers.json
    python scripts/parse_hw_manual.py resources/Hardware_Manual.html --output md --outfile knowledge/amiga_hw_reference.md
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from html import unescape
from pathlib import Path


@dataclass
class BitDef:
    bit: int
    name: str
    description: str


@dataclass
class Register:
    name: str
    address: int          # Chip-relative offset (add $DFF000 for 68K address)
    access: str           # R, W, ER, S
    chip: str             # A, D, P, or combinations
    function: str         # Short description
    ecs: bool = False     # Enhanced Chip Set register
    dma_only: bool = False  # & flag: DMA channel only
    dma_usually: bool = False  # % flag: DMA usually, processor sometimes
    pointer_pair: bool = False  # + flag: address register pair
    copper_protected: bool = False  # * flag: not writable by Copper
    copper_danger: bool = False  # ~ flag: needs COPCON danger bit
    bits: list[BitDef] = field(default_factory=list)
    detail_page: str = ""  # Link to detail page
    notes: str = ""        # Additional notes from detail page


@dataclass
class Chapter:
    number: str
    title: str
    node: str  # HTML filename
    sections: list[tuple[str, str]] = field(default_factory=list)  # (title, node)


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    return text


def extract_body(html: str) -> str:
    """Extract content between BODY=START and BODY=END markers."""
    m = re.search(r'<!-- AG2HTML: BODY=START -->(.*?)<!-- AG2HTML: BODY=END -->',
                  html, re.DOTALL)
    return m.group(1) if m else ""


def parse_address_order_summary(guide_dir: str) -> list[Register]:
    """Parse node0060.html (Register Summary Address Order) for full register map."""
    path = os.path.join(guide_dir, "node0060.html")
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()

    body = extract_body(html)
    registers = []

    # Build a map of register name -> detail page link from the raw HTML
    link_map = {}
    for m in re.finditer(r'<a href="[^"]*/([^/"]+)"[^>]*>(\w+)</a>', body):
        page, name = m.group(1), m.group(2)
        if name not in link_map and name != 'E':
            link_map[name] = page

    # Strip HTML and decode entities, then parse line by line
    text = strip_html(body)

    # Register line pattern on clean text:
    #  NAME   [&%+] [*~]HEX  ACCESS  CHIP  FUNCTION
    # Examples:
    #   BLTDDAT   & *000  ER  A       Blitter destination early read
    #   DMACONR     *002  R   AP      DMA control...
    #   BLTCON0     ~040  W   A       Blitter control register 0
    #   DMACON       096  W   ADP     DMA control write
    #   VPOSR       *004  R   A( E )  Read vert most signif...
    reg_pattern = re.compile(
        r'^\s*'
        r'(\w+)'                        # register name
        r'\s+'
        r'([&%+\s]{0,5}?)'             # flags (may be empty or spaces)
        r'([*~]?)'                      # copper flag
        r'([0-9A-Fa-f]{3})'            # 3-digit hex address
        r'\s+'
        r'(ER|[RWSE]+)'                # access mode
        r'\s+'
        r'(.*)',                         # chip + function (parse separately)
    )

    for line in text.split('\n'):
        m = reg_pattern.match(line)
        if not m:
            continue

        name = m.group(1)
        flags_raw = m.group(2)
        copper_flag = m.group(3)
        addr_hex = m.group(4)
        access = m.group(5)
        rest = m.group(6).strip()

        # Skip header line
        if name == 'NAME' and 'FUNCTION' in rest:
            continue

        # Parse chip and function from rest
        # Chip field: 1-3 letters from {A,D,P} with optional "( E )" marker
        # Examples: "A", "AP", "ADP", "A( E )", "AD( E )", "P( E )"
        # Try ECS pattern first (may have only 1 space after ")")
        chip_match = re.match(
            r'^([ADP]+\s*\(\s*E\s*\))\s+(.*)', rest)
        if not chip_match:
            # Non-ECS: chip letters followed by 2+ spaces
            chip_match = re.match(
                r'^([ADP]{1,3})\s{2,}(.*)', rest)
        if chip_match:
            chip_raw = chip_match.group(1).strip()
            function = chip_match.group(2).strip()
        else:
            chip_raw = ""
            function = rest

        # Clean chip: remove ECS markers, parens, spaces
        ecs = 'E' in chip_raw
        chip = re.sub(r'[()E\s]', '', chip_raw)
        if not chip:
            chip = "?"

        addr = int(addr_hex, 16)
        detail_page = link_map.get(name, "")

        # Remove fragment from detail page (e.g. node003D.html#line22 -> node003D.html)
        if '#' in detail_page:
            detail_page = detail_page.split('#')[0]

        reg = Register(
            name=name,
            address=addr,
            access=access,
            chip=chip,
            function=function,
            ecs=ecs,
            dma_only='&' in flags_raw,
            dma_usually='%' in flags_raw,
            pointer_pair='+' in flags_raw,
            copper_protected=copper_flag == '*',
            copper_danger=copper_flag == '~',
            detail_page=detail_page,
        )
        registers.append(reg)

    return registers


def _parse_bit_table_from_text(text: str) -> list[BitDef]:
    """Parse bit field definitions from plain text.

    Handles multiple formats:
    - Vertical: BIT# FUNCTION DESCRIPTION then "15 SET/CLR ..."
    - Vertical with level: "13 EXTER 6 External interrupt"
    - Range notation: "15-08 SV7-SV0 Start vertical..."
    - Horizontal: "BIT# 15,14,...,0" with field names on next line
    - Minimal: "0 START 1 = start Timer A"
    """
    all_bits = []
    lines = text.split('\n')
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        # === Detect horizontal/inline format ===
        # "BIT# 15,14,13,..." or "BIT#  15,14,13,..."
        horiz_m = re.match(r'BIT#?\s+(\d{1,2}[,\s]+\d)', stripped)
        if horiz_m:
            # Parse the bit numbers from header
            bit_nums = re.findall(r'\d{1,2}', stripped)
            bit_nums = [int(b) for b in bit_nums if 0 <= int(b) <= 15]

            # Skip separator
            i += 1
            if i < len(lines) and re.match(r'\s*-+', lines[i].strip()):
                i += 1

            # Next line(s) have field names aligned to bit columns
            if i < len(lines):
                field_line = lines[i].strip()
                field_parts = field_line.split()
                # First token might be a label (USE, RGB, 0DAT, etc.)
                if field_parts and not re.match(r'^[A-Z]\d$', field_parts[0]):
                    # Check if first part is a row label
                    if len(field_parts) > len(bit_nums):
                        field_parts = field_parts[1:]  # skip label
                    elif len(field_parts) < len(bit_nums):
                        pass  # keep as-is

                # Map field names to bits
                for j, bn in enumerate(bit_nums):
                    if j < len(field_parts):
                        name = field_parts[j].rstrip(',')
                        if name not in ('X', 'x', '--', '-'):
                            all_bits.append(BitDef(bit=bn, name=name, description=""))
            i += 1
            continue

        # === Detect vertical BIT# header ===
        if re.match(r'(?:BIT#?|Bit)\s', stripped, re.IGNORECASE) or re.match(r'BIT#\s*$', stripped):
            # Skip header and separator
            i += 1
            while i < len(lines) and re.match(r'\s*[-\s]+$', lines[i].strip()) and '---' in lines[i]:
                i += 1

            # Parse bit entries
            current_bit = None
            current_name = None
            current_desc_lines = []
            # Track indentation of the first bit line to detect continuations
            bit_indent = None

            def save_current():
                nonlocal current_bit, current_name, current_desc_lines
                if current_bit is not None:
                    desc = ' '.join(current_desc_lines).strip()
                    all_bits.append(BitDef(bit=current_bit, name=current_name, description=desc))
                    current_bit = None

            blank_count = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                # Match single bit: "15 SET/CLR ..."
                bm = re.match(r'^(\s+)(\d{1,2})\s+(\S+)\s*(.*)', line)
                # Match bare bit number (unused bit): "  15" with nothing after
                bare_bm = re.match(r'^(\s+)(\d{1,2})\s*$', line)
                # Also match range: "15-08 SV7-SV0 ..." or "13-0 LENGTH ..."
                rm = re.match(r'^(\s+)(\d{1,2})-(\d{1,2})\s+(\S+)\s*(.*)', line)

                if rm:
                    save_current()
                    indent = len(rm.group(1))
                    if bit_indent is None:
                        bit_indent = indent
                    hi, lo = int(rm.group(2)), int(rm.group(3))
                    current_bit = hi
                    current_name = rm.group(4)
                    rest = rm.group(5).strip()
                    current_desc_lines = [rest] if rest else []
                    # Add entries for the range
                    desc_text = f"Bits {hi}-{lo}: {current_name}"
                    for b in range(hi, lo - 1, -1):
                        all_bits.append(BitDef(bit=b, name=current_name, description=desc_text))
                    current_bit = None  # already saved
                    blank_count = 0
                    i += 1
                    continue

                if bare_bm and not bm:
                    save_current()
                    indent = len(bare_bm.group(1))
                    if bit_indent is None:
                        bit_indent = indent
                    bit_num = int(bare_bm.group(2))
                    all_bits.append(BitDef(bit=bit_num, name="X", description=""))
                    blank_count = 0
                    i += 1
                    continue

                if bm:
                    save_current()
                    indent = len(bm.group(1))
                    if bit_indent is None:
                        bit_indent = indent
                    current_bit = int(bm.group(2))
                    current_name = bm.group(3)
                    rest = bm.group(4).strip()
                    # Skip interrupt level number if present
                    level_m = re.match(r'^(\d)\s+(.*)', rest)
                    if level_m:
                        current_desc_lines = [level_m.group(2)] if level_m.group(2) else []
                    else:
                        current_desc_lines = [rest] if rest else []
                    blank_count = 0
                    i += 1
                    continue

                # Blank line
                if not stripped:
                    blank_count += 1
                    if blank_count >= 2:
                        save_current()
                        break
                    i += 1
                    continue

                # Continuation of description (more indented than bit number)
                if current_bit is not None:
                    line_indent = len(line) - len(line.lstrip())
                    if bit_indent is not None and line_indent > bit_indent + 2:
                        current_desc_lines.append(stripped)
                        blank_count = 0
                        i += 1
                        continue

                # Something else — end of bit table
                save_current()
                break

            save_current()
            continue

        # === Detect standalone bit entries without BIT# header ===
        # Some pages (CIA control regs, chapter descriptions) start directly
        # with bit entries after a separator line
        if re.match(r'\s*-+\s+-+\s+-+', stripped):
            i += 1
            # Check if next line is a bit entry
            if i < len(lines) and re.match(r'\s+\d{1,2}\s+\S+', lines[i]):
                # Reparse from here with a virtual BIT# header
                continue
            continue

        i += 1

    return all_bits


def parse_register_detail(guide_dir: str, page: str) -> tuple[list[BitDef], str]:
    """Parse a register detail page for bit field definitions."""
    path = os.path.join(guide_dir, page)
    if not os.path.exists(path):
        return [], ""

    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()

    body = extract_body(html)
    text = strip_html(body)

    bits = _parse_bit_table_from_text(text)
    return bits, ""


def parse_chapters(index_html: str) -> list[Chapter]:
    """Parse the main index for chapter structure."""
    with open(index_html, encoding="utf-8", errors="replace") as f:
        html = f.read()

    body = extract_body(html)
    chapters = []

    # Find chapter/appendix links
    ch_pattern = re.compile(
        r'(\d+|[A-K])\s+'
        r'<a href="[^"]*?/([^"]+)"[^>]*>'
        r'([^<]+)</a>'
    )
    for m in ch_pattern.finditer(body):
        num = m.group(1)
        node = m.group(2)
        title = strip_html(m.group(3)).strip()
        chapters.append(Chapter(number=num, title=title, node=node))

    return chapters


def parse_full_manual(index_html: str) -> tuple[list[Register], list[Chapter]]:
    """Parse the complete hardware manual."""
    guide_dir = os.path.join(os.path.dirname(index_html), "Hardware_Manual_guide")

    print("Parsing register summary (address order)...")
    registers = parse_address_order_summary(guide_dir)
    print(f"  Found {len(registers)} registers")

    # Collect unique detail pages to parse
    detail_pages = {}
    for reg in registers:
        if reg.detail_page and reg.detail_page not in detail_pages:
            detail_pages[reg.detail_page] = None

    print(f"Parsing {len(detail_pages)} register detail pages...")
    for page in detail_pages:
        bits, notes = parse_register_detail(guide_dir, page)
        detail_pages[page] = (bits, notes)

    # Assign bits to registers. Many registers share a detail page,
    # so we need to match by register name.
    regs_with_bits = 0
    for reg in registers:
        if reg.detail_page and reg.detail_page in detail_pages:
            bits, notes = detail_pages[reg.detail_page]
            if bits:
                reg.bits = bits
                regs_with_bits += 1
            if notes:
                reg.notes = notes

    # Copy bits for registers that share layouts but have different detail pages
    # INTREQ/INTREQR share INTENA/INTENAR bit layout
    bit_copies = {"INTREQ": "INTENA", "INTREQR": "INTENAR"}
    reg_by_name = {r.name: r for r in registers}
    for target, source in bit_copies.items():
        if target in reg_by_name and source in reg_by_name:
            src_reg = reg_by_name[source]
            tgt_reg = reg_by_name[target]
            if src_reg.bits and not tgt_reg.bits:
                tgt_reg.bits = src_reg.bits
                regs_with_bits += 1

    # Parse additional bit tables from ECS appendix and other non-detail pages
    ecs_bit_pages = {
        "BEAMCON0": "node00A7.html",  # ECS beam counter control
    }
    for regname, page in ecs_bit_pages.items():
        if regname in reg_by_name and not reg_by_name[regname].bits:
            bits, _ = parse_register_detail(guide_dir, page)
            if bits:
                reg_by_name[regname].bits = bits
                regs_with_bits += 1

    print(f"  Registers with bit definitions: {regs_with_bits}")

    # Parse CIA registers (8520 chips)
    print("Parsing CIA registers...")
    cia_regs = parse_cia_registers(guide_dir)
    registers.extend(cia_regs)
    print(f"  Found {len(cia_regs)} CIA registers")

    print("Parsing chapter index...")
    chapters = parse_chapters(index_html)
    print(f"  Found {len(chapters)} chapters/appendices")

    return registers, chapters


def parse_cia_registers(guide_dir: str) -> list[Register]:
    """Parse 8520 CIA chip registers from Appendix F and port assignment pages."""
    cia_regs = []

    # CIA register map from node012F.html
    # CIA-A base: $BFE001 (directly), CIA-B base: $BFD000
    # Register offsets: 0-F, accessed at base + reg*$100
    cia_map = [
        (0x0, "PRA", "R/W", "Peripheral Data Register A"),
        (0x1, "PRB", "R/W", "Peripheral Data Register B"),
        (0x2, "DDRA", "R/W", "Data Direction Register A"),
        (0x3, "DDRB", "R/W", "Data Direction Register B"),
        (0x4, "TALO", "R/W", "Timer A Low"),
        (0x5, "TAHI", "R/W", "Timer A High"),
        (0x6, "TBLO", "R/W", "Timer B Low"),
        (0x7, "TBHI", "R/W", "Timer B High"),
        (0x8, "TODLOW", "R/W", "Event counter bits 7-0"),
        (0x9, "TODMID", "R/W", "Event counter bits 15-8"),
        (0xA, "TODHI", "R/W", "Event counter bits 23-16"),
        (0xC, "SDR", "R/W", "Serial Data Register"),
        (0xD, "ICR", "R/W", "Interrupt Control Register"),
        (0xE, "CRA", "R/W", "Control Register A"),
        (0xF, "CRB", "R/W", "Control Register B"),
    ]

    # CIA-A port assignments (from node014A)
    ciaa_pra_bits = [
        BitDef(7, "PA7/FIRE1", "Game port 1, pin 6 (fire button)"),
        BitDef(6, "PA6/FIRE0", "Game port 0, pin 6 (fire button)"),
        BitDef(5, "PA5/DSKRDY", "Disk ready (active low)"),
        BitDef(4, "PA4/DSKTRACK0", "Disk track 00 detect (active low)"),
        BitDef(3, "PA3/DSKPROT", "Disk write protect (active low)"),
        BitDef(2, "PA2/DSKCHANGE", "Disk change (active low)"),
        BitDef(1, "PA1/LED", "Power LED (0=bright)"),
        BitDef(0, "PA0/OVL", "Memory overlay bit"),
    ]

    # CIA-B port assignments
    ciab_pra_bits = [
        BitDef(7, "PA7/DTR", "Serial DTR (active low)"),
        BitDef(6, "PA6/RTS", "Serial RTS (active low)"),
        BitDef(5, "PA5/CD", "Serial carrier detect (active low)"),
        BitDef(4, "PA4/CTS", "Serial CTS (active low)"),
        BitDef(3, "PA3/DSR", "Serial DSR (active low)"),
        BitDef(2, "PA2/SEL", "Centronics select"),
        BitDef(1, "PA1/POUT", "Centronics paper out"),
        BitDef(0, "PA0/BUSY", "Centronics busy"),
    ]
    ciab_prb_bits = [
        BitDef(7, "PB7/DSKMOTOR", "Disk motor control (active low, latched per-drive)"),
        BitDef(6, "PB6/DSKSEL3", "Select drive 3 (active low)"),
        BitDef(5, "PB5/DSKSEL2", "Select drive 2 (active low)"),
        BitDef(4, "PB4/DSKSEL1", "Select drive 1 (active low)"),
        BitDef(3, "PB3/DSKSEL0", "Select drive 0 / internal (active low)"),
        BitDef(2, "PB2/DSKSIDE", "Disk head select (0=upper)"),
        BitDef(1, "PB1/DSKDIREC", "Disk seek direction (0=inward)"),
        BitDef(0, "PB0/DSKSTEP", "Disk step pulse (active low, strobe)"),
    ]

    # Parse CRA and CRB from their detail pages
    cra_bits, _ = parse_register_detail(guide_dir, "node0146.html")
    crb_bits, _ = parse_register_detail(guide_dir, "node0148.html")

    # ICR bits (from node0143/0144)
    icr_bits = [
        BitDef(7, "IR/S/C", "Interrupt (read) / Set-Clear (write)"),
        BitDef(4, "FLG", "FLAG pin interrupt"),
        BitDef(3, "SP", "Serial port interrupt"),
        BitDef(2, "ALRM", "TOD alarm interrupt"),
        BitDef(1, "TB", "Timer B underflow interrupt"),
        BitDef(0, "TA", "Timer A underflow interrupt"),
    ]

    # Build CIA-A registers
    for offset, name, access, function in cia_map:
        addr_a = 0xBFE001 + offset * 0x100
        reg = Register(
            name=f"CIAA_{name}",
            address=addr_a,
            access=access,
            chip="CIA-A",
            function=f"CIA-A: {function}",
        )
        if name == "PRA":
            reg.bits = ciaa_pra_bits
        elif name == "CRA":
            reg.bits = cra_bits if cra_bits else []
        elif name == "CRB":
            reg.bits = crb_bits if crb_bits else []
        elif name == "ICR":
            reg.bits = icr_bits
        cia_regs.append(reg)

    # Build CIA-B registers
    for offset, name, access, function in cia_map:
        addr_b = 0xBFD000 + offset * 0x100
        reg = Register(
            name=f"CIAB_{name}",
            address=addr_b,
            access=access,
            chip="CIA-B",
            function=f"CIA-B: {function}",
        )
        if name == "PRA":
            reg.bits = ciab_pra_bits
        elif name == "PRB":
            reg.bits = ciab_prb_bits
        elif name == "CRA":
            reg.bits = cra_bits if cra_bits else []
        elif name == "CRB":
            reg.bits = crb_bits if crb_bits else []
        elif name == "ICR":
            reg.bits = icr_bits
        cia_regs.append(reg)

    return cia_regs


def output_summary(registers: list[Register], chapters: list[Chapter]):
    """Print summary to stdout."""
    print(f"\nAmiga Hardware Reference Manual")
    print(f"{'='*50}")
    print(f"Registers:       {len(registers)}")

    with_bits = sum(1 for r in registers if r.bits)
    print(f"With bit defs:   {with_bits}/{len(registers)}")

    # Count by chip
    chips = {}
    for r in registers:
        for c in r.chip:
            if c in 'ADP':
                chips[c] = chips.get(c, 0) + 1
    chip_names = {'A': 'Agnus', 'D': 'Denise', 'P': 'Paula'}
    for c in 'ADP':
        print(f"  {chip_names.get(c, c)}: {chips.get(c, 0)}")

    ecs = sum(1 for r in registers if r.ecs)
    print(f"ECS registers:   {ecs}")
    print(f"Chapters:        {len(chapters)}")

    print(f"\n{'Name':<12} {'Addr':<6} {'R/W':<4} {'Chip':<5} {'Bits':<5} Function")
    print("-" * 80)
    for reg in registers:
        bits_str = f"{len(reg.bits):2d}" if reg.bits else "  "
        ecs_mark = "(E)" if reg.ecs else "   "
        print(f"{reg.name:<12} ${reg.address:03X}   {reg.access:<4} {reg.chip:<5} {bits_str}  {ecs_mark} {reg.function[:40]}")


def output_json(registers: list[Register], chapters: list[Chapter], outfile: str):
    """Write JSON output."""
    data = {
        "source": "Amiga Hardware Reference Manual",
        "base_address": "0xDFF000",
        "registers": [],
        "chapters": [],
    }

    for reg in registers:
        rd = {
            "name": reg.name,
            "address": f"0x{reg.address:03X}",
            "address_68k": f"0x{0xDFF000 + reg.address:06X}",
            "access": reg.access,
            "chip": reg.chip,
            "function": reg.function,
        }
        if reg.ecs:
            rd["ecs"] = True
        if reg.dma_only:
            rd["dma_only"] = True
        if reg.dma_usually:
            rd["dma_usually"] = True
        if reg.pointer_pair:
            rd["pointer_pair"] = True
        if reg.copper_protected:
            rd["copper_protected"] = True
        if reg.copper_danger:
            rd["copper_danger"] = True
        if reg.bits:
            rd["bits"] = [asdict(b) for b in reg.bits]
        data["registers"].append(rd)

    for ch in chapters:
        data["chapters"].append({
            "number": ch.number,
            "title": ch.title,
        })

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(registers)} registers to {outfile}")


def output_markdown(registers: list[Register], chapters: list[Chapter], outfile: str):
    """Write Markdown reference."""
    lines = [
        "# Amiga Hardware Register Reference",
        "",
        f"Extracted from the Amiga Hardware Reference Manual. {len(registers)} registers.",
        "",
        "Base address: `$DFF000` — add register offset to get 68000 address.",
        "",
        "## Register Map (Address Order)",
        "",
        "| Address | Name | R/W | Chip | Function |",
        "|---------|------|-----|------|----------|",
    ]

    for reg in registers:
        ecs = " (ECS)" if reg.ecs else ""
        lines.append(
            f"| `${reg.address:03X}` | "
            f"[{reg.name}](#{reg.name.lower()}) | "
            f"{reg.access} | {reg.chip} | "
            f"{reg.function}{ecs} |"
        )

    lines.append("")
    lines.append("## Register Details")
    lines.append("")

    for reg in registers:
        lines.append(f"### {reg.name}")
        lines.append(f"**{reg.function}**")
        lines.append("")
        lines.append(f"- **Address**: `${reg.address:03X}` (`$DFF{reg.address:03X}`)")
        lines.append(f"- **Access**: {reg.access}")
        lines.append(f"- **Chip**: {reg.chip}")
        if reg.ecs:
            lines.append("- **ECS**: Yes")

        flags = []
        if reg.dma_only:
            flags.append("DMA channel only")
        if reg.dma_usually:
            flags.append("DMA channel usually, processor sometimes")
        if reg.pointer_pair:
            flags.append("Address register pair (must be even, chip memory)")
        if reg.copper_protected:
            flags.append("Not writable by Copper")
        if reg.copper_danger:
            flags.append("Copper-writable only with COPCON danger bit set")
        if flags:
            lines.append(f"- **Flags**: {', '.join(flags)}")

        if reg.bits:
            lines.append("")
            lines.append("| Bit | Name | Description |")
            lines.append("|-----|------|-------------|")
            for b in sorted(reg.bits, key=lambda b: -b.bit):
                lines.append(f"| {b.bit:2d} | {b.name} | {b.description} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    if chapters:
        lines.append("## Manual Chapters")
        lines.append("")
        for ch in chapters:
            prefix = "Appendix" if ch.number.isalpha() else "Chapter"
            lines.append(f"- **{prefix} {ch.number}**: {ch.title}")
        lines.append("")

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(registers)} registers to {outfile}")


def main():
    parser = argparse.ArgumentParser(description="Parse Amiga Hardware Reference Manual")
    parser.add_argument("html", help="Path to Hardware_Manual.html index file")
    parser.add_argument("--output", choices=["json", "md", "summary"], default="summary")
    parser.add_argument("--outfile", help="Output file path")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    registers, chapters = parse_full_manual(args.html)

    if args.output == "json":
        output_json(registers, chapters, args.outfile or "amiga_hw_registers.json")
    elif args.output == "md":
        output_markdown(registers, chapters, args.outfile or "amiga_hw_reference.md")
    else:
        output_summary(registers, chapters)


if __name__ == "__main__":
    main()

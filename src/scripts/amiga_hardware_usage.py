from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.scripts.kb.paths import AMIGA_HW_REGISTERS_JSON, AMIGA_HW_SYMBOLS_JSON

HARDWARE_BASES = ("_custom", "_ciaa", "_ciab")


def symbol_refs_from_listing_text(text: str, *, copper_row: bool) -> list[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for match in re.finditer(r"_custom\+([A-Za-z_][A-Za-z0-9_]*(?:\+[A-Za-z_][A-Za-z0-9_]*)*)", text):
        symbol = match.group(1)
        refs.add(("_custom", symbol))
        refs.add(("_custom", symbol.split("+", 1)[0]))
    for match in re.finditer(r"_(ciaa|ciab)\+([A-Za-z_][A-Za-z0-9_]*)", text):
        refs.add((f"_{match.group(1)}", match.group(2)))
    if copper_row:
        match = re.match(r"\s*dc\.w\s+([A-Za-z_][A-Za-z0-9_]*)(?:[,+]|$)", text)
        if match:
            refs.add(("_custom", match.group(1)))
    return sorted(refs)


def group_features(base_name: str, symbol: str, *, copper_row: bool) -> list[str]:
    base = base_name.removeprefix("_").casefold()
    head = symbol.split("+", 1)[0].casefold()
    meta = _register_metadata().get((base_name, head), {})
    function = str(meta.get("function", "")).casefold()
    features: set[str] = set()
    if base == "custom":
        if copper_row or _mentions(function, "copper") or head.startswith("cop") or head == "copper":
            features.update({"hardware:custom/copper", "value_domain:amiga.custom.copper"})
        if _is_display_register(head, function):
            features.update({"hardware:custom/display", "value_domain:amiga.custom.display_config"})
        if _mentions(function, "audio") or head.startswith("aud") or head == "adkcon":
            features.add("hardware:custom/audio")
        if _mentions(function, "dma") or head in {"dmacon", "dmaconr"}:
            features.update({"hardware:custom/dma", "value_domain:amiga.custom.dma_bits"})
        if _mentions(function, "interrupt") or head in {"intena", "intenar", "intreq", "intreqr"}:
            features.update({"hardware:custom/interrupt", "value_domain:amiga.custom.interrupt_bits"})
        if _mentions(function, "disk") or head.startswith("dsk"):
            features.add("hardware:custom/disk")
    elif base in {"ciaa", "ciab"}:
        if _mentions(function, "disk") or "dsk" in head or head in {"ciapra", "ciaprb"}:
            features.update({"hardware:cia/disk", "value_domain:amiga.cia.disk"})
    return sorted(features)


def _is_display_register(symbol: str, function: str) -> bool:
    if any(
        symbol.startswith(prefix)
        for prefix in ("bpl", "spr", "ddf", "diw", "color")
    ):
        return True
    if symbol in {"beamcon0", "vposr", "vposw", "vhposr", "vhposw", "fmode"}:
        return True
    return any(
        word in function
        for word in ("bitplane", "sprite", "display", "window", "color", "beam", "modulo")
    )


def _mentions(text: str, word: str) -> bool:
    return word in text


@lru_cache(maxsize=1)
def _register_metadata() -> dict[tuple[str, str], dict[str, Any]]:
    manual_by_address = _manual_registers_by_address(AMIGA_HW_REGISTERS_JSON)
    metadata: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        payload = json.loads(Path(AMIGA_HW_SYMBOLS_JSON).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return metadata
    for row in payload.get("registers", []):
        if not isinstance(row, dict):
            continue
        base_symbol = row.get("base_symbol")
        symbols = row.get("symbols")
        if not isinstance(base_symbol, str) or not isinstance(symbols, list):
            continue
        try:
            address = int(str(row.get("cpu_address")), 0)
        except (TypeError, ValueError):
            address = -1
        manual = manual_by_address.get(address, {})
        for symbol in symbols:
            if isinstance(symbol, str) and symbol:
                metadata[(base_symbol, symbol.casefold())] = manual
    return metadata


def _manual_registers_by_address(path: Path) -> dict[int, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    rows: dict[int, dict[str, Any]] = {}
    for row in payload.get("registers", []):
        if not isinstance(row, dict):
            continue
        try:
            rows[int(str(row.get("address_68k")), 0)] = row
        except (TypeError, ValueError):
            continue
    return rows

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.scripts.kb.paths import AMIGA_HW_REGISTERS_JSON, AMIGA_HW_SYMBOLS_JSON

HARDWARE_BASES = ("_custom", "_ciaa", "_ciab")

_CUSTOM_REF_RE = re.compile(r"_custom\+([A-Za-z_][A-Za-z0-9_]*(?:\+[A-Za-z_][A-Za-z0-9_]*)*)")
_CIA_REF_RE = re.compile(r"_(ciaa|ciab)\+([A-Za-z_][A-Za-z0-9_]*)")
_COPPER_SYMBOL_RE = re.compile(r"\s*dc\.w\s+([A-Za-z_][A-Za-z0-9_]*)(?:[,+]|$)")
_COPPER_NUMERIC_RE = re.compile(r"\s*dc\.w\s+\$([0-9A-Fa-f]{1,4})(?:[,+]|$)")
_BPLCON0_VALUE_RE = re.compile(r"BPLCON0\s*,\s*\$([0-9A-Fa-f]{1,4})")
_CUSTOM_BPLCON0_VALUE_RE = re.compile(r"_CUSTOM\+BPLCON0(?:\.\w+)?\s*,?\s*#?\$([0-9A-Fa-f]{1,4})")
_VALUE_CUSTOM_BPLCON0_RE = re.compile(r"#?\$([0-9A-Fa-f]{1,4})\s*,\s*_CUSTOM\+BPLCON0")
_COPPER_SECOND_WORD_RE = re.compile(r"\s*dc\.w\s+[^,]+,\s*\$([0-9A-Fa-f]{1,4})(?:\s|;|$)")


def display_features_from_listing_text(text: str, *, copper_row: bool) -> list[str]:
    return display_features_from_symbol_refs(
        text,
        symbol_refs_from_listing_text(text, copper_row=copper_row),
        copper_row=copper_row,
    )


def display_features_from_symbol_refs(
    text: str,
    refs: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    *,
    copper_row: bool,
) -> list[str]:
    features: set[str] = set()
    symbols = {symbol.split("+", 1)[0].casefold() for base, symbol in refs if base == "_custom"}
    if "bplcon0" in symbols:
        bitplanes = _bplcon0_bitplanes(text)
        if bitplanes is None and copper_row:
            value = _copper_row_second_word(text)
            if value is not None:
                bitplanes = (value >> 12) & 0x7
        features.add("display:bplcon0")
        if bitplanes is not None:
            features.add(f"display:bitplanes:{bitplanes}")
        if "COLORON" in text.upper():
            features.add("display:color")
        if "HIRES" in text.upper():
            features.add("display:hires")
    if any(symbol.startswith("color") for symbol in symbols):
        features.add("display:palette")
    if any(symbol.startswith("bpl") and symbol.endswith("pt") for symbol in symbols) or "bplpt" in symbols:
        features.add("display:bitplane_pointers")
    if any(symbol in {"diwstrt", "diwstop"} for symbol in symbols):
        features.add("display:window")
    if any(symbol in {"ddfstrt", "ddfstop"} for symbol in symbols):
        features.add("display:fetch_window")
    if any(symbol.startswith("spr") and symbol.endswith("pt") for symbol in symbols) or "sprpt" in symbols:
        features.add("display:sprite_pointers")
    return sorted(features)


def symbol_refs_from_listing_text(text: str, *, copper_row: bool) -> list[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for match in _CUSTOM_REF_RE.finditer(text):
        symbol = match.group(1)
        refs.add(("_custom", symbol))
        refs.add(("_custom", symbol.split("+", 1)[0]))
    for match in _CIA_REF_RE.finditer(text):
        refs.add((f"_{match.group(1)}", match.group(2)))
    if copper_row:
        match = _COPPER_SYMBOL_RE.match(text)
        if match:
            refs.add(("_custom", match.group(1)))
        numeric = _COPPER_NUMERIC_RE.match(text)
        if numeric:
            symbol = _custom_symbol_for_copper_register_word(int(numeric.group(1), 16))
            if symbol:
                refs.add(("_custom", symbol))
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


def _bplcon0_bitplanes(text: str) -> int | None:
    upper = text.upper()
    if "BPU" in upper:
        value = 0
        if "BPU0" in upper:
            value |= 1
        if "BPU1" in upper:
            value |= 2
        if "BPU2" in upper:
            value |= 4
        return value
    match = _BPLCON0_VALUE_RE.search(text)
    if not match:
        match = _CUSTOM_BPLCON0_VALUE_RE.search(upper)
    if not match:
        match = _VALUE_CUSTOM_BPLCON0_RE.search(upper)
    if not match:
        return None
    return (int(match.group(1), 16) >> 12) & 0x7


def _copper_row_second_word(text: str) -> int | None:
    match = _COPPER_SECOND_WORD_RE.match(text)
    if not match:
        return None
    return int(match.group(1), 16)


def _custom_symbol_for_copper_register_word(word: int) -> str | None:
    if word & 1:
        return None
    return _custom_symbol_by_offset().get(word & 0x01FE)


@lru_cache(maxsize=1)
def _custom_symbol_by_offset() -> dict[int, str]:
    symbols: dict[int, str] = {}
    try:
        payload = json.loads(Path(AMIGA_HW_SYMBOLS_JSON).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return symbols
    for row in payload.get("registers", []):
        if not isinstance(row, dict):
            continue
        if row.get("base_symbol") != "_custom":
            continue
        names = row.get("symbols")
        if not isinstance(names, list):
            continue
        try:
            offset = int(str(row.get("offset")), 0)
        except (TypeError, ValueError):
            continue
        for name in names:
            if isinstance(name, str) and name:
                symbols.setdefault(offset, name)
                break
    return symbols


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

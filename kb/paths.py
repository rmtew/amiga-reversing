"""Canonical KB project paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
M68K_INSTRUCTIONS_JSON = KNOWLEDGE_DIR / "m68k_instructions.json"
AMIGA_OS_REFERENCE_JSON = KNOWLEDGE_DIR / "amiga_os_reference.json"
AMIGA_HUNK_FORMAT_JSON = KNOWLEDGE_DIR / "amiga_hunk_format.json"
AMIGA_HW_SYMBOLS_JSON = KNOWLEDGE_DIR / "amiga_hw_symbols.json"
AMIGA_HW_REGISTERS_JSON = KNOWLEDGE_DIR / "amiga_hw_registers.json"

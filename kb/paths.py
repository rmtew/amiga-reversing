"""Canonical KB project paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
M68K_INSTRUCTIONS_JSON = KNOWLEDGE_DIR / "m68k_instructions.json"
AMIGA_OS_REFERENCE_INCLUDES_PARSED_JSON = KNOWLEDGE_DIR / "amiga_ndk_includes_parsed.json"
AMIGA_OS_REFERENCE_OTHER_PARSED_JSON = KNOWLEDGE_DIR / "amiga_ndk_other_parsed.json"
AMIGA_OS_REFERENCE_CORRECTIONS_JSON = KNOWLEDGE_DIR / "amiga_ndk_corrections.json"
AMIGA_HUNK_FORMAT_JSON = KNOWLEDGE_DIR / "amiga_hunk_format.json"
AMIGA_HW_SYMBOLS_JSON = KNOWLEDGE_DIR / "amiga_hw_symbols.json"
AMIGA_HW_REGISTERS_JSON = KNOWLEDGE_DIR / "amiga_hw_registers.json"

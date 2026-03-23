#!/usr/bin/env py.exe
"""CLI wrapper for kb.m68k_parser."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb.m68k_parser import main

__all__ = ["main"]


if __name__ == "__main__":
    main()

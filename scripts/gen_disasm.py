#!/usr/bin/env py.exe
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from disasm.cli import main


if __name__ == "__main__":
    main()

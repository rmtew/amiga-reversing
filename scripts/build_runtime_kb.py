"""CLI wrapper for kb.runtime_builder."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb.runtime_builder import main

__all__ = ["main"]


if __name__ == "__main__":
    main()

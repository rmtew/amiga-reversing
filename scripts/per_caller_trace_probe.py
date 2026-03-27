from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from m68k.per_caller_trace import get_per_caller_trace


def main() -> int:
    trace = get_per_caller_trace()
    print(trace.path if trace else None)
    if trace is not None:
        trace.event("probe", source_addr=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

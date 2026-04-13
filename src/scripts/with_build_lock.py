from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import msvcrt


ROOT = Path(__file__).resolve().parents[2]
LOCK_DIR = ROOT / "src" / "build"
LOCK_PATH = LOCK_DIR / ".build.lock"
LOCK_TIMEOUT_SECONDS = 600.0
LOCK_POLL_SECONDS = 0.2


def _acquire_lock(lock_file) -> None:
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for build lock: {LOCK_PATH}")
            time.sleep(LOCK_POLL_SECONDS)


def _release_lock(lock_file) -> None:
    lock_file.seek(0)
    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: with_build_lock.py <command> [args...]", file=sys.stderr)
        return 2
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+b") as lock_file:
        _acquire_lock(lock_file)
        try:
            env = os.environ.copy()
            env["AMIGA_BUILD_LOCK_HELD"] = "1"
            if sys.argv[1] == "--batch-env":
                script = env.get("AMIGA_BUILD_LOCK_SCRIPT", "")
                args = env.get("AMIGA_BUILD_LOCK_ARGS", "").strip()
                if args in ('""', "''"):
                    args = ""
                if not script:
                    print("usage: with_build_lock.py --batch-env with AMIGA_BUILD_LOCK_SCRIPT set", file=sys.stderr)
                    return 2
                command = f'call "{script}" --lock-held'
                if args:
                    command += " " + args
                if env.get("AMIGA_BUILD_LOCK_DEBUG") == "1":
                    print(command, file=sys.stderr)
                result = subprocess.run(
                    command,
                    cwd=str(ROOT),
                    env=env,
                    check=False,
                    shell=True,
                )
            else:
                command = sys.argv[1:]
                result = subprocess.run(command, cwd=str(ROOT), env=env, check=False)
            return int(result.returncode)
        finally:
            _release_lock(lock_file)


if __name__ == "__main__":
    raise SystemExit(main())

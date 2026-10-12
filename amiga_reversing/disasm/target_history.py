"""Cross-interface serialization and byte-preserving target history writes."""

from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_registry_guard = threading.Lock()
_locks: dict[str, threading.RLock] = {}
_local = threading.local()


@contextmanager
def target_lock(target_dir: Path) -> Iterator[None]:
    """Serialize threads/processes; nesting in one thread is safe.

    The sidecar inode remains stable across atomic history replacement. All
    writers must acquire this lock before reading their expected revision.
    """
    directory = target_dir.resolve()
    key = str(directory)
    with _registry_guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        held = getattr(_local, "held", None)
        if held is None:
            held = _local.held = set()
        if key in held:
            yield
            return
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / ".target-history.lock").open("a+b") as handle:
            if os.name == "nt":
                import msvcrt

                if handle.seek(0, os.SEEK_END) == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            held.add(key)
            try:
                yield
            finally:
                held.remove(key)
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def history_revision(target_dir: Path) -> str:
    """Digest the exact history bytes, including unknown fields and formatting."""
    with target_lock(target_dir):
        digest = hashlib.sha256()
        for name in ("manual_actions.jsonl", "decision_journal.jsonl"):
            path = target_dir / name
            data = path.read_bytes() if path.exists() else b""
            digest.update(name.encode("ascii") + b"\0")
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        return digest.hexdigest()


def atomic_append_history(path: Path, suffix: bytes) -> None:
    """Append all-or-nothing while preserving every existing byte.

    Caller holds target_lock and has validated the complete proposed history.
    Atomic replace prevents readers from observing a partially written batch.
    """
    original = path.read_bytes() if path.exists() else b""
    separator = b"\n" if original and not original.endswith(b"\n") else b""
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            if path.exists() and hasattr(os, "fchmod"):
                os.fchmod(handle.fileno(), path.stat().st_mode & 0o777)
            handle.write(original + separator + suffix)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

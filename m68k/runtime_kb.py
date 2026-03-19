"""Shared loaders for canonical and runtime knowledge artifacts."""

from __future__ import annotations

import importlib
import json
from functools import lru_cache
from pathlib import Path


PROJ_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = PROJ_ROOT / "knowledge"


def _load_json(name: str) -> dict:
    path = KNOWLEDGE / name
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_canonical_m68k_kb() -> dict:
    return _load_json("m68k_instructions.json")


@lru_cache(maxsize=1)
def load_canonical_os_kb() -> dict:
    return _load_json("amiga_os_reference.json")


@lru_cache(maxsize=1)
def load_canonical_hunk_kb() -> dict:
    return _load_json("amiga_hunk_format.json")


@lru_cache(maxsize=1)
def load_canonical_naming_rules() -> dict:
    return _load_json("naming_rules.json")


def _load_runtime_module(module_name: str):
    return importlib.import_module(f"knowledge.{module_name}")


@lru_cache(maxsize=1)
def load_m68k_runtime_kb() -> dict:
    payload = load_canonical_m68k_kb()
    runtime = _load_runtime_module("runtime_m68k").RUNTIME
    instructions = payload["instructions"]
    meta = dict(payload["_meta"])
    meta.update(runtime["derived_meta"])
    by_name = {inst["mnemonic"]: inst for inst in instructions}
    return {
        "instructions": instructions,
        "meta": meta,
        "by_name": by_name,
        "runtime": runtime,
    }


@lru_cache(maxsize=1)
def load_os_runtime_kb() -> dict:
    return _load_runtime_module("runtime_os").RUNTIME


@lru_cache(maxsize=1)
def load_hunk_runtime_kb() -> dict:
    return _load_runtime_module("runtime_hunk").RUNTIME


@lru_cache(maxsize=1)
def load_naming_runtime_kb() -> dict:
    return _load_runtime_module("runtime_naming").RUNTIME

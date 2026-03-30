Local vendored Amiga assembler include snapshots for assembly probes.

Rules:
- LF only.
- Lowercase paths to match emitted include strings.
- Used for local assembly and round-trip validation.
- Primary NDK parsing still reads the source trees on `D:\`.
- Regenerate from original NDK inputs via `scripts/sync_amiga_includes.py`.
- `_lib.i` files are derived from original raw includes plus `.fd` files.

Current snapshot:
- `ndk_2.0/include`
  - currently synced from `D:\NDK\NDK_2.0`

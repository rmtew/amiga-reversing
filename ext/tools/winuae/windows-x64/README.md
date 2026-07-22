# Windows headless WinUAE runtime bundle

This directory contains the checked-in Windows x64 tools used by the local
agentic reversing runtime:

- `winuae-gdb.exe` is the project-local Bartman WinUAE fork, built with the
  strict headless host-startup patch.
- `m68k-amiga-elf-gdb.exe` is Bartman's prebuilt GDB client.

Both executables are intentional repository resources. Their exact provenance,
hashes, and validation contract are recorded in `manifest.json`.
The corresponding WinUAE source history is retained on the local fork branch
`codex/local-workspace-build`.

The WinUAE Visual Studio project in
`resources/clone_amiga/WinUAE/od-win32/winuae_msvc15` writes its default x64
FullRelease executable directly to this directory. Build by-products such as
PDBs, logs, and temporary configuration files must not be committed.

No Kickstart ROM, disk image, HDF, target binary, or user-specific path belongs
in this directory.

## Local runner

Use `tools/run_winuae_headless.ps1` with a legal local Kickstart ROM. It keeps
mutable WinUAE state outside the repository in a new temporary directory for
each invocation by default, waits for the loopback GDB server, executes any
supplied GDB commands, and shuts down with GDB's orderly `kill` request. Pass
`-StateDirectory` only when deliberately retaining runtime state, such as a
future validated savestate workflow.

```powershell
.\tools\run_winuae_headless.ps1 -RomPath C:\path\to\kick34005.a500 \
  -GdbCommand @('info registers pc sp', 'x/8xb 0xfc0000')
```

To attach one original ADF as `DF0:`, pass its local path explicitly. The image
remains untracked and is never copied into the runtime state directory.

```powershell
.\tools\run_winuae_headless.ps1 -RomPath C:\path\to\kick34005.a500 \
  -Floppy0 .\bin\uploads\Pandora` (1988`)(Firebird).adf
```

For the first bounded execution-control probe, use `-ContinueSeconds` instead
of `-GdbCommand`. It keeps one hidden MI-mode GDB connection open, continues
for the requested wall-clock interval, interrupts it, records PC/SP, a small
ROM memory read, and the active Exec task's documented node information, then
kills the emulator. The JSON result is an observation only; it does not
establish that a target executable was reached.

```powershell
.\tools\run_winuae_headless.ps1 -RomPath C:\path\to\kick34005.a500 \
  -Floppy0 .\bin\uploads\Pandora` (1988`)(Firebird).adf -ContinueSeconds 8
```

`-LoadSegWatchSeconds` adds a second bounded phase after that initial pause.
It resolves the live `dos.library` base and `LoadSeg` LVO from the parsed NDK,
then reports a `LoadSeg` breakpoint hit and its filename argument or an
explicit timeout. It is an OS-loader observation, not a claim that the
observed program is the target under study.

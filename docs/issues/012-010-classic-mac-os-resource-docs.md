Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Document the external Classic Mac OS fixture inputs and the committed Mac
platform inventory check.

Problem:
Proposal 012 now has implemented Mac source/container parsers and tests, but
`RESOURCES.md` still only lists the older Amiga/M68K resources. A fresh checkout
does not clearly state where the optional MPW-GM image and `ndif2raw` provider
belong, or which command validates the committed Mac platform inventory.

Required work:
- Add the Classic Mac OS MPW-GM image path and `ndif2raw` provider path to the
  external resource documentation.
- Document the `macos-platform-kb` report/check command.
- Keep this as documentation only; do not change parser behavior or committed
  fixture policy.

Acceptance:
- `RESOURCES.md` names the paths used by the 012 tests and import code.
- `README.md` points users at the Mac platform KB check alongside the existing
  generated KB commands.
- Proposal 012 records the cleanup as a follow-up closure item.

Result:
- Resource setup now covers `resources/platform_macos/MPW-GM.img.bin` and
  `ext/tools/ndif2raw/ndif2raw.exe`.
- The README documents `uv run macos-platform-kb check` as the committed Mac
  source inventory consistency check.

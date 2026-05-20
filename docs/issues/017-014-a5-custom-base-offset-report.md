Status: implemented
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: 017-013 post-commit review

Scope:
Fix A5 hardware report identity when A5 is loaded with an address inside the
custom register block instead of exactly `_custom`.

Problem:
Post-017-013 review found that `a5-hardware-report` treated
`lea _custom+dmaconr,a5` as if A5 equalled `_custom`. That made `(a5)` look
like `bltddat` at offset `$0000`, when the effective register is `dmaconr` at
offset `$0002`. Letting this reach command payloads would record a durable
accepted hardware ref with the wrong hardware-register identity.

Required work:
- Carry the A5 definition's custom-register-block offset through lifetime and
  CFG accepted evidence.
- Resolve symbols and hardware addresses from effective offset
  `custom_base_offset + displacement`.
- Allow signed A5 displacements when the effective custom-register offset is
  still in range.
- Keep existing exact `_custom` evidence ids stable while making non-zero base
  offsets explicit.
- Add regression tests proving `_custom+dmaconr` does not produce `bltddat`.

Acceptance:
- A5 definitions inside the custom block expose `custom_base_offset`.
- Command-backed A5 hardware refs carry `custom_base_offset` and
  `hardware_register_offset`.
- Effective offsets outside the custom-register range are blocked.
- Signed displacements are accepted only through valid effective offsets.
- Focused reversing-loop tests pass.

Result:
- `_custom+dmaconr` now reports `(a5)` as `dmaconr` with hardware address
  `$DFF002`.
- Non-zero base-offset evidence ids include the base offset, while existing
  zero-offset ids remain unchanged.

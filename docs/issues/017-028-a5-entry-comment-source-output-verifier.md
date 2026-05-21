Status: active
Type: AFK
Source proposal: docs/proposals/017-pandora-post-hardening-reversal.md
Promoted from: review of 017-024 closeout

Scope:
Harden the A5 address-mode-preserving entry-comment verifier so it proves the
generated source output, not just listing/UI state.

Problem:
017-024 added entry-comment rendering for accepted A5 hardware refs whose
symbolic operand form would change encoding. Review found the rendered-source
verifier can fall back to `row.comment_text` when source rendering fails or
when the generated source text does not contain the expected comment. That lets
the verifier pass from listing JSON state rather than actual rendered `.s`
output.

Required work:
- Require successful generated-source rendering for the A5 entry-comment
  verifier path.
- Require the expected generated comment text to appear in the generated source
  output.
- Keep rejecting unsafe symbolic operand text such as `dmaconr(a5)` for the
  address-mode-preserving case.
- Add a regression test where listing row comment text is present but generated
  source output is missing the comment; the verifier must fail.
- Validate on the Pandora `s0:0000045C` style case or an equivalent focused
  fixture.

Acceptance:
- A5 entry-comment verification cannot pass from listing/UI comment state alone.
- Generated source contains the expected entry comment and does not contain an
  unsafe symbolic operand rewrite.
- Focused tests pass.

# PRD 009: Symbol, Equate, and Struct Navigation

## Purpose

Make symbolic navigation keyboard-driven and palette-visible for labels, RS values, equates, structs, and other semantic references in the listing.

## Scope

- Follow references from the current **Listing Selection** or **Listing Element**.
- Maintain navigation history for forward/back movement.
- Support relative navigation such as previous/next label or hunk.
- Integrate navigation commands with the command palette and key-binding registry.

## Requirements

- Right-arrow style navigation follows the selected reference when the selection has one clear target.
- Left-arrow style navigation returns through the navigation stack.
- Ctrl-modified navigation can open or focus the relevant Navigate dialog detail list for ambiguous references.
- Previous/next label and previous/next hunk commands are available from the palette and may have default bindings.
- Navigation commands are catalog entries marked as transient, not **Manual Action Log** actions.
- Existing Ctrl-click behavior and Navigate dialog behavior remain compatible with keyboard navigation.
- Navigation targets use symbolic names from analysis facts, target metadata, and accepted manual actions.

## Non-Goals

- Manual editing of labels, equates, or structs.
- Building new Amiga OS/type analysis.
- User-defined key binding persistence.

## Verification

- Web source tests for navigation command availability and stack behavior.
- CDP/e2e tests for follow-reference, back/forward, ambiguous reference detail opening, and relative label navigation.
- Tests must cover label, equate, and at least one struct/RS-style reference when fixtures provide them.

## Issues

- [009-001: Follow Reference Navigation](../issues/009-001-follow-reference-navigation.md)
- [009-002: Ambiguous Reference Navigation](../issues/009-002-ambiguous-reference-navigation.md)
- [009-003: Relative Navigation Commands](../issues/009-003-relative-navigation-commands.md)
- [009-004: Struct and RS Navigation Fixtures](../issues/009-004-struct-rs-navigation-fixtures.md)
- [009-005: PRD 009 Review and Tightening](../issues/009-005-prd-009-review-and-tightening.md)

## Open Questions

- Exact default bindings for follow/back when browser/platform shortcuts conflict.
- Whether ambiguous references should default to first match or force the detail list.

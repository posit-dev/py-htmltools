# `Tagifiable.tagify()` returns `Tagified`, not a narrower specific type

- **Date:** 2026-05-18
- **Context:** PR posit-dev/py-htmltools#106 (issue #105) introduced the
  Tagified type system, then needed downstream rollout to `shinychat`,
  `chatlas`, `brand-yml`, and `py-shiny`. Each downstream had to choose
  an annotation for its custom `.tagify()` methods.
- **Status:** Accepted

## Decision

The `Tagifiable` protocol's return type is `Tagified`, the broad union
of all post-`.tagify()` shapes:

```python
Tagified = TypeAliasType(
    "Tagified",
    "Tag[TagifiedNode] | TagList[TagifiedNode] | TagLeaf",
)
```

Downstream `.tagify()` implementations annotate `-> Tagified`. The
narrower `TagifiedNode`, `TagifiedTagList`, and `TagNodeLeaf` aliases
live in `htmltools._core` for internal use only — they are
deliberately **not** exported from `htmltools`.

## Why `Tagified` instead of the narrower internal aliases?

### Single concept to learn

Every downstream `.tagify()` author writes the same annotation. The
contract is "I return something fully tagified" — they don't need to
classify whether their implementation returns a `Tag`, a `TagList`, or
a leaf. The protocol stays uniform.

### `.tagify()` results are immediately serialized, not branched on

Surveying actual consumers (across `htmltools`, `shiny`, `shinychat`,
`chatlas`, `brand-yml`):

- Internal: `TagList.tagify()` recurses; `get_html_string` / `render` /
  `save_html` walk the result for HTML serialization.
- External: `_repr_html_`-style shims call `str(self.tagify())`.
- Shiny: `App.__init__`'s `ui` arg is fed straight back into htmltools
  for rendering.

None of these consumers branch on which arm of the union came back.
The one observed exception is `tests/pytest/test_sidebar.py`, which
unpacks `sb.tagify()` as a 2-tuple; that single site casts to `TagList`
before unpacking. Cheap.

### Narrow types caused more pyright noise than they prevented

During the implementation we explored returning the narrow internal
shapes directly (e.g. `Tag[TagifiedNode]` / `TagList[TagifiedNode]`).
The narrower returns surfaced `Tag[Unknown]` / `TagList[Unknown]`
leaks in downstream pyright runs (notably py-shiny's accordion /
navset / sidebar / card paths), each of which required its own `cast`
to widen back. The bookkeeping cost exceeded the static-safety win.

### The exhaustively-tagified contract is what matters

`Tagified` excludes the `Tagifiable` arm of `TagNode`. That is the
property `.tagify()` actually promises: the returned tree contains no
un-resolved `Tagifiable` objects. Whether the root is a `Tag`, a
`TagList`, or a leaf is a structural detail; the "fully tagified"
guarantee is the same.

## Trade-off

Consumers that *do* need a specific arm (rare — currently only test
code) must `cast` or `isinstance`-narrow. Acceptable: it's one line at
each site, and `isinstance` is what we already do for runtime safety.

## Affected packages

This decision was applied to:

- `htmltools.Tagifiable.tagify` (the protocol)
- `htmltools._jsx.JSXTag.tagify` (narrow `Tag[TagifiedNode]` retained
  — it's internal, not part of the downstream-author API)
- `shinychat._chat_bookmark`, `shinychat._chat_normalize_chatlas`
- `chatlas._content` (three `tagify` methods)
- `brand_yml.logo` (two `Logo.tagify` methods)
- `shiny.ui._accordion.AccordionPanel.tagify`, `_card.CardItem.tagify`,
  `_sidebar.Sidebar.tagify`, `_navs.NavSet.tagify`

## Related

- `2026-05-18-tag-mutation-wide-tagchild.md`

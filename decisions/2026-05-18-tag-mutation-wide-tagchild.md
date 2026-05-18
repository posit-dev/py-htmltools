# Tag / TagList mutation methods accept wide `TagChild`, not `TagNodeT`

- **Date:** 2026-05-18
- **Context:** PR posit-dev/py-htmltools#106 (issue #105) — introduced the
  Tagified type system: `Tag` and `TagList` are generic in their child
  type `TagNodeT` (default `TagNode`), and `Tagifiable.tagify()` returns
  the tighter `Tagified` union.
- **Status:** Accepted

## Decision

`Tag.append` / `Tag.insert` / `Tag.extend` / `TagList.append` /
`TagList.insert` / `TagList.extend` / `TagList.__add__` /
`TagList.__radd__` all keep their parameter type as the wide
`TagChild`, even though `Tag` and `TagList` are generic in `TagNodeT`.

The obvious-looking alternative — narrowing mutation to `TagNodeT` — is
rejected.

## Why not `TagNodeT`?

`TagChild` is **not** just the element type. It is the recursive
sequence-flattening alias:

```python
TagChild = Union[
    Tag, TagList, Tagifiable, MetadataNode, ReprHtml,
    str, HTML, int, float, None,
    Sequence["TagChild"],   # <-- the flattening arm
]
```

The `Sequence["TagChild"]` arm is what lets every caller write:

```python
tag.append([a, b, [c, d]])      # nested lists flatten
tl.extend([[x, y], z])           # mixed flat + nested
TagList(a, [b, c], d)            # constructor too
```

`_tagchilds_to_tagnodes` walks the structure inside each mutation and
returns a flat `list[TagNode]`. Narrowing `append(x: TagNodeT)` would
type-reject every nested-list mutation, including in the *default*
`Tag[TagNode]` case, which is the call site for ~all existing user
code.

## Why doesn't narrowing buy us static safety either?

The hoped-for win of narrowing — statically rejecting
`Tag[TagifiedNode].append(some_tagifiable)` — collapses for the common
case:

- Default `Tag` is `Tag[TagNode]`.
- `TagNode = Tagifiable | TagifiedNode`.
- So `TagNodeT = TagNode` still includes `Tagifiable`.

Narrowing only changes behavior for the rare `Tag[TagifiedNode]` /
`TagList[TagifiedNode]` case (i.e. a post-`.tagify()` reference being
mutated). That case is already covered by a runtime boundary check
inside `TagList.tagify()`, which raises `TypeError` naming the
offending class and slot index. Better diagnostics than a static error
pointing at a single `append` call.

## Trade-off

`TagList[TagifiedNode].append(some_tagifiable)` no longer static-errors.
We accept this and document the trade-off in
`tests/test_types.py::test_TagifiedTagList_append_accepts_Tagifiable`
(read that test's docstring for the full rationale and the conditions
under which we'd reverse this decision).

Pyright currently accepts these signatures cleanly, so no
`# pyright: ignore` comments are needed at the mutation sites. If
some future pyright version starts flagging them as
`reportArgumentType` again, the conventional fix is to silence each
site with `# pyright: ignore[reportArgumentType]` rather than reverse
this decision.

## Related

- `2026-05-18-tagify-returns-tagified.md`
- `tests/test_types.py::test_TagifiedTagList_append_accepts_Tagifiable`

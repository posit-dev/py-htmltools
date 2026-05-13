# Design: Generic `Tag` / `TagList` and a tagified return contract for `.tagify()`

- **Issue:** [posit-dev/py-htmltools#105](https://github.com/posit-dev/py-htmltools/issues/105)
- **Related:** [#7](https://github.com/posit-dev/py-htmltools/issues/7) (motivating bug)
- **Date:** 2026-05-13
- **Status:** Approved (brainstorming)

## Motivation

`Tagifiable.tagify()` is supposed to return a fully-tagified subtree: no
`Tagifiable` objects whose `.tagify()` still needs to be called. Today the
return type is `TagList | Tag | MetadataNode | str | HTML` — none of which
encode the recursive "fully tagified" invariant. As a result, bugs like
[#7](https://github.com/posit-dev/py-htmltools/issues/7) surface only inside
`get_html_string` with a `RuntimeError`, far from the `.tagify()`
implementation that violated the contract.

We want to:

1. Make "tagified" a first-class type so the type checker catches violations.
2. Keep source compatibility for current downstreams (notably Shiny).
3. Raise at the `.tagify()` boundary, not at render time, when the runtime
   invariant is broken.

## Decisions (locked during brainstorming)

| # | Question | Choice |
|---|---|---|
| Q1 | Compat stance | **A.** Source-compatible: PEP 696 `default=TagNode` on the new type parameter so unparameterized `Tag` / `TagList` mean what they do today. |
| Q2 | Runtime behavior in `TagList.tagify()` | **A3.** Validate at the tagify boundary. One-level recursion stays; a post-pass asserts no `Tagifiable` slipped through. |
| Q3 | Mutability of a tagified tree | **A.** Snapshot only. `TagifiedTag` is a post-condition of `.tagify()`, not a permanent runtime invariant. |
| Q4 | Render-time guard in `get_html_string` | **A.** Keep as belt-and-braces (covers mutation-after-tagify, since not all users use type checkers). |
| Q5 | JSXTag scope | **B.** Just tighten the return annotation; leave `JSXTag` non-generic. |
| Q6 | Input methods (`__init__`/`append`/`extend`/`insert`) | **B.** Parameterize via `TagChildOf[ChildT]` so `TagifiedTagList.append(SomeTagifiable())` static-errors. |
| Q7 | Subclass-preserving `Tag.tagify()` signature | **A.** Drop it. `Tag.tagify() -> TagifiedTag`. Runtime still returns the subclass instance; the static type narrows. |

## Architecture

### Type model

```python
# A Tag whose entire subtree is tagified.
TagifiedTag: TypeAlias = "Tag[TagifiedNode]"
# A TagList whose items are all tagified.
TagifiedTagList: TypeAlias = "TagList[TagifiedNode]"

# Slot-item type for a tagified TagList. Excludes TagList (flattening rule:
# a TagList never contains another TagList as a child slot).
TagifiedNode = Union[TagifiedTag, MetadataNode, "ReprHtml", str, HTML]

# Anything .tagify() can return. Includes the top-level TagifiedTagList arm
# (a user's tagify() may legitimately produce a flat list, not just a Tag).
Tagified = Union[TagifiedTagList, TagifiedNode]

# Existing TagNode, factored. Same set as today.
TagNode = Union["Tagifiable", TagifiedNode]

# Generic parameter for Tag / TagList. PEP 696 default keeps unparameterized
# Tag / TagList meaning Tag[TagNode] / TagList[TagNode].
from typing_extensions import TypeVar
ChildT = TypeVar("ChildT", bound=TagNode, default=TagNode)

# Generic version of TagChild (user-input alias) so input methods can be
# parameterized too. TagChild itself stays unchanged for source compat.
TagChildOf = Union[ChildT, "TagList[ChildT]", float, None, Sequence["TagChildOf[ChildT]"]]
```

`TagChild` (the wide user-input alias) stays unchanged in name and meaning so
public call sites like `div("hi", x)` continue to work without churn.

### Class signatures

```python
class TagList(UserList[ChildT]):
    def __init__(self, *args: "TagChildOf[ChildT]") -> None: ...
    def append(self, item: "TagChildOf[ChildT]", *args: "TagChildOf[ChildT]") -> None: ...
    def extend(self, other: Iterable["TagChildOf[ChildT]"]) -> None: ...
    def insert(self, i: SupportsIndex, item: "TagChildOf[ChildT]") -> None: ...
    def tagify(self) -> "TagifiedTagList": ...

class Tag(Generic[ChildT]):
    children: TagList[ChildT]
    def tagify(self) -> "TagifiedTag": ...

class Tagifiable(Protocol):
    def tagify(self) -> "Tagified": ...

# _jsx.py — annotation only, no genericity
class JSXTag:
    def tagify(self) -> "TagifiedTag": ...
```

### `TagList.tagify()` body (A3 boundary check)

The existing one-level recursion is preserved. A post-pass asserts the
invariant before returning, so a `.tagify()` implementation that returned an
un-tagified `TagList` is rejected here instead of later in `get_html_string`.

```python
def tagify(self) -> "TagifiedTagList":
    cp = copy(self)
    for i in reversed(range(len(cp))):
        child = cp[i]
        if isinstance(child, Tagifiable):
            tagified_child = child.tagify()
            if isinstance(tagified_child, TagList):
                cp[i : i + 1] = _tagchilds_to_tagnodes(tagified_child)
            else:
                cp[i] = tagified_child
        elif isinstance(child, MetadataNode):
            ...  # existing handling unchanged

    # A3 post-condition. Tag and TagList are Tagifiable but already tagified;
    # exclude them. Anything else implies a child's .tagify() returned an
    # un-tagified subtree.
    for i, child in enumerate(cp):
        if isinstance(child, Tagifiable) and not isinstance(child, (Tag, TagList)):
            raise TypeError(
                f"Expected a Tagified value, but a child .tagify() returned a "
                f"TagList containing an un-tagified "
                f"{type(child).__name__} at index {i}. "
                f"A .tagify() implementation must recursively tagify its return "
                f"value (consider returning `something.tagify()` instead of "
                f"`something`)."
            )
    return cast("TagifiedTagList", cp)
```

`Tag.tagify()` is unchanged in body — it delegates to
`self.children.tagify()`, so it inherits A3 automatically.

### Render-time guard

The existing `isinstance(child, Tagifiable)` branch in
`TagList.get_html_string` stays as the safety net for mutation-after-tagify.
Only the message is updated:

```python
raise RuntimeError(
    f"Encountered an un-tagified {type(child).__name__} at render time. "
    "This usually means the tag tree was mutated to add a Tagifiable "
    "object after .tagify() was called. Call .tagify() again before "
    "rendering."
)
```

## Migration impact

- **htmltools internal.** All existing annotations using `Tag` / `TagList`
  keep working unchanged (default `ChildT = TagNode`). The changes that
  carry meaning:
  - `Tagifiable.tagify()` return type narrows to `Tagified`.
  - `TagList.tagify()` / `Tag.tagify()` / `JSXTag.tagify()` return types
    narrow to `TagifiedTagList` / `TagifiedTag` / `TagifiedTag`.
  - `Tag.tagify()` loses its `TagT`-bound subclass-preserving signature
    (Q7).
- **Downstreams (Shiny, etc.).** Type-only impact. Custom `.tagify()`
  implementations annotated `-> TagList` or `-> Tag` will no longer satisfy
  the `Tagifiable` protocol — those aliases mean `TagList[TagNode]` /
  `Tag[TagNode]`, which are not assignable to `TagifiedTagList` /
  `TagifiedTag`. This is the *useful* breakage: it surfaces real #7-style
  bugs at type-check time. Fix recipe in `NEWS.md`: annotate the return as
  `TagifiedTagList` / `TagifiedTag`, or `Tagified`, or omit the annotation.
- **Dependency bump.** `typing_extensions>=4.7.0` for PEP 696
  `default=` support (already a dependency at `>=3.10.0.0`; current floor
  is too low for `TypeVar(default=...)`).
- **Runtime breakage.** None for code that is already correct. Code with
  a buggy `.tagify()` returning un-tagified content (issue #7) starts
  raising at `TagList.tagify()` time instead of at render time.

## Testing

### Runtime (pytest, `tests/`)

- The #7 example raises `TypeError` from `TagList.tagify()` with a message
  naming the offending class and index. Replaces the existing render-time
  error path for this case.
- Idempotence: `div(...).tagify().tagify()` equals the first `.tagify()`
  result.
- Mutation-after-tagify: append a `Tagifiable` onto a tagified
  `Tag.children`, then render — still raises `RuntimeError` from
  `get_html_string` with the updated message.
- Existing render tests pass unchanged for well-formed `.tagify()`
  implementations.

### Static types

Pyright is already run in CI. Add `tests/test_types.py` using `assert_type`
from `typing_extensions` for the cases below:

- `assert_type(div("hi").tagify(), TagifiedTag)`
- `assert_type(TagList("hi").tagify(), TagifiedTagList)`
- A user class with `def tagify(self) -> TagList: ...` is **not** assignable
  to `Tagifiable` (negative test gated with `# type: ignore[assignment]`).
- `tl: TagifiedTagList; tl.append(some_tagifiable)` is a static error
  (negative test).
- Default behavior unchanged: `TagList("hi").append(some_tagifiable)` still
  type-checks (because the default `ChildT = TagNode` includes
  `Tagifiable`).

## Out of scope

- Making `JSXTag` itself generic (Q5-C).
- Freezing `Tag.children` after `.tagify()` (Q3-C).
- Auto-recursing `TagList.tagify()` to a fixed point so #7's example
  silently works (Q2-A2). We chose to error at the boundary instead, so
  buggy `.tagify()` implementations are caught.
- Subclass-preserving `Tag.tagify()` signature (Q7-B/C). Runtime preserves
  the subclass instance; only the static type narrows.

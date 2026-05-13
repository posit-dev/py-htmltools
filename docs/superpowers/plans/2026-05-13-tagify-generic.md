# Tagify Generic Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce `TagifiedTag` / `TagifiedTagList` / `TagifiedNode` / `Tagified` aliases backed by a generic `ChildT` parameter on `Tag` / `TagList`, plus a runtime A3 boundary check in `TagList.tagify()` so #7-style bugs error where they originate.

**Architecture:** `Tag` and `TagList` become `Generic[ChildT]`. `ChildT` defaults to `TagNode` (PEP 696) so bare `Tag` / `TagList` keep today's meaning — no source break. `TagChild` itself becomes a generic `TypeAliasType` so input methods on `TagList[TagifiedNode]` static-error when handed an un-tagified value. `TagList.tagify()` gains a post-pass that raises `TypeError` if any `Tagifiable` slipped through, replacing the late render-time error path. JSXTag stays non-generic; only its `.tagify()` annotation tightens.

**Tech Stack:** Python 3.10+, `typing_extensions >= 4.7.0` (for `TypeVar(default=...)` and `TypeAliasType`), pyright (strict on `htmltools/`), pytest, syrupy.

**Spec:** [`docs/superpowers/specs/2026-05-13-tagify-generic-design.md`](../specs/2026-05-13-tagify-generic-design.md)

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `pyproject.toml` | dependency declarations | bump `typing_extensions` floor |
| `htmltools/_core.py` | core type aliases, `Tag`, `TagList`, `Tagifiable`, render guard | most of the work |
| `htmltools/_jsx.py` | `JSXTag` | tighten `.tagify()` annotation only |
| `htmltools/__init__.py` | public exports | export `TagifiedTag`, `TagifiedTagList`, `TagifiedNode`, `Tagified` |
| `tests/test_tagify.py` (new) | runtime tests for tagify behavior | A3 + idempotence + mutation-after-tagify |
| `tests/test_types.py` (new) | static-type assertions | `assert_type` cases |
| `CHANGELOG.md` | release notes | add "0.7.0 (unreleased)" section |

The bulk of changes are confined to `_core.py`. Each phase commits independently.

---

## Phase 1 — Runtime: A3 boundary check + guard message

### Task 1: Runtime test — `TagList.tagify()` raises on un-tagified grand-children

**Files:**
- Create: `tests/test_tagify.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tagify.py
import pytest

from htmltools import TagList, Tagifiable, div


class _ReturnsTagifiable:
    """A buggy Tagifiable: returns a TagList containing an un-tagified Tagifiable."""

    def tagify(self) -> "TagList":
        return TagList(_NestedTagifiable())


class _NestedTagifiable:
    """A Tagifiable whose .tagify() returns a plain string."""

    def tagify(self) -> str:
        return "bar"


def test_taglist_tagify_raises_on_untagified_grandchild() -> None:
    # The buggy wrapper returns a TagList with a still-Tagifiable child;
    # TagList.tagify() must raise at the boundary, naming the offending type.
    tl = TagList(_ReturnsTagifiable())
    with pytest.raises(TypeError, match="_NestedTagifiable"):
        tl.tagify()


def test_tag_tagify_raises_on_untagified_grandchild() -> None:
    # Same scenario, but via Tag.tagify(), which delegates to children.tagify().
    with pytest.raises(TypeError, match="_NestedTagifiable"):
        div(_ReturnsTagifiable()).tagify()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tagify.py::test_taglist_tagify_raises_on_untagified_grandchild -v`

Expected: **FAIL** — today the un-tagified nested object survives through `TagList.tagify()` and the error (if any) surfaces later in `get_html_string` as `RuntimeError`, not `TypeError` from `tagify`.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_tagify.py
git commit -m "test: failing test for TagList.tagify A3 boundary check (#105)"
```

---

### Task 2: Implement A3 boundary check in `TagList.tagify()`

**Files:**
- Modify: `htmltools/_core.py` (the `TagList.tagify` method, currently at lines 323–345)

- [ ] **Step 1: Replace `TagList.tagify` body with the A3 post-pass**

Find the existing method:

```python
    def tagify(self) -> "TagList":
        """
        Convert any tagifiable children to Tag/TagList objects.
        """

        cp = copy(self)

        # Iterate backwards because if we hit a Tagifiable object, it may be replaced
        # with 0, 1, or more items (if it returns TagList).
        for i in reversed(range(len(cp))):
            child = cp[i]

            if isinstance(child, Tagifiable):
                tagified_child = child.tagify()
                if isinstance(tagified_child, TagList):
                    # If the Tagifiable object returned a TagList, flatten it into this
                    # one.
                    cp[i : i + 1] = _tagchilds_to_tagnodes(tagified_child)
                else:
                    cp[i] = tagified_child

            elif isinstance(child, MetadataNode):
                ...
```

Append the A3 post-pass before `return cp`. The full new method body:

```python
    def tagify(self) -> "TagList":
        """
        Convert any tagifiable children to Tag/TagList objects.

        Raises
        ------
        TypeError
            If a child's `.tagify()` returned a `TagList` containing an
            un-tagified `Tagifiable` object — i.e. the recursion was not done
            all the way down. The error names the offending class and slot
            index so the broken `.tagify()` is easy to find.
        """

        cp = copy(self)

        # Iterate backwards because if we hit a Tagifiable object, it may be replaced
        # with 0, 1, or more items (if it returns TagList).
        for i in reversed(range(len(cp))):
            child = cp[i]

            if isinstance(child, Tagifiable):
                tagified_child = child.tagify()
                if isinstance(tagified_child, TagList):
                    # If the Tagifiable object returned a TagList, flatten it into this
                    # one.
                    cp[i : i + 1] = _tagchilds_to_tagnodes(tagified_child)
                else:
                    cp[i] = tagified_child

            elif isinstance(child, MetadataNode):
                # Existing handling unchanged — leave the existing body here.
                ...  # KEEP THE EXISTING METADATA-NODE BRANCH AS-IS

        # A3 post-condition: after the recursion, no bare Tagifiable may remain.
        # Tag and TagList are themselves Tagifiable but already-tagified shapes,
        # so they are excluded from the check.
        for i, child in enumerate(cp):
            if isinstance(child, Tagifiable) and not isinstance(child, (Tag, TagList)):
                raise TypeError(
                    "Expected a fully tagified value, but a child .tagify() "
                    "returned a TagList containing an un-tagified "
                    f"{type(child).__name__} at index {i}. "
                    "A .tagify() implementation must recursively tagify its "
                    "return value (consider returning `something.tagify()` "
                    "instead of `something`)."
                )

        return cp
```

When editing: keep the existing `elif isinstance(child, MetadataNode):` branch body intact — only the post-pass loop and the docstring are new.

- [ ] **Step 2: Run the new tests**

Run: `pytest tests/test_tagify.py -v`

Expected: **PASS** for both `test_taglist_tagify_raises_on_untagified_grandchild` and `test_tag_tagify_raises_on_untagified_grandchild`.

- [ ] **Step 3: Run the existing test suite to confirm no regressions**

Run: `pytest tests/ -v`

Expected: **PASS** — all existing tests still pass.

- [ ] **Step 4: Commit**

```bash
git add htmltools/_core.py
git commit -m "feat: raise TypeError at TagList.tagify boundary on un-tagified content (#105)"
```

---

### Task 3: Idempotence test

**Files:**
- Modify: `tests/test_tagify.py`

- [ ] **Step 1: Add the idempotence test**

Append to `tests/test_tagify.py`:

```python
def test_tagify_is_idempotent() -> None:
    # .tagify() applied twice must produce the same HTML as once.
    original = div("hello", span("world"))
    once = original.tagify()
    twice = once.tagify()
    assert once.get_html_string() == twice.get_html_string()
```

You'll need to add `span` to the import line at the top of the file:

```python
from htmltools import TagList, Tagifiable, div, span
```

- [ ] **Step 2: Run the test**

Run: `pytest tests/test_tagify.py::test_tagify_is_idempotent -v`

Expected: **PASS**.

- [ ] **Step 3: Commit**

```bash
git add tests/test_tagify.py
git commit -m "test: idempotence of .tagify() (#105)"
```

---

### Task 4: Update render-time guard message

**Files:**
- Modify: `htmltools/_core.py` (the `Tagifiable` branch of `TagList.get_html_string`, currently lines 444–447)

- [ ] **Step 1: Update the `RuntimeError` message**

Find:

```python
            elif isinstance(child, Tagifiable):
                raise RuntimeError(
                    "Encountered a non-tagified object. x.tagify() must be called before x.render()"
                )
```

Replace with:

```python
            elif isinstance(child, Tagifiable):
                raise RuntimeError(
                    f"Encountered an un-tagified {type(child).__name__} at render time. "
                    "This usually means the tag tree was mutated to add a "
                    "Tagifiable object after .tagify() was called. Call "
                    ".tagify() again before rendering."
                )
```

- [ ] **Step 2: Run the test suite**

Run: `pytest tests/ -v`

Expected: **PASS** — no test depended on the old message text.

- [ ] **Step 3: Commit**

```bash
git add htmltools/_core.py
git commit -m "feat: clearer render-time guard message for un-tagified content (#105)"
```

---

### Task 5: Mutation-after-tagify test

**Files:**
- Modify: `tests/test_tagify.py`

- [ ] **Step 1: Add the test**

Append:

```python
def test_render_guard_catches_mutation_after_tagify() -> None:
    # The static guarantee is a snapshot at .tagify() time; if a Tagifiable
    # is appended afterwards, the render-time guard must catch it.
    tagified = div("hello").tagify()
    tagified.children.append(_NestedTagifiable())
    with pytest.raises(RuntimeError, match="_NestedTagifiable"):
        tagified.get_html_string()
```

- [ ] **Step 2: Run the test**

Run: `pytest tests/test_tagify.py::test_render_guard_catches_mutation_after_tagify -v`

Expected: **PASS** — the render guard catches the post-tagify mutation.

- [ ] **Step 3: Commit**

```bash
git add tests/test_tagify.py
git commit -m "test: render-time guard catches mutation after .tagify() (#105)"
```

---

## Phase 2 — Type system: generic `Tag` / `TagList` and tagified aliases

### Task 6: Bump `typing_extensions` floor

**Files:**
- Modify: `pyproject.toml` (line 28)

- [ ] **Step 1: Update the dependency**

Find:

```toml
dependencies = ["typing-extensions>=3.10.0.0", "packaging>=20.9"]
```

Replace with:

```toml
dependencies = ["typing-extensions>=4.7.0", "packaging>=20.9"]
```

`4.7.0` is the minimum version that supports both `TypeVar(default=...)` (PEP 696 backport) and `TypeAliasType` with `type_params=`.

- [ ] **Step 2: Reinstall in dev env to confirm**

Run: `pip install -e .`

Expected: install succeeds, `typing_extensions>=4.7.0` is satisfied.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "build: require typing_extensions>=4.7.0 for PEP 696 defaults (#105)"
```

---

### Task 7: Add tagified type aliases and generic `TagChild`

**Files:**
- Modify: `htmltools/_core.py` (imports near line 17, and the `TagNode`/`TagChild` block at lines 112–140)

- [ ] **Step 1: Update imports**

Find the existing imports near line 17 and the conditional `typing_extensions` imports near line 37–42. Ensure these names come from `typing_extensions` (which supports the `default=` and `TypeAliasType` features uniformly on all supported Pythons):

Add at the top of the conditional import block (around line 37):

```python
from typing_extensions import TypeAliasType
```

And update the `TypeVar` import at line 25 — remove `TypeVar` from the `typing` import line and add to a `typing_extensions` import. The full block becomes:

```python
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
    overload,
)

# ...existing version-conditional imports for Never/NotRequired/TypedDict/TypeIs...

from typing_extensions import TypeAliasType, TypeVar
```

(`typing_extensions.TypeVar` is a drop-in replacement for `typing.TypeVar` and adds `default=` support across all Python versions we ship for.)

- [ ] **Step 2: Add tagified type aliases and `ChildT` TypeVar**

Locate the existing `TagNode` definition near line 112 and replace the entire `TagNode` / `TagChild` / `TagChildArg` / `TagAttrArg` / `TagChildT` block with the following. The replacement keeps the public names (`TagNode`, `TagChild`, `TagChildT`, `TagChildArg`, `TagAttrArg`) intact so external users do not see a source break — `TagChild` becomes generic with a default so bare uses are unchanged.

Find:

```python
# NOTE: If this type is updated, please update `is_tag_node()`
TagNode = Union[
    "Tagifiable",
    # "Tag", # Tag is Tagifiable, do not include here
    # "TagList" is Tagifiable, so it is included in practice.
    #   But in reality it should be excluded because a TagList cannot contain a TagList.
    MetadataNode,
    "ReprHtml",
    str,
    "HTML",
]
"""
Types of objects that can be a node in a `Tag` tree. Equivalently, these are the valid
elements of a `TagList`. Note that this type represents the internal structure of items
in a `TagList`; the user-facing type is `TagChild`.
"""

# NOTE: If this type is updated, please update `is_tag_child()`
TagChild = Union[
    TagNode,
    "TagList",
    float,
    None,
    Sequence["TagChild"],
]
"""
Types of objects that can be passed as children to Tag functions like `div()`. The `Tag`
functions and the `TagList()` constructor can accept these as unnamed arguments; they
will be flattened and normalized to `TagNode` objects.
"""


# These two types existed in htmltools 0.14.0 and earlier. They are here so that
# existing versions of Shiny will be able to load, but users of those existing packages
# will see type errors, which should encourage them to upgrade Shiny.
TagChildArg = Never
TagAttrArg = Never


# # No use yet, so keeping code commented for now
# TagNodeT = TypeVar("TagNodeT", bound=TagNode)
# """
# Type variable for `TagNode`.
# """

TagChildT = TypeVar("TagChildT", bound=TagChild)
"""
Type variable for `TagChild`.
"""
```

Replace with:

```python
# -----------------------------------------------------------------------------
# Tagified shape aliases
# -----------------------------------------------------------------------------
# A node that has already been fully tagified: no Tagifiable objects whose
# .tagify() still needs to be called. Recursive — a tagified Tag's children
# are themselves tagified. TagList is NOT a member because TagList children
# are flattened (a TagList never appears as a child slot of another TagList).
TagifiedNode = Union["Tag[TagifiedNode]", MetadataNode, "ReprHtml", str, "HTML"]
"""
A fully-tagified child-slot type. Members never include an un-resolved
`Tagifiable`; calling `.tagify()` on a node tree returns a structure whose
slot items are all `TagifiedNode`.
"""

TagifiedTag = TypeAliasType("TagifiedTag", "Tag[TagifiedNode]")
"""
A `Tag` whose entire subtree has been tagified. This is the return type of
`Tag.tagify()` and `JSXTag.tagify()`.
"""

TagifiedTagList = TypeAliasType("TagifiedTagList", "TagList[TagifiedNode]")
"""
A `TagList` whose items are all tagified. This is the return type of
`TagList.tagify()`.
"""

Tagified = Union[TagifiedTagList, TagifiedNode]
"""
Anything `.tagify()` is permitted to return: either a top-level
`TagifiedTagList`, or one of the `TagifiedNode` shapes (which themselves
include `TagifiedTag`).
"""


# -----------------------------------------------------------------------------
# TagNode / TagChild (generic) and the ChildT TypeVar
# -----------------------------------------------------------------------------
# NOTE: If this type is updated, please update `is_tag_node()`
TagNode = Union["Tagifiable", TagifiedNode]
"""
Types of objects that can be a node in a `Tag` tree. Equivalently, these are
the valid elements of a `TagList`. Note that this type represents the
internal structure of items in a `TagList`; the user-facing type is
`TagChild`.
"""

ChildT = TypeVar("ChildT", bound=TagNode, default=TagNode)
"""
Type parameter for `Tag` and `TagList`. Defaults to `TagNode`, so bare
`Tag` / `TagList` keep their pre-#105 meaning.
"""

# NOTE: If this alias is updated, please update `is_tag_child()`
# `TagChild` is itself generic: bare `TagChild` means `TagChild[TagNode]`
# (today's wide alias); `TagChild[TagifiedNode]` is the tagified-input alias
# used by `TagList[TagifiedNode]`'s mutation methods.
TagChild = TypeAliasType(
    "TagChild",
    Union[ChildT, "TagList[ChildT]", float, None, Sequence["TagChild[ChildT]"]],
    type_params=(ChildT,),
)
"""
Types of objects that can be passed as children to Tag functions like
`div()`. The `Tag` functions and the `TagList()` constructor can accept
these as unnamed arguments; they will be flattened and normalized to
`TagNode` objects.
"""


# These two types existed in htmltools 0.14.0 and earlier. They are here so
# that existing versions of Shiny will be able to load, but users of those
# existing packages will see type errors, which should encourage them to
# upgrade Shiny.
TagChildArg = Never
TagAttrArg = Never


TagChildT = TypeVar("TagChildT", bound="TagChild")
"""
Type variable for `TagChild`.
"""
```

Notes for the engineer:

- The `TagChildT` TypeVar (used by `consolidate_attrs`) is preserved with the same name. Its `bound=` argument now points to the generic `TagChild` (unparameterized → defaults to `TagChild[TagNode]` — same set as today).
- Forward references in the recursive `TagifiedNode` and `TagChild` definitions are handled by string-quoted annotations.
- Both `TagifiedTag` and `TagifiedTagList` use `TypeAliasType` so they appear as proper alias names in error messages (e.g. pyright displays `TagifiedTag` instead of `Tag[TagifiedNode]`).

- [ ] **Step 3: Type-check**

Run: `pyright htmltools/_core.py`

Expected: no new errors. (There may be pre-existing errors unrelated to this change — note them but do not fix as part of this task.)

- [ ] **Step 4: Run the test suite**

Run: `pytest tests/ -v`

Expected: **PASS** — runtime behavior is unchanged.

- [ ] **Step 5: Commit**

```bash
git add htmltools/_core.py
git commit -m "feat: add TagifiedNode/TagifiedTag/TagifiedTagList/Tagified aliases (#105)"
```

---

### Task 8: Make `TagList` generic in `ChildT`

**Files:**
- Modify: `htmltools/_core.py` (the `TagList` class definition, starting at line 257)

- [ ] **Step 1: Parameterize the class and input methods**

Find:

```python
class TagList(UserList[TagNode]):
    """
    Create an HTML tag list (i.e., a fragment of HTML)
    ...
    """

    def _should_not_expand(self, x: object) -> TypeIs[str]:
        ...

    def __init__(self, *args: TagChild) -> None:
        super().__init__(_tagchilds_to_tagnodes(args))

    def extend(self, other: Iterable[TagChild]) -> None:
        ...
        super().extend(_tagchilds_to_tagnodes(other))

    def append(self, item: TagChild, *args: TagChild) -> None:
        ...
        self.extend([item, *args])

    def insert(self, i: SupportsIndex, item: TagChild) -> None:
        ...
        self[i:i] = _tagchilds_to_tagnodes([item])

    def __add__(self, item: Iterable[TagChild]) -> TagList:
        ...

    def __radd__(self, item: Iterable[TagChild]) -> TagList:
        ...
```

Replace with:

```python
class TagList(UserList[ChildT]):
    """
    Create an HTML tag list (i.e., a fragment of HTML)
    ...
    """

    def _should_not_expand(self, x: object) -> TypeIs[str]:
        ...  # keep existing body

    def __init__(self, *args: "TagChild[ChildT]") -> None:
        super().__init__(_tagchilds_to_tagnodes(args))

    def extend(self, other: Iterable["TagChild[ChildT]"]) -> None:
        ...  # keep existing body
        super().extend(_tagchilds_to_tagnodes(other))

    def append(self, item: "TagChild[ChildT]", *args: "TagChild[ChildT]") -> None:
        ...  # keep existing body
        self.extend([item, *args])

    def insert(self, i: SupportsIndex, item: "TagChild[ChildT]") -> None:
        ...  # keep existing body
        self[i:i] = _tagchilds_to_tagnodes([item])

    def __add__(self, item: Iterable["TagChild[ChildT]"]) -> "TagList[ChildT]":
        ...  # keep existing body

    def __radd__(self, item: Iterable["TagChild[ChildT]"]) -> "TagList[ChildT]":
        ...  # keep existing body
```

(Bodies of each method stay exactly as they are today — only the annotations change.)

- [ ] **Step 2: Tighten `TagList.tagify()` return type**

Find:

```python
    def tagify(self) -> "TagList":
        """
        Convert any tagifiable children to Tag/TagList objects.
        ...
        """
```

Replace with:

```python
    def tagify(self) -> "TagifiedTagList":
        """
        Convert any tagifiable children to Tag/TagList objects.
        ...
        """
```

At the `return cp` line, replace with:

```python
        return cast("TagifiedTagList", cp)
```

(The body of `tagify` was already updated in Task 2; this is just the signature and the `cast` on return.)

- [ ] **Step 3: Type-check**

Run: `pyright htmltools/_core.py`

Expected: no new errors.

- [ ] **Step 4: Run tests**

Run: `pytest tests/ -v`

Expected: **PASS**.

- [ ] **Step 5: Commit**

```bash
git add htmltools/_core.py
git commit -m "feat: make TagList generic in ChildT (#105)"
```

---

### Task 9: Make `Tag` generic in `ChildT`

**Files:**
- Modify: `htmltools/_core.py` (the `Tag` class definition, starting at line 592, and `Tag.tagify` at line 844)

- [ ] **Step 1: Parameterize the class declaration**

Find:

```python
class Tag:
    """
    The HTML tag class.
    ...
    """
```

Replace with:

```python
class Tag(Generic[ChildT]):
    """
    The HTML tag class.
    ...
    """
```

If `Generic` is not imported, add it to the `typing` import block at the top of the file:

```python
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    ...
)
```

- [ ] **Step 2: Type the `children` attribute**

Find the class-level or `__init__`-level reference to `self.children`. In `__init__` (around line 679):

```python
        kids = [x for x in args if not isinstance(x, dict)]
        self.children = TagList(*kids)
```

Add an explicit class-level annotation just inside the class body (right after the docstring):

```python
    children: "TagList[ChildT]"
```

(This is a class-level type annotation only; no runtime change.)

- [ ] **Step 3: Tighten `Tag.tagify()` signature**

Find at line 844:

```python
    def tagify(self: TagT) -> TagT:
        """
        Convert any tagifiable children to Tag/TagList objects.
        """

        cp = copy(self)
        cp.children = cp.children.tagify()
        return cp
```

Replace with:

```python
    def tagify(self) -> "TagifiedTag":
        """
        Convert any tagifiable children to Tag/TagList objects.
        """

        cp = copy(self)
        cp.children = cp.children.tagify()
        return cast("TagifiedTag", cp)
```

This drops the subclass-preserving `TagT` signature in favor of the narrowed `TagifiedTag`. Runtime behavior is unchanged (`copy(self)` still returns the same subclass instance); only the static type narrows. See spec Q7-A.

The other methods on `Tag` that use `TagT` — `__copy__` (line 683), `add_class` (line 730), `remove_class` (line 753), `add_style` (line 810) — stay as-is. Q7-A's loss-of-subclass-info is scoped narrowly to `.tagify()`; these other methods continue to return the caller's subclass.

- [ ] **Step 4: Type-check**

Run: `pyright htmltools/_core.py`

Expected: no new errors.

- [ ] **Step 5: Run tests**

Run: `pytest tests/ -v`

Expected: **PASS**.

- [ ] **Step 6: Commit**

```bash
git add htmltools/_core.py
git commit -m "feat: make Tag generic in ChildT (#105)"
```

---

### Task 10: Tighten `Tagifiable` protocol return type

**Files:**
- Modify: `htmltools/_core.py` (lines 221–228)

- [ ] **Step 1: Update the protocol**

Find:

```python
@runtime_checkable
class Tagifiable(Protocol):
    """
    Objects with `tagify()` methods are considered `Tagifiable`. Note that an object
    returns a `TagList`, the children of the `TagList` must also be tagified.
    """

    def tagify(self) -> "TagList | Tag | MetadataNode | str | HTML": ...
```

Replace with:

```python
@runtime_checkable
class Tagifiable(Protocol):
    """
    Objects with `tagify()` methods are considered `Tagifiable`. The return
    value must be `Tagified` — i.e. fully tagified all the way down. See
    `TagifiedNode` / `TagifiedTag` / `TagifiedTagList`.
    """

    def tagify(self) -> "Tagified": ...
```

- [ ] **Step 2: Type-check**

Run: `pyright htmltools/_core.py`

Expected: no new errors in `_core.py`. There may be downstream type errors in `_jsx.py` for `JSXTag` — leave those for Task 11.

- [ ] **Step 3: Run tests**

Run: `pytest tests/ -v`

Expected: **PASS** — `Tagifiable` is `@runtime_checkable`, and `isinstance` uses structural matching on `.tagify` presence only, not its signature.

- [ ] **Step 4: Commit**

```bash
git add htmltools/_core.py
git commit -m "feat: Tagifiable.tagify() returns Tagified (#105)"
```

---

### Task 11: Tighten `JSXTag.tagify()` annotation

**Files:**
- Modify: `htmltools/_jsx.py` (line 113)

- [ ] **Step 1: Update the imports and the return annotation**

At the top of `_jsx.py`, ensure `TagifiedTag` is imported. Find the existing import from `._core`:

```python
from ._core import (
    ...
    Tagifiable,
    ...
)
```

Add `TagifiedTag` to that import list:

```python
from ._core import (
    ...
    Tagifiable,
    TagifiedTag,
    ...
)
```

Find at line 113:

```python
    def tagify(self) -> Tag:
```

Replace with:

```python
    def tagify(self) -> TagifiedTag:
```

At the `return Tag(...)` near line 164, wrap in a cast:

```python
        return cast("TagifiedTag", Tag(
            "script",
            ...
            *metadata_nodes,
        ))
```

(`cast` should already be imported in `_jsx.py`; if not, add it from `typing`.)

- [ ] **Step 2: Type-check**

Run: `pyright htmltools/_jsx.py`

Expected: no new errors.

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_jsx_tags.py -v`

Expected: **PASS**.

- [ ] **Step 4: Commit**

```bash
git add htmltools/_jsx.py
git commit -m "feat: JSXTag.tagify() returns TagifiedTag (#105)"
```

---

## Phase 3 — Exports, type tests, changelog

### Task 12: Export new aliases from `__init__.py`

**Files:**
- Modify: `htmltools/__init__.py`

- [ ] **Step 1: Update the imports from `_core`**

Find:

```python
from ._core import (
    HTML,
    HTMLDependency,
    HTMLDocument,
    HTMLTextDocument,
    MetadataNode,
    RenderedHTML,
    ReprHtml,
    Tag,
    TagAttrs,
    TagAttrValue,
    TagChild,
    TagFunction,
    Tagifiable,
    TagList,
    TagNode,
    consolidate_attrs,
    head_content,
    is_tag_child,
    is_tag_node,
    wrap_displayhook_handler,
)
```

Add the four new aliases:

```python
from ._core import (
    HTML,
    HTMLDependency,
    HTMLDocument,
    HTMLTextDocument,
    MetadataNode,
    RenderedHTML,
    ReprHtml,
    Tag,
    TagAttrs,
    TagAttrValue,
    TagChild,
    TagFunction,
    Tagified,
    Tagifiable,
    TagifiedNode,
    TagifiedTag,
    TagifiedTagList,
    TagList,
    TagNode,
    consolidate_attrs,
    head_content,
    is_tag_child,
    is_tag_node,
    wrap_displayhook_handler,
)
```

- [ ] **Step 2: Update `__all__`**

Find the `__all__` tuple (line 49). Add `"Tagified"`, `"TagifiedNode"`, `"TagifiedTag"`, `"TagifiedTagList"` in alphabetical position. The relevant slice becomes:

```python
    "Tag",
    "TagAttrs",
    "TagAttrValue",
    "TagChild",
    "TagFunction",
    "Tagified",
    "Tagifiable",
    "TagifiedNode",
    "TagifiedTag",
    "TagifiedTagList",
    "TagList",
    "TagNode",
```

- [ ] **Step 3: Update the parent `_core.__all__`**

In `htmltools/_core.py`, the `__all__` tuple at line 56–76 needs the same four names. Find:

```python
__all__ = (
    "TagList",
    "Tag",
    ...
    "TagFunction",
    "Tagifiable",
    ...
)
```

Add `"Tagified"`, `"TagifiedNode"`, `"TagifiedTag"`, `"TagifiedTagList"` (alphabetical order if you want to match the rest, otherwise grouped near `"Tagifiable"`).

- [ ] **Step 4: Smoke-test imports**

Run: `python -c "from htmltools import TagifiedTag, TagifiedTagList, TagifiedNode, Tagified; print('ok')"`

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add htmltools/__init__.py htmltools/_core.py
git commit -m "feat: export Tagified / TagifiedNode / TagifiedTag / TagifiedTagList (#105)"
```

---

### Task 13: Static-type assertions in `tests/test_types.py`

**Files:**
- Create: `tests/test_types.py`

- [ ] **Step 1: Write the file**

Create `tests/test_types.py`:

```python
"""
Static-type assertions for the tagified type contract.

This module is exercised by pyright (in CI and via `pyright tests/`). It does
not contain runtime assertions; the `assert_type` calls are no-ops at runtime
but produce type errors if the inferred types are wrong.

Lines marked `# pyright: ignore[<rule>]` are *intentional* — they assert that
pyright would refuse the indicated assignment.
"""

from __future__ import annotations

from typing_extensions import assert_type

from htmltools import (
    Tag,
    Tagified,
    Tagifiable,
    TagifiedTag,
    TagifiedTagList,
    TagList,
    div,
)


def test_tag_tagify_returns_TagifiedTag() -> None:
    assert_type(div("hi").tagify(), TagifiedTag)


def test_taglist_tagify_returns_TagifiedTagList() -> None:
    assert_type(TagList("hi").tagify(), TagifiedTagList)


def test_bare_TagList_is_not_assignable_to_TagifiedTagList() -> None:
    tl: TagList = TagList("hi")
    # A bare TagList means TagList[TagNode], which may still contain Tagifiables.
    # It must NOT be assignable to TagifiedTagList without explicit narrowing.
    narrowed: TagifiedTagList = tl  # pyright: ignore[reportAssignmentType]


def test_TagifiedTagList_append_rejects_Tagifiable() -> None:
    class _BadTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    # _BadTagifiable is a Tagifiable; appending it to a TagifiedTagList must
    # fail static type checking, since TagList[TagifiedNode]'s input type is
    # TagChild[TagifiedNode] which excludes Tagifiable.
    tl.append(_BadTagifiable())  # pyright: ignore[reportArgumentType]


def test_bare_TagList_append_accepts_Tagifiable() -> None:
    class _OkTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    # Default behavior must be unchanged: bare TagList accepts any TagChild,
    # which includes Tagifiable.
    tl: TagList = TagList()
    tl.append(_OkTagifiable())


def test_user_tagify_returning_bare_TagList_violates_Tagifiable() -> None:
    class _Bad:
        # Bare TagList annotation means TagList[TagNode], which is wider than
        # TagifiedTagList. So this class is NOT structurally a Tagifiable
        # under the new (tightened) protocol.
        def tagify(self) -> TagList:
            return TagList("x")

    not_a_tagifiable: Tagifiable = _Bad()  # pyright: ignore[reportAssignmentType]


def test_user_tagify_returning_TagifiedTagList_is_Tagifiable() -> None:
    class _Good:
        def tagify(self) -> TagifiedTagList:
            return TagList("x").tagify()

    ok: Tagifiable = _Good()
```

- [ ] **Step 2: Run pyright on the new file**

Run: `pyright tests/test_types.py`

Expected: **0 errors, 0 warnings** — all the `pyright: ignore` lines are validated as actually suppressing real errors. If a `pyright: ignore` line reports `Unused "pyright: ignore" comment`, the type system isn't catching what we expect — that's a real failure.

- [ ] **Step 3: Run the file under pytest to confirm no runtime issues**

Run: `pytest tests/test_types.py -v`

Expected: **PASS** (all tests are runtime no-ops that exercise import paths).

- [ ] **Step 4: Commit**

```bash
git add tests/test_types.py
git commit -m "test: static-type assertions for Tagified types (#105)"
```

---

### Task 14: Update `CHANGELOG.md`

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add an "unreleased" section**

Insert immediately after the top header block (after the `## [0.6.1]` section is the last release section; the unreleased section goes above it):

```markdown
## [0.7.0] - unreleased

### Breaking changes

* `Tagifiable.tagify()` now returns `Tagified`, a tighter type covering
  `TagifiedTag` / `TagifiedTagList` / `TagifiedNode`. Custom `.tagify()`
  implementations annotated with bare `TagList` or `Tag` return types will
  fail static type checking; update them to `TagifiedTagList` /
  `TagifiedTag` / `Tagified` (or omit the return annotation). Runtime
  behavior of correct `.tagify()` implementations is unchanged. (#105)

* `Tag.tagify()` now statically returns `TagifiedTag` instead of the
  caller's `Tag` subclass. Code relying on the subclass-preserving
  signature should `cast` the result. (#105)

* `TagList.tagify()` raises `TypeError` at the boundary when a child's
  `.tagify()` returned an un-tagified `TagList`, replacing the prior
  render-time `RuntimeError` for that case. Buggy `.tagify()` implementations
  now surface at the source rather than at render time. (#7, #105)

### New features

* `Tag` and `TagList` are now generic in their child type (`ChildT`,
  defaulting to `TagNode`). `TagList[TagifiedNode]`'s mutation methods
  (`__init__` / `append` / `extend` / `insert`) static-error when handed
  a `Tagifiable` argument. Bare `Tag` / `TagList` retain today's meaning.
  (#105)

* Added type aliases `Tagified`, `TagifiedNode`, `TagifiedTag`,
  `TagifiedTagList`. (#105)

### Dependencies

* Bumped `typing_extensions` floor to `>=4.7.0` for PEP 696 `default=`
  support on `TypeVar` and `TypeAliasType` with `type_params=`.
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: changelog entry for tagified type system (#105)"
```

---

### Task 15: Final verification

**Files:**
- (no edits — verification only)

- [ ] **Step 1: Run the full test suite**

Run: `pytest tests/ -v`

Expected: **PASS** for every test.

- [ ] **Step 2: Run pyright on the whole project**

Run: `pyright`

Expected: **0 errors, 0 warnings** in `htmltools/` and `tests/test_types.py`. There may be pre-existing warnings in `examples/` or elsewhere — those are out of scope. Compare against a `pyright` run from before the changes to confirm no regressions.

- [ ] **Step 3: Smoke-test the original issue #7 example**

Run:

```bash
python -c "
from htmltools import TagList, div

class Foo:
    def tagify(self):
        return TagList('foo')

# This was the original #7 example. After our changes, the simple variant
# still works because the flatten-on-tagify pass resolves the TagList's
# string content correctly.
print(div(Foo()).tagify().get_html_string())
"
```

Expected output: `<div>foo</div>` — the simple #7 case now succeeds end-to-end (the type system flags it statically because `def tagify(self) -> TagList` is too wide for `Tagifiable`, but the runtime handles it correctly via the flatten pass).

- [ ] **Step 4: Verify the nested-buggy variant errors at the boundary**

Run:

```bash
python -c "
from htmltools import TagList, div

class Bar:
    def tagify(self):
        return 'bar'

class Foo:
    def tagify(self):
        return TagList(Bar())  # un-tagified Bar

try:
    div(Foo()).tagify()
except TypeError as e:
    print('OK:', e)
"
```

Expected output: `OK: Expected a fully tagified value, but a child .tagify() returned a TagList containing an un-tagified Bar at index 0. ...`

- [ ] **Step 5: No final commit needed; the prior task commits cover all changes.**

---

## Spec coverage check

| Spec section | Tasks |
|---|---|
| Type model | Task 7 |
| Class signatures (TagList) | Task 8 |
| Class signatures (Tag) | Task 9 |
| Class signatures (Tagifiable) | Task 10 |
| Class signatures (JSXTag) | Task 11 |
| TagList.tagify A3 body | Tasks 1, 2 |
| Render-time guard message | Task 4 |
| Migration — internal | Tasks 8–11 |
| Migration — downstreams (Changelog) | Task 14 |
| Migration — dependency bump | Task 6 |
| Runtime tests | Tasks 1, 3, 5 |
| Static type tests | Task 13 |
| Out of scope (JSXTag genericity, freezing, auto-recurse, subclass-preserving signature) | Not implemented, called out in spec |

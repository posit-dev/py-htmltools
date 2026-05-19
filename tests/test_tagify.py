import pytest

from htmltools import Tagified, TagList, div, span


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


def test_tagify_is_idempotent() -> None:
    # .tagify() applied twice must produce the same HTML as once.
    original = div("hello", span("world"))
    once = original.tagify()
    twice = once.tagify()
    assert once.get_html_string() == twice.get_html_string()


def test_render_guard_catches_mutation_after_tagify() -> None:
    # The static guarantee is a snapshot at .tagify() time; if a Tagifiable
    # is appended afterwards, the render-time guard must catch it.
    tagified = div("hello").tagify()
    tagified.children.append(_NestedTagifiable())
    with pytest.raises(RuntimeError, match="_NestedTagifiable"):
        tagified.get_html_string()


# -----------------------------------------------------------------------------
# Boundary normalization of child.tagify() returns (closes #117)
# -----------------------------------------------------------------------------
# The `Tagified` union now permits `None`, `float`, and `Sequence[Tagified]`
# returns from `.tagify()` (parallel to `TagChild` on the input side). The
# `TagList.tagify()` boundary routes every return through
# `_tagchilds_to_tagnodes`, which normalizes those shapes uniformly: drop
# `None`, str-ify `float`/`int`, flatten `Sequence`.


class _ReturnsNone:
    def tagify(self) -> Tagified:
        return None


class _ReturnsFloat:
    def tagify(self) -> Tagified:
        return 3.14


class _ReturnsList:
    def tagify(self) -> Tagified:
        return ["a", "b"]


def test_tagify_returning_None_drops_the_slot() -> None:
    tl = TagList(_ReturnsNone(), "after").tagify()
    assert list(tl) == ["after"]
    # Render must not crash.
    assert tl.get_html_string() == "after"


def test_tagify_returning_float_is_strified() -> None:
    tl = TagList(_ReturnsFloat(), "after").tagify()
    assert list(tl) == ["3.14", "after"]
    assert "3.14" in tl.get_html_string()


def test_tagify_returning_Sequence_flattens() -> None:
    tl = TagList(_ReturnsList(), "after").tagify()
    assert list(tl) == ["a", "b", "after"]
    # Render: sibling text nodes concatenate without separators.
    assert tl.get_html_string() == "abafter"


# -----------------------------------------------------------------------------
# Strict post-tagify boundary: bare `Tag` / `TagList` returns are rejected.
# -----------------------------------------------------------------------------
# `Tagified` permits `TagifiedTag` (not bare `Tag`) and `TagifiedTagList`
# (not bare `TagList`). A `.tagify()` that returns `div(some_tagifiable)`
# without calling `.tagify()` on the result will leave un-tagified content
# in the tree — the bare-Tag shape passes runtime `isinstance(_, Tag)`
# checks but fails the `Tagified` contract. The boundary catches this
# before render time, where the error message would otherwise be the
# misleading "tree was mutated to add a Tagifiable object after
# .tagify() was called."


class _ReturnsBareTagWithTagifiableChild:
    """Wraps a Tagifiable in a bare div() — does NOT call .tagify() on result."""

    def tagify(
        self,
    ):  # intentionally unannotated; pyright would catch the contract violation
        return div(_NestedTagifiable())


class _ReturnsBareTagWithLeafChild:
    """Even a bare Tag whose contents are leaves violates the contract."""

    def tagify(self):
        return div("leaf")


def test_taglist_tagify_raises_on_bare_Tag_return_with_tagifiable_child() -> None:
    # Direct reproducer of the bug Copilot flagged on PR #118: a bare Tag
    # carrying an un-tagified child slipped past the boundary and only
    # failed at render time with a misleading "tree was mutated" error.
    tl = TagList(_ReturnsBareTagWithTagifiableChild())
    with pytest.raises(TypeError, match=r"Tag at index"):
        tl.tagify()


def test_taglist_tagify_raises_on_bare_Tag_return_with_leaf_child() -> None:
    # Even when the bare Tag's children are leaves, the strict boundary
    # raises — matching the static `Tagified` contract (which excludes bare
    # `Tag`). Easy fix at the call site: append `.tagify()` to the return.
    tl = TagList(_ReturnsBareTagWithLeafChild())
    with pytest.raises(TypeError, match=r"Tag at index"):
        tl.tagify()


def test_taglist_tagify_accepts_self_tagified_Tag_return() -> None:
    # The recommended fix: call `.tagify()` on the wrapping Tag before returning.
    class _ReturnsTagifiedTag:
        def tagify(self):
            return div(_NestedTagifiable()).tagify()

    tl = TagList(_ReturnsTagifiedTag()).tagify()
    html = tl.get_html_string()
    assert "<div>" in html
    assert "bar" in html
    assert "</div>" in html

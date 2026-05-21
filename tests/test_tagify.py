import pytest

from htmltools import TagList, div, span


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


def test_render_guard_catches_untagified_tagifiable() -> None:
    # Defense-in-depth: calling .get_html_string() directly on a buildable
    # tree that contains an un-tagified Tagifiable raises with an
    # actionable message. The normal render path (.render()) tagifies
    # first and avoids this; this guard catches the direct-call case.
    tl = TagList(_NestedTagifiable())
    with pytest.raises(RuntimeError, match="_NestedTagifiable"):
        tl.get_html_string()

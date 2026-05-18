import pytest

from htmltools import Tag, TagList, div, span


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
    assert isinstance(once, Tag)
    twice = once.tagify()
    assert isinstance(twice, Tag)
    assert once.get_html_string() == twice.get_html_string()


def test_render_guard_catches_mutation_after_tagify() -> None:
    # The static guarantee is a snapshot at .tagify() time; if a Tagifiable
    # is appended afterwards, the render-time guard must catch it.
    tagified = div("hello").tagify()
    assert isinstance(tagified, Tag)
    tagified.children.append(_NestedTagifiable())
    with pytest.raises(RuntimeError, match="_NestedTagifiable"):
        tagified.get_html_string()

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

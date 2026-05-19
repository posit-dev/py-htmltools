"""Runtime isinstance tests for the TagifiedTagList / TagifiedTag subclasses."""

from htmltools import Tag, TagList
from htmltools._core import TagifiedTag, TagifiedTagList


def test_TagifiedTagList_is_a_class() -> None:
    # Was a TypeAliasType before #116; isinstance would raise TypeError.
    # After: a real class.
    assert isinstance(TagifiedTagList(), TagifiedTagList)
    assert isinstance(TagifiedTagList(), TagList)


def test_TagifiedTag_is_a_class() -> None:
    assert isinstance(TagifiedTag("div"), TagifiedTag)
    assert isinstance(TagifiedTag("div"), Tag)

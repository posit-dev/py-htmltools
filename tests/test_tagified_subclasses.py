"""Runtime isinstance tests for the TagifiedTagList / TagifiedTag subclasses."""

from htmltools import Tag, TagList, div
from htmltools._core import TagifiedTag, TagifiedTagList


def test_TagifiedTagList_is_a_class() -> None:
    # Was a TypeAliasType before #116; isinstance would raise TypeError.
    # After: a real class.
    assert isinstance(TagifiedTagList(), TagifiedTagList)
    assert isinstance(TagifiedTagList(), TagList)


def test_TagifiedTag_is_a_class() -> None:
    assert isinstance(TagifiedTag("div"), TagifiedTag)
    assert isinstance(TagifiedTag("div"), Tag)


def test_TagList_tagify_returns_TagifiedTagList_instance() -> None:
    result = TagList("hi", div()).tagify()
    assert isinstance(result, TagifiedTagList)
    # Verify it's the actual class, not the base TagList
    assert type(result) is TagifiedTagList

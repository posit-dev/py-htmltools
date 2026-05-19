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


def test_Tag_tagify_returns_TagifiedTag_instance() -> None:
    result = div("hi").tagify()
    assert isinstance(result, TagifiedTag)
    assert type(result) is TagifiedTag


def test_TagifiedTagList_children_are_TagifiedTag() -> None:
    # Recursive guarantee: nested children inside a tagified result are also
    # TagifiedTag instances, not bare Tag.
    result = TagList(div(div("inner"))).tagify()
    inner = result[0]
    assert isinstance(inner, TagifiedTag)
    assert isinstance(inner.children[0], TagifiedTag)


def test_JSXTag_tagify_returns_TagifiedTag() -> None:
    # Import locally because JSXTag is not in the top-level htmltools namespace.
    from htmltools._jsx import JSXTag

    jsx = JSXTag("MyComponent")
    result = jsx.tagify()
    assert isinstance(result, TagifiedTag)

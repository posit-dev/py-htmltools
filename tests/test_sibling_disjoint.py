"""Tests that lock in the sibling-classes invariants from
decisions/2026-05-20-tagified-as-classes.md.

Tag and TagifiedTag are disjoint runtime classes (neither is a
subclass of the other). Same for TagList and TagifiedTagList. The
tagified-side classes are immutable.
"""

from htmltools import TagList, div, is_tagified
from htmltools._core import TagifiedTag, TagifiedTagList


def test_tagified_tag_is_not_a_Tag() -> None:
    from htmltools import Tag

    tt = div("x").tagify()
    assert isinstance(tt, TagifiedTag)
    assert not isinstance(tt, Tag)


def test_buildable_tag_is_not_a_TagifiedTag() -> None:
    t = div("x")
    assert not isinstance(t, TagifiedTag)


def test_tagified_taglist_is_not_a_TagList() -> None:
    ttl = TagList("x").tagify()
    assert isinstance(ttl, TagifiedTagList)
    assert not isinstance(ttl, TagList)


def test_buildable_taglist_is_not_a_TagifiedTagList() -> None:
    tl = TagList("x")
    assert not isinstance(tl, TagifiedTagList)


def test_TagifiedTag_has_no_mutators() -> None:
    tt = div("x").tagify()
    assert not hasattr(tt, "append")
    assert not hasattr(tt, "extend")
    assert not hasattr(tt, "insert")


def test_TagifiedTag_has_no_buildtime_helpers() -> None:
    tt = div("x").tagify()
    assert not hasattr(tt, "add_class")
    assert not hasattr(tt, "remove_class")
    assert not hasattr(tt, "has_class")
    assert not hasattr(tt, "__enter__")
    assert not hasattr(tt, "__exit__")


def test_TagifiedTagList_has_no_mutators() -> None:
    ttl = TagList("x").tagify()
    assert not hasattr(ttl, "append")
    assert not hasattr(ttl, "extend")
    assert not hasattr(ttl, "insert")


def test_TagifiedTagList_slice_returns_TagifiedTagList() -> None:
    ttl = TagList("a", "b", "c").tagify()
    sliced = ttl[0:2]
    assert isinstance(sliced, TagifiedTagList)
    assert len(sliced) == 2


def test_tagify_is_idempotent_returns_self() -> None:
    # TagifiedTag.tagify() and TagifiedTagList.tagify() return self,
    # not a copy. Documented invariant for the immutable side.
    tt = div("x").tagify()
    assert tt.tagify() is tt

    ttl = TagList("x").tagify()
    assert ttl.tagify() is ttl


def test_is_tagified_helper() -> None:
    assert is_tagified(div("x").tagify())
    assert is_tagified(TagList("x").tagify())
    assert not is_tagified(div("x"))
    assert not is_tagified(TagList("x"))
    assert not is_tagified("plain string")
    assert not is_tagified(None)
    assert not is_tagified(42)

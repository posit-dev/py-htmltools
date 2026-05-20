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
    Tagifiable,
    Tagified,
    TagList,
    div,
)
from htmltools._core import TagifiedTag, TagifiedTagList


def test_tag_tagify_returns_TagifiedTag() -> None:
    assert_type(div("hi").tagify(), TagifiedTag)


def test_taglist_tagify_returns_TagifiedTagList() -> None:
    assert_type(TagList("hi").tagify(), TagifiedTagList)


def test_bare_TagList_is_not_assignable_to_TagifiedTagList() -> None:
    tl: TagList = TagList("hi")
    # A bare TagList means TagList[TagNode], which may still contain Tagifiables.
    # It must NOT be assignable to TagifiedTagList without explicit narrowing.
    _: TagifiedTagList = tl  # pyright: ignore[reportAssignmentType]


def test_TagifiedTag_append_is_static_error() -> None:
    """TagifiedTag has no .append — static-error path.

    The body runs at runtime and *also* raises AttributeError, but this
    module is primarily exercised by pyright. The `# pyright: ignore`
    asserts the static error fires; the `pytest.raises` keeps the test
    green at runtime so it travels through CI's pytest run too.
    """
    import pytest

    tt: TagifiedTag = div("hi").tagify()
    with pytest.raises(AttributeError):
        tt.append("x")  # pyright: ignore[reportAttributeAccessIssue]


def test_TagifiedTagList_append_is_static_error() -> None:
    """TagifiedTagList has no .append — static-error path."""
    import pytest

    ttl: TagifiedTagList = TagList("hi").tagify()
    with pytest.raises(AttributeError):
        ttl.append("x")  # pyright: ignore[reportAttributeAccessIssue]


def test_Tag_does_not_accept_TagifiedTag() -> None:
    """Tag and TagifiedTag are disjoint — variance honest."""

    def f(t: Tag) -> str:
        return t.name

    tagified = div("hi").tagify()
    # This call would runtime-succeed (TagifiedTag has a .name attribute),
    # but pyright must reject the argument type since Tag and TagifiedTag
    # are sibling classes (neither subclasses the other).
    f(tagified)  # pyright: ignore[reportArgumentType]


def test_bare_TagList_append_accepts_Tagifiable() -> None:
    class _OkTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    # Default behavior is unchanged: bare TagList accepts any TagChild,
    # which includes Tagifiable. (Same as today and same as before #105.)
    tl: TagList = TagList()
    tl.append(_OkTagifiable())


def test_user_tagify_returning_bare_TagList_violates_Tagifiable() -> None:
    class _Bad:
        # Bare TagList annotation means TagList[TagNode], which is wider than
        # TagifiedTagList. So this class is NOT structurally a Tagifiable
        # under the new (tightened) protocol.
        def tagify(self) -> TagList:
            return TagList("x")

    _: Tagifiable = _Bad()  # pyright: ignore[reportAssignmentType]


def test_user_tagify_returning_TagifiedTagList_is_Tagifiable() -> None:
    class _Good:
        def tagify(self) -> TagifiedTagList:
            return TagList("x").tagify()

    _: Tagifiable = _Good()

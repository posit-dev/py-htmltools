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
    Tagifiable,
    Tagified,
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
    _: TagifiedTagList = tl  # pyright: ignore[reportAssignmentType]


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

    _: Tagifiable = _Bad()  # pyright: ignore[reportAssignmentType]


def test_user_tagify_returning_TagifiedTagList_is_Tagifiable() -> None:
    class _Good:
        def tagify(self) -> TagifiedTagList:
            return TagList("x").tagify()

    _: Tagifiable = _Good()

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


def test_TagifiedTagList_append_accepts_Tagifiable_lost_Q6() -> None:
    """
    Documents the *lost* Q6 trade-off.

    The spec's Q6 (see ``docs/superpowers/specs/2026-05-13-tagify-generic-design.md``)
    originally promised that ``TagifiedTagList.append(some_tagifiable)`` would
    static-error, on the grounds that ``TagifiedTagList = TagList[TagifiedNode]``
    and ``TagifiedNode`` excludes the un-resolved ``Tagifiable`` arm.

    Implementing that required making ``TagChild`` a *generic recursive
    ``TypeAliasType``*: ``TagChild[ChildT] = ChildT | TagList[ChildT] | float |
    None | Sequence[TagChild[ChildT]]``. Pyright (1.1.409) does not fully
    re-bind ``ChildT`` through the ``Sequence["TagChild[ChildT]"]`` arm when a
    downstream module imports the symbols in strict mode — every ``Tag``
    function signature leaks a ``Sequence[Unknown]`` arm, producing
    thousands of ``reportUnknownMemberType`` errors in Shiny's CI.

    We therefore reverted ``TagChild`` to a plain non-generic ``Union`` and
    let mutating methods on ``TagList[ChildT]`` accept the wide bare
    ``TagChild``. The static guarantee is gone, but the runtime guarantee
    is still enforced by ``TagList.get_html_string``'s render-time guard
    (covered by
    ``test_tagify.py::test_render_guard_catches_mutation_after_tagify``)
    and by the A3 boundary check inside ``TagList.tagify()``.

    If a future pyright/typing release handles recursive generic
    ``TypeAliasType`` cleanly across modules, flip this test back to the
    negative form (``# pyright: ignore[reportArgumentType]`` on the
    ``tl.append(...)`` call) and reinstate ``TagChild[ChildT]`` on
    ``TagList``'s mutation-method signatures.
    """

    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    # Today this type-checks (Q6 lost). In an ideal world it would fail.
    tl.append(_SomeTagifiable())


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

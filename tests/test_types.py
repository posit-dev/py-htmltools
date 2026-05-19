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
    TagNode,
    div,
)
from htmltools._core import TagifiedTag, TagifiedTagList


def test_tag_tagify_returns_TagifiedTag() -> None:
    assert_type(div("hi").tagify(), TagifiedTag)


def test_taglist_tagify_returns_TagifiedTagList() -> None:
    assert_type(TagList("hi").tagify(), TagifiedTagList)


def test_TagifiedTagList_append_rejects_Tagifiable_statically() -> None:
    """Mutators on TagifiedTagList narrow input to TagifiedChild; appending
    a Tagifiable must be a pyright error."""

    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    # Acceptable: a tagified node
    tl.append("ok")
    # Static error: bare Tagifiable is not in TagifiedChild.
    tl.append(_SomeTagifiable())  # pyright: ignore[reportArgumentType]


def test_TagifiedTagList_extend_rejects_Tagifiable_statically() -> None:
    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    tl.extend([_SomeTagifiable()])  # pyright: ignore[reportArgumentType]


def test_TagifiedTagList_insert_rejects_Tagifiable_statically() -> None:
    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    tl.insert(0, _SomeTagifiable())  # pyright: ignore[reportArgumentType]


def test_bare_TagList_is_not_assignable_to_TagifiedTagList() -> None:
    tl: TagList = TagList("hi")
    # A bare TagList means TagList[TagNode], which may still contain Tagifiables.
    # It must NOT be assignable to TagifiedTagList without explicit narrowing.
    _: TagifiedTagList = tl  # pyright: ignore[reportAssignmentType]


def test_TagifiedTagList_append_rejects_Tagifiable() -> None:
    """
    Appending a ``Tagifiable`` to a ``TagifiedTagList`` is a *static* error.

    Enforced by ``TagifiedTagList.append``'s narrow signature, which accepts
    only ``TagifiedChild`` (a non-generic union that excludes the
    ``Tagifiable`` arm of ``TagNode``). The previous design — a recursive
    generic ``TagChild[TagNodeT]`` — was abandoned in #105 because it
    leaked ``Sequence[Unknown]`` through downstream pyright in strict mode;
    the subclass-with-narrow-overrides approach (#116) closes the gap
    without parameterizing ``TagChild``.

    The runtime guards in ``TagList.tagify`` (boundary ``TypeError``) and
    ``get_html_string`` (render-time ``RuntimeError``) remain the safety
    net for code that uses ``# pyright: ignore`` to bypass the static check.
    """

    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    tl.append(_SomeTagifiable())  # pyright: ignore[reportArgumentType]


def test_TagifiedTag_append_rejects_Tagifiable_statically() -> None:
    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tag: TagifiedTag = div("hi").tagify()
    tag.append("ok")
    tag.append(_SomeTagifiable())  # pyright: ignore[reportArgumentType]


def test_TagifiedTag_extend_rejects_Tagifiable_statically() -> None:
    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tag: TagifiedTag = div("hi").tagify()
    tag.extend([_SomeTagifiable()])  # pyright: ignore[reportArgumentType]


def test_TagifiedTag_insert_rejects_Tagifiable_statically() -> None:
    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tag: TagifiedTag = div("hi").tagify()
    tag.insert(0, _SomeTagifiable())  # pyright: ignore[reportArgumentType]


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


def test_TagifiedTagList_to_bare_TagList_is_accepted() -> None:
    """Documents pyright's observed permissive behavior on TagifiedTagList flows.

    ``TagList`` is invariant in ``TagNodeT`` per its ``TypeVar`` declaration,
    so ``TagList[TagifiedNode]`` is *technically* not assignable to
    ``TagList[TagNode]``. In practice, pyright (verified through 1.1.409)
    treats a nominal subclass ``TagifiedTagList(TagList["TagifiedNode"])`` as
    assignable to bare ``TagList`` and to explicit ``TagList[TagNode]``,
    likely because the ``TagNodeT`` default and the class-hierarchy lookup
    take precedence over the parameterized-instance invariance check.

    This is the answer to the "open question" in #116 — the previous
    TypeAliasType alias appeared to "silently relax" variance, but the
    subclass form has the same practical behavior. Downstream consumers
    using ``def f(t: TagList): ...`` (or even ``TagList[TagNode]``) do NOT
    need migration to accept tagified inputs.

    If pyright ever starts flagging these flows, this fixture will fail —
    that's the signal to add a real migration note and update downstream
    packages.
    """

    def f_bare_taglist(t: TagList) -> str:
        return t.get_html_string()

    def f_explicit_taglist(t: TagList[TagNode]) -> str:
        return t.get_html_string()

    tagified: TagifiedTagList = TagList("hi").tagify()
    # All three of these are accepted by pyright. No `# pyright: ignore`
    # is needed (and adding one would be flagged as unnecessary if
    # `reportUnnecessaryTypeIgnoreComment` is enabled).
    f_bare_taglist(tagified)
    f_explicit_taglist(tagified)
    _: TagList[TagNode] = tagified


def test_TagifiedTag_to_bare_Tag_is_accepted() -> None:
    """Symmetric to ``test_TagifiedTagList_to_bare_TagList_is_accepted``."""

    def f_bare_tag(t: Tag) -> str:
        return t.get_html_string()

    def f_explicit_tag(t: Tag[TagNode]) -> str:
        return t.get_html_string()

    tagified: TagifiedTag = div("hi").tagify()
    f_bare_tag(tagified)
    f_explicit_tag(tagified)
    _: Tag[TagNode] = tagified

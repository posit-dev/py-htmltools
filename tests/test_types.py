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
from htmltools._core import TagifiedNode, TagifiedTagList


def test_tag_tagify_returns_Tag_TagifiedNode() -> None:
    assert_type(div("hi").tagify(), Tag[TagifiedNode])


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


def test_TagifiedTagList_append_accepts_Tagifiable() -> None:
    """
    Documents a deliberate static-typing gap: appending a ``Tagifiable``
    to a ``TagList[TagifiedNode]`` is **not** a static error today, even
    though ``TagifiedNode`` does not include the ``Tagifiable`` arm of
    ``TagNode``. The runtime catches it instead.

    Why we can't enforce it statically
    ----------------------------------
    The natural enforcement would parameterize ``TagChild`` itself —
    ``TagChild[TagNodeT] = TagNodeT | TagList[TagNodeT] | float | None |
    Sequence[TagChild[TagNodeT]]`` — and use it in mutation signatures so
    that ``TagList[TagifiedNode].append`` only accepts ``TagifiedNode``
    -shaped values. We tried that. Pyright (tested through 1.1.409)
    does not fully re-bind ``TagNodeT`` through the recursive
    ``Sequence["TagChild[TagNodeT]"]`` arm when a *downstream* module
    imports the symbols in strict mode. Every ``Tag``-function signature
    then leaks a ``Sequence[Unknown]`` arm, which surfaced as thousands
    of ``reportUnknownMemberType`` errors in Shiny's CI — far more noise
    than the win was worth.

    What we do instead
    ------------------
    - ``TagChild`` is a plain non-generic ``Union`` (including the
      recursive ``Sequence["TagChild"]`` arm for nested-list flattening).
    - Mutation methods on ``TagList[TagNodeT]`` and ``Tag[TagNodeT]`` accept
      bare ``TagChild`` (wide). This preserves the nested-list
      ergonomics like ``tl.append([a, b, [c, d]])``.
    - The "no un-tagified children in a tagified tree" invariant is
      enforced at runtime:
        * ``TagList.tagify()`` raises ``TypeError`` at the boundary
          when a child's ``.tagify()`` returns a ``TagList`` containing
          a ``Tagifiable``, naming the offending class and slot index.
        * ``TagList.get_html_string`` raises ``RuntimeError`` at render
          time if a ``Tagifiable`` is still in the tree (covers
          mutation-after-tagify; see
          ``test_tagify.py::test_render_guard_catches_mutation_after_tagify``).

    When to revisit
    ---------------
    If a future pyright/typing release handles recursive generic
    ``TypeAliasType`` cleanly across module boundaries, flip this test
    to a *negative* form (``# pyright: ignore[reportArgumentType]`` on
    the ``tl.append(...)`` call) and reinstate ``TagChild[TagNodeT]`` on
    ``TagList`` / ``Tag`` mutation-method signatures.
    """

    class _SomeTagifiable:
        def tagify(self) -> Tagified:
            return "x"

    tl: TagifiedTagList = TagList("hi").tagify()
    # This currently type-checks. In an ideal world it would static-error;
    # see the docstring for why we accept the gap.
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

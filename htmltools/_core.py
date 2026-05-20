# pyright: reportMissingTypeStubs=false, reportMissingImports=false

from __future__ import annotations

import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
import urllib.parse
import webbrowser
from collections import UserList, UserString
from copy import copy, deepcopy
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
    overload,
)

# Even though TypedDict is available in Python 3.8, because it's used with NotRequired,
# they should both come from the same typing module.
# https://peps.python.org/pep-0655/#usage-in-python-3-11
if sys.version_info >= (3, 11):
    from typing import Never, NotRequired, TypedDict
else:
    from typing_extensions import Never, NotRequired, TypedDict

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

from typing import Literal, Protocol, SupportsIndex, runtime_checkable

from packaging.version import Version
from typing_extensions import TypeVar

from ._util import (
    ensure_http_server,
    flatten,
    hash_deterministic,
    html_escape,
    package_dir,
)

__all__ = (
    "TagList",
    "Tag",
    "HTMLDocument",
    "HTMLTextDocument",
    "HTML",
    "MetadataNode",
    "HTMLDependency",
    "RenderedHTML",
    "TagAttrs",
    "TagAttrValue",
    "TagChild",
    "TagNode",
    "TagFunction",
    "Tagifiable",
    "Tagified",
    "TagifiedTag",
    "TagifiedTagList",
    "consolidate_attrs",
    "head_content",
    "is_tag_child",
    "is_tag_like",
    "is_tag_node",
    "is_tagified",
    "is_taglist_like",
    "wrap_displayhook_handler",
)


class RenderedHTML(TypedDict):
    dependencies: list["HTMLDependency"]
    html: str


# MetadataNode objects are not shown when a Tag tree is rendered to HTML text. They can
# be used to carry information that doesn't fit into the normal HTML tree structure,
# such as `HTMLDependency` objects.
#
# Note that when `x.tagify()` is called on the parent of a MetadataNode, it calls copy()
# on MetadataNode; when copied, the resulting object should be completely independent of
# the original. This may require implementing a custom `__copy__` method.
class MetadataNode:
    pass


T = TypeVar("T")

TagT = TypeVar("TagT", bound="Tag")

TagAttrValue = Union[str, float, bool, "HTML", None]
"""
Types that can be passed in as attributes to `Tag` functions. These values will be
converted to strings before being stored as tag attributes.
"""

TagAttrs = Union[Dict[str, TagAttrValue], "TagAttrDict"]
"""
For dictionaries of tag attributes (e.g., `{"id": "foo"}`), which can be passed as
unnamed arguments to Tag functions like `div()`.
"""

# Kept as a plain `Union` (not `TypeAliasType`) so the arms are visible
# in pyright diagnostics — a value typed as `TagNodeLeaf` shows up as
# `MetadataNode | ReprHtml | str | HTML` directly instead of as an
# opaque alias name.
TagNodeLeaf = Union["MetadataNode", "ReprHtml", str, "HTML"]
"""
Leaf nodes in a tag tree: members that do not recursively contain tag
children. `MetadataNode` carries non-rendered metadata, `ReprHtml` and
`HTML` render themselves, and `str` is plain text. These are the non-`Tag`
/ non-`TagList` arms shared by both `TagNode` and `TagifiedNode`.
"""

# A node that has already been fully tagified: no Tagifiable objects whose
# .tagify() still needs to be called. Recursive — a tagified Tag's children
# are themselves tagified.
TagifiedNode = Union["TagifiedTag", "TagifiedTagList", TagNodeLeaf]
"""
A fully-tagified child-slot type. References the `TagifiedTag` and
`TagifiedTagList` classes by forward reference (defined below). Calling
`.tagify()` on a node tree returns a structure whose slot items are all
`TagifiedNode`.

`TagifiedTagList` is a type-level member here for parity with how
`TagNode` contains `Tagifiable` (which subsumes both `Tag` and
`TagList`). At runtime a `TagifiedTagList` never appears as a child
slot of another `TagifiedTagList` — `_tagchilds_to_tagnodes` flattens
nested lists — but the type allows it.
"""

# Kept as a plain `Union` (not `TypeAliasType`) because pyright's
# recursive-alias resolution leaks `Unknown` when downstream packages
# inspect the type in strict mode. The alias name is then lost in
# diagnostics, but downstream pyright stays clean.
Tagified = Union[TagifiedNode, float, None, Sequence["Tagified"]]
"""
Anything `.tagify()` is permitted to return: a fully-tagified node, a
numeric/None leaf, or a recursive sequence thereof. `Tagified` mirrors
`TagChild`'s structural shape (both are `Element | float | None |
Sequence[recursive]`); the element-type unions (`TagifiedNode` /
`TagNode`) carry the tagified-vs-buildable distinction.
"""


# -----------------------------------------------------------------------------
# TagNode / TagChild
# -----------------------------------------------------------------------------
# NOTE: If this type is updated, please update `is_tag_node()`
TagNode = Union["Tagifiable", TagNodeLeaf]
"""
Types of objects that can be a node in a `Tag` tree. Equivalently, these are
the valid elements of a `TagList`. Note that this type represents the
internal structure of items in a `TagList`; the user-facing type is
`TagChild`.

`Tag` and `TagList` are structurally `Tagifiable` (each defines
`.tagify() -> Tagified`), so the `Tagifiable` arm subsumes them and
their tagified specializations. Only the leaf arm is spelled out
explicitly.
"""

# NOTE: If this type is updated, please update `is_tag_child()`.
#
# `TagChild` is intentionally NOT generic. Making it a generic
# `TypeAliasType` with a recursive `Sequence["TagChild[TagNodeT]"]`
# arm caused pyright to leak `Sequence[Unknown]` into every `Tag`
# function signature when inspected from a downstream module in
# strict mode (e.g. Shiny's CI reported 2500+
# `reportUnknownMemberType` errors). The trade-off is that
# `TagList.append(some_tagifiable)` on a tagified-flavored list no
# longer static-errors — the runtime guard in `TagList.get_html_string`
# still catches it at render time. See
# `tests/test_types.py::test_TagifiedTagList_append_accepts_Tagifiable`
# for the full rationale.
TagChild = Union[TagNode, float, None, Sequence["TagChild"]]
"""
Types of objects that can be passed as children to Tag functions like
`div()`. The `Tag` functions and the `TagList()` constructor can accept
these as unnamed arguments; they will be flattened and normalized to
`TagNode` objects.
"""


# These two types existed in htmltools 0.14.0 and earlier. They are here so
# that existing versions of Shiny will be able to load, but users of those
# existing packages will see type errors, which should encourage them to
# upgrade Shiny.
TagChildArg = Never
TagAttrArg = Never


TagChildT = TypeVar("TagChildT", bound=TagChild)
"""
Type variable for `TagChild`.
"""


def is_tag_node(x: object) -> TypeIs[TagNode]:
    """
    Check if an object is a `TagNode`.

    Note: The type hint is `TypeIs[TagNode]` to allow for type checking of the
    return value. (`TypeIs` is imported from `typing_extensions` for Python < 3.13.)

    Parameters
    ----------
    x
        Object to check.

    Returns
    -------
    :
        `True` if the object is a `TagNode`, `False` otherwise.
    """
    # Note: Tag and TagList are both Tagifiable
    return isinstance(x, (Tagifiable, MetadataNode, ReprHtml, str, HTML))


def is_tag_child(x: object) -> TypeIs[TagChild]:
    """
    Check if an object is a `TagChild`.

    Note: The type hint is `TypeIs[TagChild]` to allow for type checking of the
    return value. (`TypeIs` is imported from `typing_extensions` for Python < 3.13.)

    Parameters
    ----------
    x
        Object to check.

    Returns
    -------
    :
        `True` if the object is a `TagChild`, `False` otherwise.
    """

    if is_tag_node(x):
        return True
    if x is None:
        return True
    if isinstance(
        x,
        (
            # TagNode, # Handled above
            float,
            # None, # Handled above
            Sequence,
        ),
    ):
        return True

    # Could not determine the type
    return False


def is_tag_like(x: object) -> TypeIs["Tag | TagifiedTag"]:
    """
    True if `x` is either a buildable `Tag` or a tagified `TagifiedTag`.

    Both classes share the `_TagBase` plumbing (name, attrs, children,
    rendering). Use this helper at call sites that handle either form so
    the "either flavor" intent is explicit and the narrowing is expressed
    through public types rather than the private `_TagBase`.
    """
    return isinstance(x, (Tag, TagifiedTag))


def is_taglist_like(x: object) -> TypeIs["TagList | TagifiedTagList"]:
    """
    True if `x` is either a buildable `TagList` or a tagified `TagifiedTagList`.

    Both classes share the `_TagListBase` render plumbing. Use this helper
    at call sites that handle either form.
    """
    return isinstance(x, (TagList, TagifiedTagList))


def is_tagified(x: object) -> TypeIs["TagifiedTag | TagifiedTagList"]:
    """
    True if `x` is a fully-tagified container (`TagifiedTag` or `TagifiedTagList`).

    Useful for distinguishing post-`.tagify()` values from buildable
    `Tag` / `TagList` instances at runtime. Symmetric with `is_tag_like`
    and `is_taglist_like`.
    """
    return isinstance(x, (TagifiedTag, TagifiedTagList))


@runtime_checkable
class Tagifiable(Protocol):
    """
    Objects with `tagify()` methods are considered `Tagifiable`. The return
    value must be `Tagified` — i.e. fully tagified all the way down. See
    `TagifiedNode` / `TagifiedTagList`.
    """

    def tagify(self) -> "Tagified": ...


@runtime_checkable
class TagFunction(Protocol):
    """
    Tag functions, like `div()`, `span()`, etc.
    """

    def __call__(
        self,
        *args: TagChild | TagAttrs,
        _add_ws: TagAttrValue = ...,
        **kwargs: TagAttrValue,
    ) -> "Tag": ...


@runtime_checkable
class ReprHtml(Protocol):
    """
    Objects with a `_repr_html_()` method.
    """

    def _repr_html_(self) -> str: ...


# =============================================================================
# _TagListBase mixin (shared between TagList and TagifiedTagList)
# =============================================================================
class _TagListBase:
    """
    Render plumbing shared between `TagList` (buildable, `UserList`-backed)
    and `TagifiedTagList` (immutable, `Sequence`-backed). Both subclasses
    support iteration over their elements, which is all the bodies below
    need.

    This is the `TagList`-side analog of `_TagBase`: a methods-only mixin
    that does NOT inherit from `UserList` or `Sequence`. Subclasses bring
    their own iteration / indexing / mutation surface.
    """

    def tagify(self) -> "TagifiedTagList":
        """
        Return a fully-tagified form of this tag list. Implemented by subclasses.
        """
        raise NotImplementedError

    def get_html_string(
        self,
        indent: int = 0,
        eol: str = "\n",
        *,
        add_ws: bool = True,
        _escape_strings: bool = True,
    ) -> str:
        """
        Return the HTML string for this tag list.

        Parameters
        ----------
        indent
            Number of spaces to indent each line of the HTML.
        eol
            End-of-line character(s).
        add_ws:
            Whether to add whitespace between the opening tag and the first child. If
            either this is True, or the child's add_ws attribute is True, then
            whitespace will be added; if they are both False, then no whitespace will be
            added.
        """

        html_ = ""
        first_child = True
        prev_was_add_ws = add_ws

        for child in cast(Iterable[Any], self):
            if isinstance(child, MetadataNode):
                continue

            # True if the previous and current node are inline; False otherwise. This
            # affects whether or not we add whitespace and indentation.
            prev_or_current_add_ws = prev_was_add_ws or (
                is_tag_like(child) and child.add_ws
            )

            if first_child:
                first_child = False
            elif prev_or_current_add_ws:
                html_ += eol

            if is_tag_like(child):
                # Note that we don't pass _escape_strings along, because that should
                # only be set to True when <script> and <style> tags call
                # self.children.get_html_string(), and those tags don't have children to
                # recurse into.
                if prev_or_current_add_ws:
                    html_ += child.get_html_string(indent, eol)
                else:
                    html_ += child.get_html_string(0, "")

                prev_was_add_ws = child.add_ws

            elif isinstance(child, ReprHtml):
                if prev_was_add_ws:
                    html_ += "  " * indent

                html_ += child._repr_html_()  # pyright: ignore[reportPrivateUsage]

                prev_was_add_ws = False

            elif isinstance(child, Tagifiable):
                # Defense-in-depth: a buildable `TagList` containing an
                # un-tagified `Tagifiable` would normally be tagified
                # before reaching here (`.render()` calls `.tagify()`
                # first). This guard catches the case where a caller
                # invokes `.get_html_string()` directly on a buildable
                # tree, or where the type system was bypassed (cast,
                # __dict__ manipulation) to smuggle a `Tagifiable` into
                # a tagified container's internal storage.
                raise RuntimeError(
                    f"Encountered an un-tagified {type(child).__name__} at render time. "
                    "Call `.tagify()` (or `.render()`, which tagifies "
                    "internally) before invoking `.get_html_string()` on "
                    "a buildable tree."
                )

            else:
                # If we get here, x must be a string.
                if prev_was_add_ws:
                    html_ += "  " * indent

                if _escape_strings:
                    html_ += _normalize_text(child)
                else:
                    html_ += child

                prev_was_add_ws = False

        return html_

    def get_dependencies(self, *, dedup: bool = True) -> list["HTMLDependency"]:
        """
        Get any dependencies needed to render the HTML.

        Parameters
        ----------
        dedup
            Whether to deduplicate the dependencies.
        """

        deps: list[HTMLDependency] = []
        for x in cast(Iterable[Any], self):
            if isinstance(x, HTMLDependency):
                deps.append(x)
            elif is_tag_like(x):
                # When we recurse, don't deduplicate at every node. We only need to do
                # that once, at the top level.
                deps.extend(x.get_dependencies(dedup=False))

        if dedup:
            return _resolve_dependencies(deps)
        else:
            return deps

    def render(self) -> "RenderedHTML":
        """
        Get string representation as well as its HTML dependencies.
        """
        cp = self.tagify()
        deps = cp.get_dependencies()
        return {"dependencies": deps, "html": cp.get_html_string()}

    def save_html(
        self, file: str, *, libdir: Optional[str] = "lib", include_version: bool = True
    ) -> str:
        """
        Save to a HTML file.

        Parameters
        ----------
        file
            The file to save to.
        libdir
            The directory to save the dependencies to.
        include_version
            Whether to include the version number in the dependency folder name.

        Returns
        -------
        :
            The path to the generated HTML file.
        """
        return HTMLDocument(self).save_html(
            file, libdir=libdir, include_version=include_version
        )

    def show(self, renderer: Literal["auto", "ipython", "browser"] = "auto") -> object:
        """
        Preview as a complete HTML document.

        Parameters
        ----------
        renderer
            The renderer to use.
        """
        _tag_show(self, renderer)

    def __eq__(self, other: Any) -> bool:
        return _equals_impl(self, other)

    def __str__(self) -> str:
        return _render_tag_or_taglist(self)

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return str(self)


# =============================================================================
# TagList class
# =============================================================================
class TagList(_TagListBase, UserList[TagNode]):
    """
    Create an HTML tag list (i.e., a fragment of HTML)

    Parameters
    ----------
    *args
        The tag children to add to the list.

    Examples
    --------
    >>> from htmltools import TagList, div
    >>> TagList("hello", div(id="foo", class_="bar"))
    hello
    <div id="foo" class="bar"></div>
    """

    def _should_not_expand(self, x: object) -> TypeIs[str]:
        """
        Check if an object should not be expanded into a list of children.
        """
        return isinstance(x, str)

    def __init__(self, *args: TagChild) -> None:
        super().__init__(_tagchilds_to_tagnodes(args))

    def extend(self, other: Iterable[TagChild]) -> None:
        """
        Extend the children by appending an iterable of children.
        """
        super().extend(_tagchilds_to_tagnodes(other))

    def append(self, item: TagChild, *args: TagChild) -> None:
        """
        Append tag children to the end of the list.
        """

        self.extend([item, *args])

    def insert(self, i: SupportsIndex, item: TagChild) -> None:
        """
        Insert tag children before a given index.
        """

        self[i:i] = _tagchilds_to_tagnodes([item])

    def __add__(self, item: Iterable[TagChild]) -> "TagList":
        """
        Return a new TagList with the item added at the end.
        """

        if self._should_not_expand(item):
            return TagList(self, item)

        return TagList(self, *item)

    def __radd__(self, item: Iterable[TagChild]) -> "TagList":
        """
        Return a new TagList with the item added to the beginning.
        """

        if self._should_not_expand(item):
            return TagList(item, self)

        return TagList(*item, self)

    def tagify(self) -> "TagifiedTagList":
        """
        Convert any tagifiable children to TagifiedTag/TagifiedTagList objects.

        Raises
        ------
        TypeError
            If a child's ``.tagify()`` returned a ``TagList`` containing an
            un-tagified ``Tagifiable`` object — i.e. the recursion was not
            done all the way down. The error names the offending class and
            slot index so the broken ``.tagify()`` is easy to find.
        """

        # Work on a private list that we'll wrap into a TagifiedTagList at
        # the end. Use a plain list because items may expand (a child's
        # .tagify() can return a TagList which gets flattened in place).
        new_data: list[Any] = list(self.data)

        # Iterate backwards because if we hit a Tagifiable object, it may be
        # replaced with 0, 1, or more items (if it returns TagList).
        for i in reversed(range(len(new_data))):
            child = new_data[i]

            if isinstance(child, Tagifiable):
                tagified_child = child.tagify()
                # _tagchilds_to_tagnodes flattens TagList and
                # TagifiedTagList equivalently (both are handled by
                # `flatten`), normalizes float/None/Sequence, and
                # passes leaf nodes through.
                new_data[i : i + 1] = _tagchilds_to_tagnodes(
                    cast("Iterable[TagChild]", [tagified_child])
                )

            elif isinstance(child, MetadataNode):
                new_data[i] = copy(child)

        # Boundary check: after the recursion above, every child should be
        # a fully-tagified shape (TagifiedTag, TagifiedTagList, MetadataNode,
        # ReprHtml, str, or HTML). A bare Tagifiable still present here means
        # some child's `.tagify()` returned a value containing un-tagified
        # objects — which violates the Tagifiable protocol. Surface that
        # here, where the offending class and index are still in scope,
        # instead of waiting for the render-time guard in `get_html_string`
        # to raise a less-actionable error.
        for i, child in enumerate(new_data):
            if isinstance(child, Tagifiable) and not isinstance(
                child, (TagifiedTag, TagifiedTagList)
            ):
                raise TypeError(
                    "Expected a fully tagified value, but a child .tagify() "
                    f"returned an un-tagified {type(child).__name__} at index "
                    f"{i}. A .tagify() implementation must return a fully-"
                    "tagified value (consider returning `something.tagify()` "
                    "instead of `something`)."
                )

        # Wrap in a TagifiedTagList. Use __new__ + direct _data assignment
        # because we already normalized; running through __init__ would
        # re-normalize unnecessarily.
        out = TagifiedTagList.__new__(TagifiedTagList)
        out._data = tuple(  # pyright: ignore[reportPrivateUsage]
            cast("list[TagifiedNode]", new_data)
        )
        return out


# =============================================================================
# TagifiedTagList class
# =============================================================================
class TagifiedTagList(_TagListBase, Sequence["TagifiedNode"]):
    """
    A fully-tagified `TagList`. Immutable: no append / extend / insert
    / __setitem__ / pop / etc. Construct via `TagList.tagify()` or
    directly with pre-tagified arguments; once constructed the
    contents are frozen.

    Storage is an internal tuple. The `Sequence` ABC gives read-only
    indexing, iteration, `len()`, `__contains__`, `__reversed__`,
    `index`, and `count` — all that's needed for render-time access.
    """

    _data: "tuple[TagifiedNode, ...]"

    def __init__(self, *args: "Tagified") -> None:
        # Flatten/normalize input through the same pipeline TagList
        # uses, so float/None/nested Sequence behave consistently
        # between the two sides. Cast: _tagchilds_to_tagnodes expects
        # an iterable of TagChild; Tagified is a subset of TagChild
        # (TagifiedNode <: TagNode), so the cast is sound.
        normalized = _tagchilds_to_tagnodes(cast("tuple[TagChild, ...]", args))
        self._data = tuple(cast("list[TagifiedNode]", normalized))

    # Sequence ABC requirements ------------------------------------------------

    @overload
    def __getitem__(self, i: SupportsIndex) -> "TagifiedNode": ...
    @overload
    def __getitem__(self, i: slice) -> "TagifiedTagList": ...
    def __getitem__(
        self, i: "SupportsIndex | slice"
    ) -> "TagifiedNode | TagifiedTagList":
        if isinstance(i, slice):
            sliced = TagifiedTagList.__new__(TagifiedTagList)
            sliced._data = self._data[i]
            return sliced
        return self._data[i]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> "Iterator[TagifiedNode]":
        return iter(self._data)

    # Construction-not-mutation arithmetic --------------------------------------

    def __add__(self, item: "Iterable[Tagified]") -> "TagifiedTagList":
        # Mirror TagList.__add__'s str guard: a str is an Iterable, so a
        # naive splat would iterate it character-by-character. Treat it
        # as a single tagified leaf instead.
        if isinstance(item, str):
            return TagifiedTagList(*self._data, item)
        return TagifiedTagList(*self._data, *item)

    def __radd__(self, item: "Iterable[Tagified]") -> "TagifiedTagList":
        if isinstance(item, str):
            return TagifiedTagList(item, *self._data)
        return TagifiedTagList(*item, *self._data)

    # Idempotent tagify --------------------------------------------------------

    def tagify(self) -> "TagifiedTagList":
        return self


# =============================================================================
# TagAttrDict class
# =============================================================================
class TagAttrDict(Dict[str, "str | HTML"]):
    """
    A dictionary-like object that can be used to store attributes for a tag. All
    attribute values will be stored as strings.

    Parameters
    ----------
    *args
        A dictionary of attributes. The values can be strings, numbers, or booleans, and
        they will be converted to strings. A value can also be ``None``, in which case
        it will be skipped.
    **kwargs
        More attributes.
    """

    def __init__(
        self, *args: Mapping[str, TagAttrValue], **kwargs: TagAttrValue
    ) -> None:
        super().__init__()
        self.update(*args, **kwargs)

    def __setitem__(self, name: str, value: TagAttrValue) -> None:
        val = self._normalize_attr_value(value)
        if val is not None:
            nm = self._normalize_attr_name(name)
            super().__setitem__(nm, val)

    def update(  # type: ignore[reportIncompatibleMethodOverride] # TODO-future: fix typing
        self,
        *args: Mapping[str, TagAttrValue],
        **kwargs: TagAttrValue,
    ) -> None:
        if kwargs:
            args = args + (kwargs,)

        attrz: dict[str, str | HTML] = {}
        for arg in args:
            for k, v in arg.items():
                val = self._normalize_attr_value(v)
                if val is None:
                    continue
                nm = self._normalize_attr_name(k)

                if nm in attrz:
                    val = attrz[nm] + " " + val

                attrz[nm] = val

        super().update(attrz)

    @staticmethod
    def _normalize_attr_name(x: str) -> str:
        # e.g., foo_Bar_ -> foo-Bar
        if x.endswith("_"):
            x = x[:-1]
        return x.replace("_", "-")

    @staticmethod
    def _normalize_attr_value(x: TagAttrValue) -> str | HTML | None:
        if x is None or x is False:
            return None
        if x is True:
            return ""
        # Return both str and HTML objects as is.
        # HTML objects will handle value escaping when added to other values
        if isinstance(x, (str, HTML)):
            return x
        if isinstance(x, (int, float)):  # pyright: ignore[reportUnnecessaryIsInstance]
            return str(x)
        raise TypeError(
            f"Invalid type for attribute: {type(x)}."
            + "Consider calling str() on this value before treating it as a tag attribute."
        )


# =============================================================================
# Tag class
# =============================================================================
class _TagBase:
    """Shared state and render plumbing between Tag (buildable) and
    TagifiedTag (rendered).

    Both subclasses carry the same surface attributes (name, attrs,
    add_ws, children). The children attribute is narrowed to the
    concrete TagList / TagifiedTagList type in each subclass.

    Render / equality / repr methods live here so that both subclasses
    inherit a single implementation.
    """

    name: str
    attrs: "TagAttrDict"
    add_ws: bool
    # children is also narrowed in subclasses to its concrete type
    # (TagList for Tag, TagifiedTagList for TagifiedTag); we declare a
    # union here so the shared methods below type-check.
    children: "TagList | TagifiedTagList"

    def tagify(self) -> "TagifiedTag":
        """
        Return a fully-tagified form of this tag. Implemented by subclasses.
        """
        raise NotImplementedError

    def get_html_string(self, indent: int = 0, eol: str = "\n") -> str:
        """
        Get the HTML string representation of the tag.

        Parameters
        ----------
        indent
            The number of spaces to indent the tag.
        eol
            The end-of-line character(s).
        """

        indent_str = "  " * indent
        html_ = indent_str + "<" + self.name

        # Write attributes
        for key, val in self.attrs.items():
            if not isinstance(val, HTML):
                val = html_escape(val, attr=True)
            html_ += f' {key}="{val}"'

        # Dependencies are ignored in the HTML output
        children = [x for x in self.children if not isinstance(x, MetadataNode)]

        # Don't enclose JSX/void elements if there are no children
        if len(children) == 0 and self.name in _VOID_TAG_NAMES:
            return html_ + "/>"

        # Other empty tags are enclosed
        html_ += ">"
        close = "</" + self.name + ">"
        if len(children) == 0:
            return html_ + close

        # Inline a single/empty child text node
        if len(children) == 1 and isinstance(children[0], (str, HTML)):
            if self.name in _NO_ESCAPE_TAG_NAMES:
                return html_ + str(children[0]) + close
            else:
                return html_ + _normalize_text(children[0]) + close

        # Write children
        if self.add_ws:
            html_ += eol

        html_ += self.children.get_html_string(
            indent=indent + 1,
            eol=eol,
            add_ws=self.add_ws,
            _escape_strings=(self.name not in _NO_ESCAPE_TAG_NAMES),
        )

        if self.add_ws:
            html_ += eol + indent_str

        return html_ + close

    def get_dependencies(self, dedup: bool = True) -> list["HTMLDependency"]:
        """
        Get any HTML dependencies.
        """
        return self.children.get_dependencies(dedup=dedup)

    def render(self) -> RenderedHTML:
        """
        Get string representation as well as its HTML dependencies.
        """
        cp = self.tagify()
        deps = cp.get_dependencies()
        return {"dependencies": deps, "html": cp.get_html_string()}

    def save_html(
        self, file: str, *, libdir: Optional[str] = "lib", include_version: bool = True
    ) -> str:
        """
        Save to a HTML file.

        Parameters
        ----------
        file
            The file to save to.
        libdir
            The directory to save the dependencies to.
        include_version
            Whether to include the version number in the dependency folder name.

        Returns
        -------
        The path to the generated HTML file.
        """

        return HTMLDocument(self).save_html(
            file, libdir=libdir, include_version=include_version
        )

    def show(self, renderer: Literal["auto", "ipython", "browser"] = "auto") -> object:
        """
        Preview as a complete HTML document.

        Parameters
        ----------
        renderer
            The renderer to use.
        """
        _tag_show(self, renderer)

    def __eq__(self, other: Any) -> bool:
        return _equals_impl(self, other)

    def __str__(self) -> str:
        return _render_tag_or_taglist(self)

    def __repr__(self) -> str:
        return str(self)

    def _repr_html_(self) -> str:
        return str(self)

    def has_class(self, class_: str) -> bool:
        """
        Check if the tag has a particular class value.

        Parameters
        ----------
        class_
            The class name to check for.

        Returns
        -------
        :
            ``True`` if the tag has the class, ``False`` otherwise.
        """
        cls = self.attrs.get("class")
        if cls:
            return class_ in cls.split()
        return False


def _parse_tag_args(
    args: tuple[Any, ...],
    kwargs: dict[str, TagAttrValue],
    add_ws: TagAttrValue,
) -> tuple[bool, TagAttrDict, list[Any]]:
    """Parse the positional+kwarg arguments to `Tag` / `TagifiedTag`.

    Shared between both constructors: validates `_add_ws` is `bool`,
    extracts dict-shaped attrs from positional args (per the documented
    `Tag(...)` calling convention), folds them with `**kwargs` into a
    `TagAttrDict`, and returns the remaining positional args (the
    children) untouched.

    The children list is intentionally returned as `list[Any]` — each
    subclass narrows it to its own constructor's argument type
    (`TagChild` for `TagList`, `Tagified` for `TagifiedTagList`) at the
    call site.
    """
    # Note that _add_ws is marked as a TagAttrValue for the sake of static type
    # checking, but it must in fact be a bool. This is due to limitations in
    # Python's type system when passing along **kwargs.
    # https://github.com/posit-dev/py-htmltools/pull/67
    if not isinstance(add_ws, bool):
        raise TypeError("`_add_ws` must be `True` or `False`")
    attrs_dicts = cast(
        "list[Mapping[str, TagAttrValue]]",
        [x for x in args if isinstance(x, dict)],
    )
    attrs = TagAttrDict(*attrs_dicts, **kwargs)
    kids = [x for x in args if not isinstance(x, dict)]
    return add_ws, attrs, kids


def _thaw_top(x: "Tag | TagifiedTag") -> "Tag":
    """Build a buildable `Tag` from `x`'s top-level data.

    Only the top node is freshly mutable — children are passed by
    reference (they may still be `TagifiedTag` instances). This is the
    minimal "thaw" needed by `_hoist_head_content` to splice in head
    content without mutating a frozen `TagifiedTag`.
    """
    res = Tag.__new__(Tag)
    res.name = x.name
    res.add_ws = x.add_ws
    res.attrs = copy(x.attrs)
    res.children = TagList(*x.children)
    res.prev_displayhook = None
    return res


class Tag(_TagBase):
    """
    The HTML tag class.

    A Tag object consists of a name, attributes, and children. The name is a string, the
    attributes are held in a TagAttrDict object, and the children are held in a TagList
    object.

    This class usually should not be instantiated directly. Instead, use the tag wrapper
    functions in ``htmltools.tags``, like ``div()`` or ``a()``.

    Parameters
    -----------
    _name
        The tag's name.
    *args
        Children for the tag.
    _add_ws
        A ``bool`` indicating whether to add whitespace surrounding the tag (see Note
        for details).
    **kwargs
        Attributes for the tag.

    Attributes
    ----------
    name
        The tag's name.
    attrs
        The tag's attributes.
    children
        The tag's children.

    Note
    ----
    The `_add_ws` parameter controls whether whitespace is added around the tag. Inline
    tags (like `span()` and `a()`) default to  `False` and block tags (like `div()` and
    `p()`) default to `True`.

    When a tag with `_add_ws=True` is rendered to HTML, whitespace (including
    indentation) is added before the opening tag (like `<div>`), after the closing tag
    (like `</div>`), and also between the opening tag and its first child. This usually
    results in formatting that is easier to read.

    The only times that whitespace is not added around tags is when two sibling tags
    have `_add_ws=False`, or when a tag and its first child both have `_add_ws=False`.
    Bare strings are treated as children with `_add_ws=False`.

    If you need fine control over whitespace in the output HTML, you can create tags
    with `_add_ws=False` and manually add whitespace, like `div("\\n", span("a"),
    _add_ws=False)`.

    Examples
    --------
    >>> from htmltools import div
    >>> x = div("hello", id="foo", class_="bar")
    >>> x
    <div id="foo" class="bar">hello</div>
    >>> x.show()
    """

    name: str
    add_ws: bool
    attrs: TagAttrDict
    children: "TagList"

    def __init__(
        self,
        _name: str,
        *args: TagChild | TagAttrs,
        _add_ws: TagAttrValue = True,
        **kwargs: TagAttrValue,
    ) -> None:
        self.name = _name
        self.add_ws, self.attrs, kids = _parse_tag_args(args, kwargs, _add_ws)
        self.children = TagList(*cast("list[TagChild]", kids))  # pyright: ignore[reportIncompatibleVariableOverride]

        self.prev_displayhook: Callable[[object], None] | None = None

    def __copy__(self: TagT) -> TagT:
        cls = self.__class__
        cp = cls.__new__(cls)
        # Any instance fields (like .children, and _attrs for the tag subclass) are
        # shallow-copied.
        new_dict = {key: copy(value) for key, value in self.__dict__.items()}
        cp.__dict__.update(new_dict)
        return cp

    def __enter__(self) -> None:
        if self.prev_displayhook is not None:
            raise RuntimeError(
                "Attempted to enter a Tag object's context manager, but it has already been entered."
            )
        self.prev_displayhook = sys.displayhook
        sys.displayhook = wrap_displayhook_handler(
            # self.append takes a TagChild, but the wrapper expects a function that
            # takes a object.
            self.append  # pyright: ignore[reportArgumentType]
        )

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        # If we got here, then self.prev_displayhook must be not None.
        sys.displayhook = cast(Callable[[object], None], self.prev_displayhook)
        sys.displayhook(self)

    def insert(self, index: SupportsIndex, x: TagChild) -> None:
        """
        Insert tag children before a given index.
        """

        self.children.insert(index, x)

    def extend(self, x: Iterable[TagChild]) -> None:
        """
        Extend the children by appending an iterable of children.
        """

        self.children.extend(x)

    def append(self, *args: TagChild) -> None:
        """
        Append tag children to the end of the list.
        """

        self.children.append(*args)

    def add_class(self: TagT, class_: str, *, prepend: bool = False) -> TagT:
        """
        Add a class value to the HTML class attribute.

        Parameters
        ----------
        class_
            The class name to add.
        prepend
            Bool that determines if the `class` is added to the beginning or end of the
            class attribute.

        Returns
        -------
        :
            The modified tag.
        """
        if prepend:
            self.attrs.update({"class": class_}, {"class": self.attrs.get("class")})
        else:
            self.attrs.update({"class": self.attrs.get("class")}, {"class": class_})
        return self

    def remove_class(self: TagT, class_: str) -> TagT:
        """
        Remove a class value from the HTML class attribute.

        Parameters
        ----------
        class_
            The class name to remove.

        Returns
        -------
        :
            The modified tag.
        """
        # Nothing to do if no class is specified
        if not class_:
            return self
        cls = self.attrs.get("class") or ""

        # If no class attribute exists, there's nothing to remove
        if not cls:
            return self

        # Coerce and clean
        class_ = str(class_).strip()

        # Remove the class value from the ordered set of class values
        # Note: .split() splits on any whitespace and removes empty strings
        new_classes = [cls_val for cls_val in cls.split() if cls_val != class_]
        if len(new_classes) > 0:
            # Store the new class value
            self.attrs.update({"class": " ".join(new_classes)})
        else:
            # If no class values remain, remove the class attribute
            self.attrs.pop("class")
        return self

    def add_style(self: TagT, style: str | HTML, *, prepend: bool = False) -> TagT:
        """
        Add a style value(s) to the HTML style attribute.

        Parameters
        ----------
        style
            CSS properties and values already properly formatted. Each should already
            contain trailing semicolons.
        prepend
            Bool that determines if the `style` is added to the beginning or end of the
            style attribute.

        See Also
        --------
        ~htmltools.css

        Returns
        -------
        :
            The modified tag.
        """

        if isinstance(  # type: ignore[reportUnnecessaryIsInstance]
            style, (str, HTML)
        ) and not style.endswith(";"):
            raise ValueError("`Tag.add_style(style=)` must end with a semicolon")

        if prepend:
            self.attrs.update({"style": style}, {"style": self.attrs.get("style")})
        else:
            self.attrs.update({"style": self.attrs.get("style")}, {"style": style})
        return self

    def tagify(self) -> "TagifiedTag":
        """
        Convert any tagifiable children to TagifiedTag/TagifiedTagList objects.
        """
        # Build a fresh TagifiedTag with tagified children. Construct via
        # __new__ + manual field population so we bypass the constructor's
        # argument-parsing logic. TagifiedTag is not a context manager, so
        # don't copy `prev_displayhook`.
        out = TagifiedTag.__new__(TagifiedTag)
        out.name = self.name
        out.add_ws = self.add_ws
        out.attrs = copy(self.attrs)
        out.children = self.children.tagify()
        return out


class TagifiedTag(_TagBase):
    """
    A fully-tagified `Tag`. Immutable: no mutators, no add_class, no
    context-manager use. Construct via `Tag.tagify()` or directly with
    pre-tagified arguments.
    """

    children: "TagifiedTagList"

    def __init__(
        self,
        _name: str,
        *args: "Tagified | TagAttrs",
        _add_ws: TagAttrValue = True,
        **kwargs: TagAttrValue,
    ) -> None:
        self.name = _name
        self.add_ws, self.attrs, kids = _parse_tag_args(args, kwargs, _add_ws)
        self.children = TagifiedTagList(  # pyright: ignore[reportIncompatibleVariableOverride]
            *cast("tuple[Tagified, ...]", tuple(kids))
        )

    def tagify(self) -> "TagifiedTag":
        return self


# Tags that have the form <tagname />
_VOID_TAG_NAMES = {
    "area",
    "base",
    "br",
    "col",
    "command",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

_NO_ESCAPE_TAG_NAMES = {"script", "style"}


def _render_tag_or_taglist(x: "_TagBase | _TagListBase") -> str:
    """Render a Tag or TagList to a string.

    This looks at html_dependency_render_mode to see if HTMLDependency objects should be
    serialized as HTML. This type of serialization is used with Quarto.
    """
    rendered = x.render()
    res = rendered["html"]
    from . import html_dependency_render_mode

    if html_dependency_render_mode == "json":
        dep_html = [
            x.serialize_to_script_json().get_html_string()
            for x in rendered["dependencies"]
        ]
        res += "\n".join(dep_html)

    return str(res)


def wrap_displayhook_handler(
    handler: Callable[[object], None],
) -> Callable[[object], None]:
    """
    Wrap a displayhook function to handle different types of input objects

    This function takes a function ``handler`` that would be used as a displayhook, and
    returns a function which filters/transforms the input object depending on its type,
    before passing it to ``handler()``.
    """

    def handler_wrapper(value: object) -> None:
        if isinstance(value, (Tag, TagList, Tagifiable)):
            handler(value)  # pyright: ignore[reportUnknownArgumentType]
        elif isinstance(value, ReprHtml):
            handler(HTML(value._repr_html_()))  # pyright: ignore[reportPrivateUsage]
        elif value not in (None, ...):
            handler(value)

    return handler_wrapper


# =============================================================================
# HTMLDocument class
# =============================================================================
class HTMLDocument:
    """
    Create an HTML document from Tag objects.

    Parameters
    ----------
    *args
        Children to add to the document.
    **kwargs
        Attributes to set on the document (i.e., the root <html> tag).

    Examples
    --------
    >>> from htmltools import HTMLDocument, h1, tags
    >>> HTMLDocument(h1("Hello"), tags.meta(name="description", content="test"), lang = "en")
    """

    def __init__(
        self,
        *args: TagChild,
        **kwargs: TagAttrValue,
    ) -> None:
        self._content: TagList = TagList(*args)
        self._html_attr_args: dict[str, TagAttrValue] = kwargs

    def __copy__(self) -> "HTMLDocument":
        cls = self.__class__
        cp = cls.__new__(cls)
        # Any instance fields (like .children, and _attrs for the tag subclass) are
        # shallow-copied.
        new_dict = {key: copy(value) for key, value in self.__dict__.items()}
        cp.__dict__.update(new_dict)
        return cp

    def append(self, *args: TagChild) -> None:
        """
        Add children to the document.

        Parameters
        ----------
        *args
            Children to add to the document.
        """
        self._content.append(*args)

    def render(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> RenderedHTML:
        """
        Render the document.

        Parameters
        ----------
        lib_prefix
            A prefix to add to relative paths to dependency files.
        include_version
            Whether to include the version number in the dependency's folder name.
        """

        html_ = self._gen_html_tag_tree(lib_prefix, include_version=include_version)
        rendered = html_.render()
        rendered["html"] = "<!DOCTYPE html>\n" + rendered["html"]
        return rendered

    def save_html(
        self, file: str, libdir: Optional[str] = "lib", include_version: bool = True
    ) -> str:
        """
        Save the document to a HTML file.

        Parameters
        ----------
        file
            The file to save to.
        libdir
            The directory to save the dependencies to (relative to the file's directory).
        include_version
            Whether to include the version number in the dependency folder name.
        """

        # Directory where dependencies are copied to.
        destdir = str(Path(file).resolve().parent)
        if libdir:
            destdir = os.path.join(destdir, libdir)

        rendered = self.render(lib_prefix=libdir, include_version=include_version)
        for dep in rendered["dependencies"]:
            dep.copy_to(destdir, include_version=include_version)

        with open(file, "w", encoding="utf-8") as f:
            f.write(rendered["html"])
        return file

    # Take the stored content, and generate an <html> tag which contains the correct
    # <head> and <body> content. HTMLDependency items will be extracted out of the body
    # and inserted into the <head>.
    # - lib_prefix: A directory prefix to add to <script src="[lib_prefix]/script.js">
    #   and <link rel="[lib_prefix]/style.css"> tags.
    def _gen_html_tag_tree(
        self, lib_prefix: Optional[str], include_version: bool
    ) -> Tag:
        # Tagify first so .get_dependencies() sees deps that only
        # materialize during tagify (e.g. JSXTag injects its React
        # dependencies on .tagify()). _hoist_head_content thaws the
        # tagified wrapper into a buildable Tag so it can splice in
        # the hoisted head content.
        content: TagList = self._content
        html: Tag
        body: TagifiedTag

        if (
            len(content) == 1
            and isinstance(content[0], Tag)
            and cast(Tag, content[0]).name == "html"
        ):
            user_html = cast(Tag, content[0])
            user_html.attrs.update(**self._html_attr_args)
            tagified_html = user_html.tagify()
            html = HTMLDocument._hoist_head_content(
                tagified_html, lib_prefix, include_version
            )
            return html

        if (
            len(content) == 1
            and isinstance(content[0], Tag)
            and cast(Tag, content[0]).name == "body"
        ):
            user_body = cast(Tag, content[0])
        else:
            user_body = Tag("body", content)

        body = user_body.tagify()

        tagified_html = Tag(
            "html", Tag("head"), body, _add_ws=True, **self._html_attr_args
        ).tagify()
        html = HTMLDocument._hoist_head_content(
            tagified_html, lib_prefix, include_version
        )
        return html

    # Given a tagified <html> tag, build a fresh buildable copy of the top
    # node (and its <head> child), extract dependencies from the tree, and
    # splice the dependency tags into <head>.
    @staticmethod
    def _hoist_head_content(
        x: TagifiedTag, lib_prefix: Optional[str], include_version: bool
    ) -> Tag:
        if x.name != "html":
            raise ValueError(f"Expected <html> tag, got <{x.name}>.")

        # Thaw the tagified <html> wrapper into a buildable Tag so we can
        # splice in the hoisted head content. Children stay tagified
        # (TagifiedTag instances) — only the top node is freshly mutable.
        res = _thaw_top(x)

        # <head> needs to be a direct child of <html>, but not necessarily the first
        # child (it would be suprising if you weren't able to, for example, have a
        # HTMLDependency() as the first child of <html>).
        head_index: Optional[int] = None
        for i, child in enumerate(res.children):
            if is_tag_like(child) and child.name == "head":
                head_index = i
                break

        if head_index is None:
            res.insert(0, Tag("head"))
            head_index = 0

        # Thaw the <head> child too — we need to mutate it.
        head_child = res.children[head_index]
        head = _thaw_top(head_child) if is_tag_like(head_child) else Tag("head")
        res.children[head_index] = head
        # Put <meta charset="utf-8"> at beginning of head, and other hoisted tags at the
        # end. This matters only if the <head> tag starts out with some children.
        head.insert(0, Tag("meta", charset="utf-8"))

        # Add some metadata about the dependencies so that shiny.js' renderDependency
        # logic knows not to re-render them.
        deps = x.get_dependencies()
        if len(deps) > 0:
            head.append(
                Tag(
                    "script",
                    ";".join([d.name + "[" + str(d.version) + "]" for d in deps]),
                    type="application/html-dependencies",
                )
            )

        head.extend(
            [
                d.as_html_tags(lib_prefix=lib_prefix, include_version=include_version)
                for d in deps
            ]
        )
        return res


class HTMLTextDocument:
    """
    Create an HTML document object from text.

    The text should be a complete HTML document, with `<html>`. This class is used to
    insert HTML dependency objects into the head of an existing HTML document.

    Parameters
    ----------
    template
        The template to use.
    deps
        HTML dependencies for the document.
    deps_replace_pattern
        A string that will be replaced with the head content. The first instance of this
        string will be replaced with the head content. If this is None, then deps must
        be provided.

    Examples
    --------
    >>> dep = HTMLDependency(name="foo", version="1.0.0", script={"src": "foo.js"})
    >>> doc = HTMLTextDocument(
            '<html><head><meta data-foo=""></head><body></body></html>',
            deps=[dep],
            deps_replace_pattern='<meta data-foo="">',
        )
    >>> res = doc.render()
    {
      'dependencies': [<HTMLDependency "foo-1.0.0">],
      'html': '<html><head><script type="application/html-dependencies">foo[1.0.0]</script>\n<script src="foo.js"></script></head><body></body></html>'
    }
    """

    def __init__(
        self,
        html: str,
        deps: Optional[list[HTMLDependency]] = None,
        deps_replace_pattern: Optional[str] = None,
    ) -> None:
        if deps_replace_pattern is None and deps is not None:
            raise ValueError(
                "If deps is not None, deps_replace_pattern must also be not None."
            )

        self._html = html
        if deps is None:
            deps = []
        self._deps = deps

        self._deps_replace_pattern = deps_replace_pattern

        self._extract_serialized_html_deps()

    def render(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> RenderedHTML:
        """
        Render the document.

        Parameters
        ----------
        lib_prefix
            A prefix to add to relative paths to dependency files.
        include_version
            Whether to include the version number in the dependency's folder name.
        """

        dep_tags = TagList()
        # Add some metadata about the dependencies so that shiny.js' renderDependency
        # logic knows not to re-render them.
        if len(self._deps) > 0:
            dep_tags.append(
                Tag(
                    "script",
                    ";".join([d.name + "[" + str(d.version) + "]" for d in self._deps]),
                    type="application/html-dependencies",
                )
            )

        dep_tags.extend(
            [
                d.as_html_tags(lib_prefix=lib_prefix, include_version=include_version)
                for d in self._deps
            ]
        )

        rendered_dep_tags = dep_tags.render()

        html = self._html.replace(
            cast(str, self._deps_replace_pattern),  # If we got here, we know it's a str
            rendered_dep_tags["html"],
            1,
        )

        return {"dependencies": deepcopy(self._deps), "html": html}

    def _extract_serialized_html_deps(self) -> None:
        """
        Search the HTML text for serialized HTML dependency objects, remove the text for
        those serialized objects, and add the reconstituted dependency objects to
        self._deps.
        """
        self._html, body_deps = self._static_extract_serialized_html_deps(self._html)
        self._deps.extend(body_deps)

    @staticmethod
    def _static_extract_serialized_html_deps(
        html: str,
    ) -> tuple[str, list[HTMLDependency]]:
        # Scan for HTML dependencies that were serialized via
        # HTMLdependency.get_tag_representation()
        pattern = r'<script type="application/json" data-html-dependency="">((?:.|\r|\n)*?)</script>'
        dep_strs = re.findall(pattern, html)

        # Remove the serialized HTML dependencies from the HTML string
        html = re.sub(pattern, "", html)

        # Reconstitute the HTMLDependency objects
        #
        # Note: htmltools normally would dedupe dependencies, but
        # with HTMLTextDocuments, the input HTML would usually have been generated by
        # something else (like Quarto) and may not have the dependencies deduped.
        seen_deps: set[str] = set()
        deps: list[HTMLDependency] = []
        for dep_str in dep_strs:
            if dep_str in seen_deps:
                continue
            args = json.loads(dep_str)
            dep = HTMLDependency(**args)
            deps.append(dep)
            seen_deps.add(dep_str)

        return (html, deps)


# =============================================================================
# HTML strings
# =============================================================================


class HTML(UserString):
    """
    Mark a string as raw HTML. This will prevent the string from being escaped when
    rendered inside an HTML tag.

    Examples
    --------
    >>> from htmltools import HTML, div
    >>> div("<p>Hello</p>")
    <div>&lt;p&gt;Hello&lt;/p&gt;</div>
    >>> div(HTML("<p>Hello</p>"))
    <div><p>Hello</p></div>
    """

    def __init__(self, html: object) -> None:
        super().__init__(str(html))

    def __str__(self) -> str:
        return self.as_string()

    # DEV NOTE: 2024/09 -
    #   This class is a building block for other classes, therefore it should not
    #   tagifiable! If this method is added, HTML strings are escaped within Shiny and
    #   not kept "as is"
    # def tagify(self) -> Tag:
    #     return self.as_string()

    # Cases:
    # * `str + str` should return str # Not HTML's responsibility!
    # * `str + HTML()` should return HTML() # Handled by HTML.__radd__()
    # * `HTML() + str` should return HTML()
    # * `HTML() + HTML()` should return HTML()
    def __add__(self, other: object) -> HTML:
        if isinstance(other, HTML):
            # HTML strings should be concatenated without escaping
            # Convert each element to strings, then concatenate them, and return HTML
            # Case: `HTML() + HTML()`
            return HTML(self.as_string() + other.as_string())

        # Non-HTML text added to HTML should be escaped before being added
        # Convert each element to strings, then concatenate them, and return HTML
        # Case: `HTML() + str`
        return HTML(self.as_string() + html_escape(str(other)))

    # Right side addition for when types are: `str + HTML()` or `unknown + HTML()`
    def __radd__(self, other: object) -> HTML:
        # Non-HTML text added to HTML should be escaped before being added
        # Convert each element to strings, then concatenate them, and return HTML
        # Case: `str + HTML()`
        return HTML(html_escape(str(other)) + self.as_string())

    def __repr__(self) -> str:
        return self.as_string()

    def _repr_html_(self) -> str:
        return self.as_string()

    def as_string(self) -> str:
        # Returns a new string
        return self.data + ""


# =============================================================================
# HTML dependencies
# =============================================================================
class HTMLDependencySource(TypedDict):
    package: NotRequired[Optional[str]]
    subdir: str


class HTMLDependencyUrl(TypedDict):
    href: str


class SourcePathMapping(TypedDict):
    source: str
    href: str


# These TypedDict declarations are a weird combination of the class and non-class forms
# of TypedDict. We use total=False for the optional attrs, and use inheritance to
# combine the required and optional attrs. The reason we use the non-class TypedDict is
# because some of the attributes (like `async`) are reserved keywords in Python, and
# can't be used as field names in a class. Awkward.
class ScriptItemBaseAttrs(TypedDict):
    src: str


ScriptItemExtraAttrs = TypedDict(
    "ScriptItemExtraAttrs",
    {
        "async": str,
        "crossorigin": str,
        "defer": str,
        "fetchpriority": str,
        "integrity": str,
        "referrerpolicy": str,
        "type": str,
    },
    total=False,
)


class ScriptItem(ScriptItemBaseAttrs, ScriptItemExtraAttrs):
    pass


class StylesheetItemBaseAttrs(TypedDict):
    href: str


StylesheetItemExtraAttrs = TypedDict(
    "StylesheetItemExtraAttrs",
    {
        "as": str,
        "crossorigin": str,
        "disabled": str,
        "hreflang": str,
        "imagesizes": str,
        "imagesrcset": str,
        "integrity": str,
        "media": str,
        "prefetch": str,
        "referrerpolicy": str,
        "rel": str,
        "sizes": str,
        "title": str,
        "type": str,
    },
    total=False,
)


class StylesheetItem(StylesheetItemExtraAttrs, StylesheetItemBaseAttrs):
    pass


class MetaItemBaseAttrs(TypedDict):
    name: str
    content: str


MetaItemExtraAttrs = TypedDict(
    "MetaItemExtraAttrs", {"charset": str, "http-equiv": str}, total=False
)


class MetaItem(MetaItemBaseAttrs, MetaItemExtraAttrs):
    pass


class HTMLDependency(MetadataNode):
    """
    Define an HTML dependency.

    Define an HTML dependency (i.e. CSS and/or JavaScript bundled in a directory). HTML
    dependencies make it possible to use libraries like jQuery, Bootstrap, and d3 in a
    more composable and portable way than simply using script, link, and style tags.

    Parameters
    ----------
    name
        Library name.
    version
        Library version.
    source
        A specification for the location of dependency files.
    script
        ``<script>`` tags to include in the document's ``<head>``. Each tag definition
        should include at least the ``src`` attribute (which should be file path
        relative to the ``source`` file location).
    stylesheet
        ``<link>`` tags to include in the document's ``<head>``. Each tag definition
        should include at least the ``href`` attribute (which should be file path
        relative to the ``source`` file location).
    all_files
        Whether all files under the ``source`` directory are dependency files. If
        ``False``, only the files specified in script and stylesheet are treated as
        dependency files.
    meta
        ``<meta>`` tags to include in the document's ``<head>``.
    head
        Tags to include in the document's ``<head>``.

    Examples
    --------
    >>> dep = HTMLDependency(
            name="mypackage",
            version="1.0",
            source={
                "package": "mypackage",
                "subdir": "lib/",
            },
            script={"src": "foo.js"},
            stylesheet={"href": "css/foo.css"},
        )

    >>> x = div("Hello", dep)
    >>> x.render()
    """

    name: str
    version: Version
    source: Optional[HTMLDependencySource | HTMLDependencyUrl]
    script: list[ScriptItem]
    stylesheet: list[StylesheetItem]
    meta: list[MetaItem]
    all_files: bool
    head: Optional[TagList]

    def __init__(
        self,
        name: str,
        version: str | Version,
        *,
        source: Optional[HTMLDependencySource | HTMLDependencyUrl] = None,
        script: Optional[ScriptItem | list[ScriptItem]] = None,
        stylesheet: Optional[StylesheetItem | list[StylesheetItem]] = None,
        all_files: bool = False,
        meta: Optional[MetaItem | list[MetaItem]] = None,
        head: TagChild = None,
    ) -> None:
        self.name = name
        self.version = Version(version) if isinstance(version, str) else version

        if source is not None:
            if not isinstance(source, dict):  # type: ignore
                raise TypeError(
                    f"Expected `source=` to be a dict (or `None`), but got {type(source)}"
                )
            if not (("href" in source) or ("subdir" in source)):
                raise TypeError(
                    "Expected `source=` to have either `subdir` [and `package`] key or `href` key."
                )
        self.source = source

        if script is None:
            script = []
        elif isinstance(script, dict):
            script = [script]
        self._validate_dicts(script, ["src"])
        self.script = script

        if stylesheet is None:
            stylesheet = []
        elif isinstance(stylesheet, dict):
            stylesheet = [stylesheet]
        self._validate_dicts(stylesheet, ["href"])
        self.stylesheet = stylesheet

        # Ensures a rel='stylesheet' default
        for s in self.stylesheet:
            if "rel" not in s:
                s["rel"] = "stylesheet"

        if meta is None:
            meta = []
        elif isinstance(meta, dict):
            meta = [meta]
        self._validate_dicts(meta, ["name", "content"])
        self.meta = meta

        self.all_files = all_files

        if head is None:
            self.head = None
        elif isinstance(head, str):
            # User doesn't have to manually wrap the text in HTML().
            self.head = TagList(HTML(head))
        else:
            self.head = TagList(head)

    def source_path_map(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> SourcePathMapping:
        """
        Returns a dict of the absolute 'source' filepath and the 'href' path it will
        point to in the HTML (given the lib_prefix).
        """

        src = self.source
        if src is None:
            return {"source": "", "href": ""}

        if "href" in src:
            return {"source": "", "href": src["href"]}

        pkg = src.get("package", None)
        if pkg is None:
            source = os.path.realpath(src["subdir"])
        else:
            source = os.path.join(package_dir(pkg), src["subdir"])

        href = self.name
        if include_version:
            href += "-" + str(self.version)
        if lib_prefix:
            href = posixpath.join(lib_prefix, href)
        return {"source": source, "href": href}

    def as_html_tags(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> TagList:
        """
        Render the dependency as a ``TagList()``.
        """
        d = self.as_dict(lib_prefix=lib_prefix, include_version=include_version)
        metas = [Tag("meta", **m) for m in d["meta"]]
        links = [Tag("link", **s) for s in d["stylesheet"]]
        scripts = [Tag("script", **s) for s in d["script"]]
        return TagList(*metas, *links, *scripts, self.head)

    def serialize_to_script_json(self, indent: int | None = None) -> Tag:
        res = {
            "name": self.name,
            "version": str(self.version),
            "source": self.source,
            "script": self.script,
            "stylesheet": self.stylesheet,
            "meta": self.meta,
            "all_files": self.all_files,
            # Tags cannot be serialized to JSON, so render to HTML
            "head": (
                TagList(self.head).get_html_string() if self.head is not None else None
            ),
        }

        return Tag(
            "script",
            # "</script>" in a script tag must be escaped
            json.dumps(res, indent=indent).replace("</script>", "<\\/script>"),
            type="application/json",
            data_html_dependency=True,
        )

    def as_dict(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> dict[str, Any]:
        """
        Returns a dict of the dependency's attributes.
        """

        # The paths["source"] is the absolute path to the source directory.
        # This may be empty if the dependency is a URL.
        # Only use `source_path_map()["href"]`!
        source_href = self.source_path_map(
            lib_prefix=lib_prefix, include_version=include_version
        )["href"]

        stylesheets = deepcopy(self.stylesheet)
        for s in stylesheets:
            href = urllib.parse.quote(s["href"])
            s.update(
                {
                    "href": posixpath.join(source_href, href),
                    "rel": "stylesheet",
                }
            )

        scripts = deepcopy(self.script)
        for s in scripts:
            src = urllib.parse.quote(s["src"])
            s.update({"src": posixpath.join(source_href, src)})

        head: Optional[str]
        if self.head is None:
            head = None
        else:
            head = self.head.get_html_string()

        return {
            "name": self.name,
            "version": str(self.version),
            "script": scripts,
            "stylesheet": stylesheets,
            "meta": self.meta,
            "head": head,
        }

    def copy_to(self, path: str, include_version: bool = True) -> None:
        """
        Copy the dependency's files to the given path.
        """

        paths = self.source_path_map(lib_prefix=None, include_version=include_version)
        if paths["source"] == "":
            return None

        # Collect all the source files
        if self.all_files:
            path_src = Path(paths["source"])
            src_files = [str(x.relative_to(path_src)) for x in path_src.glob("*")]
        else:
            src_files = [
                *[s["src"] for s in self.script],
                *[s["href"] for s in self.stylesheet],
            ]

        # Verify they all exist
        for f in src_files:
            src_file = os.path.join(paths["source"], f)
            if not os.path.exists(src_file):
                raise Exception(
                    f"Failed to copy HTML dependency {self.name}-{str(self.version)} "
                    + f"because {src_file} doesn't exist."
                )

        # Set up the target directory.
        target_dir = Path(os.path.join(path, paths["href"])).resolve()
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy all the files
        for f in src_files:
            src_file = os.path.join(paths["source"], f)
            target_file = os.path.join(target_dir, f)
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, target_file)
            elif os.path.isdir(src_file):
                shutil.copytree(src_file, target_file)

    def _validate_dicts(self, ld: Iterable[object], req_attr: list[str]) -> None:
        for d in ld:
            self._validate_dict(d, req_attr)

    def _validate_dict(self, d: object, req_attr: list[str]) -> None:
        if not isinstance(d, dict):
            raise TypeError(
                f"Expected dict, got {type(d)} for {d} in HTMLDependency "
                + f"{self.name}-{self.version}"
            )
        for a in req_attr:
            if a not in d:
                raise KeyError(
                    f"Missing required attribute '{a}' for {d} in HTMLDependency "
                    + f"{self.name}-{self.version}"
                )

    def __repr__(self):
        return f'<HTMLDependency "{self.name}-{self.version}">'

    def __str__(self):
        return str(self.as_html_tags())

    def __eq__(self, other: Any) -> bool:
        return _equals_impl(self, other)


def _resolve_dependencies(deps: list[HTMLDependency]) -> list[HTMLDependency]:
    map: dict[str, HTMLDependency] = {}
    for dep in deps:
        if dep.name not in map:
            map[dep.name] = dep
        else:
            if dep.version > map[dep.name].version:
                map[dep.name] = dep

    return list(map.values())


def head_content(*args: TagChild) -> HTMLDependency:
    """
    Place content in the ``<head>`` of the HTML document.

    Parameters
    ----------
    *args
        The content to place in the ``<head>``.

    Note
    ----
    If the same content, ``x``, is included in a document multiple times via
    ``head_content(x)``, ``x`` will only appear once in the final HTML document's
    ``<head>``. More often than not, this is desirable behavior, but if you need the
    same content included multiple times, you can add some irrelevant/empty tags (e.g.,
    ``TagList(x, Tag("meta"))``) to make sure ``x`` is included multiple times.

    Examples
    --------
    >>> from htmltools import *
    >>> x = div(head_content(title("My Title")))
    >>> print(HTMLDocument(x).render()["html"])
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>My Title</title>
      </head>
      <body>
        <div></div>
      </body>
    </html>
    """
    head = TagList(*args)
    head_str = head.get_html_string()
    # Create unique ID to use as name
    name = "headcontent_" + hash_deterministic(head_str)
    return HTMLDependency(name=name, version="0.0", head=head)


# If no children are provided, it will not be able to infer the type of `TagChildT`.
# Using `TagChild`, even though the list will be empty.
@overload
def consolidate_attrs(
    *args: TagAttrs,
    **kwargs: TagAttrValue,
) -> tuple[TagAttrs, list[TagChild]]: ...


# Same as original definition
@overload
def consolidate_attrs(
    *args: TagChildT | TagAttrs,
    **kwargs: TagAttrValue,
) -> tuple[TagAttrs, list[TagChildT]]: ...


def consolidate_attrs(
    *args: TagChildT | TagAttrs,
    **kwargs: TagAttrValue,
) -> tuple[TagAttrs, list[TagChildT]]:
    """
    Consolidate attributes and children into a single tuple.

    Convenience function to consolidate attributes and children into a single tuple. All
    `args` that are not dictionaries are considered children. This helps preserve the
    non-attribute elements within `args`. To extract the attributes, all `args` and
    `kwargs` are passed to `Tag` function and the attributes (`.attrs`) are extracted
    from the resulting `Tag` object.

    Parameters
    ----------
    *args
        Child elements to this tag and attribute dictionaries.
    **kwargs
        Named attributes to this tag.

    Returns
    -------
    :
        A tuple of attributes and children. The attributes are a dictionary of combined
        named attributes, and the children are a list of unaltered child elements.
    """
    tag = Tag("consolidate_attrs", *args, **kwargs)

    # Convert to a plain dict to avoid getting custom methods from TagAttrDict
    # Cast to `TagAttrs` as that is the common type used by py-shiny
    attrs = cast(TagAttrs, dict(tag.attrs))

    # Do not alter/flatten children structure (like `TagList` does)
    # Instead, return all `args` who are not dictionaries
    children = [child for child in args if not isinstance(child, dict)]
    return (attrs, children)


# =============================================================================
# Utility functions
# =============================================================================


# Convert a list of TagChild objects to a list of TagNode objects. Does not alter input
# object.
def _tagchilds_to_tagnodes(x: Iterable[TagChild]) -> list[TagNode]:
    if isinstance(x, str):
        return [x]

    result = flatten(x)
    for i, item in enumerate(result):
        if isinstance(item, (int, float)):
            result[i] = str(item)
        elif not is_tag_node(item):
            raise TypeError(
                f"Invalid tag item type: {type(item)}. "
                + "Consider calling str() on this value before treating it as a tag item."
            )

    # At this point, we know that all items in result must be valid TagNode
    # objects, because None, int, float, and TagList objects have been removed. (Note
    # that the TagList objects that have been flattened are TagList which are NOT tags.)
    return cast("list[TagNode]", result)


def _tag_show(
    self: "_TagBase | _TagListBase",
    renderer: Literal["auto", "ipython", "browser"] = "auto",
) -> object:
    if renderer == "auto":
        try:
            import IPython

            ipy = (  # pyright: ignore[reportUnknownVariableType]
                IPython.get_ipython()  # pyright: ignore[reportUnknownMemberType, reportPrivateImportUsage, reportAttributeAccessIssue]
            )
            renderer = "ipython" if ipy else "browser"
        except ImportError:
            renderer = "browser"

    # TODO: can we get htmlDependencies working in IPython?
    if renderer == "ipython":
        from IPython.core.display import (
            display_html,  # pyright: ignore[reportUnknownVariableType]
        )

        # https://github.com/ipython/ipython/pull/10962
        return display_html(  # pyright: ignore[reportUnknownVariableType]
            str(self), raw=True, metadata={"text/html": {"isolated": True}}
        )

    if renderer == "browser":
        tmpdir = tempfile.gettempdir()
        key_ = "viewhtml" + str(hash(str(self)))
        dir = os.path.join(tmpdir, key_)
        Path(dir).mkdir(parents=True, exist_ok=True)
        file = os.path.join(dir, "index.html")
        self.save_html(file)
        port = ensure_http_server(tmpdir)
        webbrowser.open(f"http://localhost:{port}/{key_}/index.html")
        return file

    raise Exception(f"Unknown renderer {renderer}")


def _normalize_text(txt: str | HTML) -> str:
    if isinstance(txt, HTML):
        return txt.as_string()
    else:
        return html_escape(txt, attr=False)


def _equals_impl(x: Any, y: Any) -> bool:
    if not isinstance(y, type(x)):
        return False
    for key in x.__dict__.keys():
        if getattr(x, key, None) != getattr(y, key, None):
            return False
    return True

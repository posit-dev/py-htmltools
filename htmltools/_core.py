import os
import sys
import shutil
import tempfile
from pathlib import Path
from copy import copy, deepcopy
import urllib.parse
import webbrowser
from typing import (
    Iterable,
    Optional,
    Sequence,
    Union,
    List,
    Dict,
    Mapping,
    Any,
    TypeVar,
    cast,
)

# Even though TypedDict is available in Python 3.8, because it's used with NotRequired,
# they should both come from the same typing module.
# https://peps.python.org/pep-0655/#usage-in-python-3-11
if sys.version_info >= (3, 11):
    from typing import NotRequired, TypedDict
else:
    from typing_extensions import NotRequired, TypedDict

if sys.version_info >= (3, 8):
    from typing import SupportsIndex, Protocol, runtime_checkable, Literal
else:
    from typing_extensions import (
        SupportsIndex,
        Protocol,
        runtime_checkable,
        Literal,
    )

from packaging.version import Version


from ._util import (
    ensure_http_server,
    _package_dir,  # type: ignore
    _html_escape,  # type: ignore
    _flatten,  # type: ignore
    hash_deterministic,
)

__all__ = (
    "TagList",
    "Tag",
    "HTMLDocument",
    "HTML",
    "MetadataNode",
    "HTMLDependency",
    "RenderedHTML",
    "TagAttrArg",
    "TagChildArg",
    "TagChild",
    "TagFunction",
    "Tagifiable",
    "head_content",
)


class RenderedHTML(TypedDict):
    dependencies: List["HTMLDependency"]
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

# Types that can be passed in as attributes to tag functions.
TagAttrArg = Union[str, float, bool, None]

# Types of objects that can be a child of a tag.
TagChild = Union["Tagifiable", "Tag", MetadataNode, str]

# Types that can be passed as args to TagList() and tag functions.
TagChildArg = Union[
    TagChild,
    "TagList",
    float,
    None,
    Dict[str, TagAttrArg],  # i.e., tag attrbutes (e.g., {"id": "foo"})
    Sequence["TagChildArg"],
]


# Objects with tagify() methods are considered Tagifiable. Note that an object returns a
# TagList, the children of the TagList must also be tagified.
@runtime_checkable
class Tagifiable(Protocol):
    def tagify(self) -> Union["TagList", "Tag", MetadataNode, str]:
        ...


# Tag functions, like div(), span(), etc.
@runtime_checkable
class TagFunction(Protocol):
    def __call__(
        self,
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> "Tag":
        ...


# =============================================================================
# TagList class
# =============================================================================
class TagList(List[TagChild]):
    """
    Create an HTML tag list (i.e., a fragment of HTML)

    Parameters
    ----------
    *args
        The tag children to add to the list.

    Example
    -------
    >>> from htmltools import TagList, div
    >>> TagList("hello", div(id="foo", class_="bar"))
    hello
    <div id="foo" class="bar"></div>
    """

    def __init__(self, *args: TagChildArg) -> None:
        super().__init__(_tagchildargs_to_tagchilds(args))

    def extend(self, x: Iterable[TagChildArg]) -> None:
        """
        Extend the children by appending an iterable of children.
        """

        super().extend(_tagchildargs_to_tagchilds(x))

    def append(self, *args: TagChildArg) -> None:  # type: ignore
        """
        Append tag children to the end of the list.
        """

        # Note that if x is a list or tag_list, it could be flattened into a list of
        # TagChildArg or TagChild objects, and the list.append() method only accepts one
        # item, so we need to wrap it into a list and send it to .extend().
        self.extend(args)

    def insert(self, index: SupportsIndex, x: TagChildArg) -> None:
        """
        Insert tag children before a given index.
        """

        self[index:index] = _tagchildargs_to_tagchilds([x])

    def tagify(self) -> "TagList":
        """
        Convert any tagifiable children to Tag/TagList objects.
        """

        cp = copy(self)

        # Iterate backwards because if we hit a Tagifiable object, it may be replaced
        # with 0, 1, or more items (if it returns TagList).
        for i in reversed(range(len(cp))):
            child = cp[i]

            if isinstance(child, Tagifiable):
                tagified_child = child.tagify()
                if isinstance(tagified_child, TagList):
                    # If the Tagifiable object returned a TagList, flatten it into this one.
                    cp[i : i + 1] = _tagchildargs_to_tagchilds(tagified_child)
                else:
                    cp[i] = tagified_child

            elif isinstance(child, MetadataNode):
                cp[i] = copy(child)
        return cp

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

    def render(self) -> RenderedHTML:
        """
        Get string representation as well as it's HTML dependencies.
        """
        cp = self.tagify()
        deps = cp.get_dependencies()
        return {"dependencies": deps, "html": cp.get_html_string()}

    def get_html_string(
        self, indent: int = 0, eol: str = "\n", *, _escape_strings: bool = True
    ) -> "HTML":
        """
        Return the HTML string for this tag list.

        Parameters
        ----------
        indent
            Number of spaces to indent each line of the HTML.
        eol
            End-of-line character(s).
        """

        html_ = ""
        line_prefix = ""
        for child in self:
            if isinstance(child, Tag):
                # Note that we don't pass _escape_strings along, because that should
                # only be set to True when <script> and <style> tags call
                # self.children.get_html_string(), and those tags don't have children to
                # recurse into.
                html_ += line_prefix + child.get_html_string(indent, eol)
            elif isinstance(child, MetadataNode):
                continue
            elif isinstance(child, Tagifiable):
                raise RuntimeError(
                    "Encountered a non-tagified object. x.tagify() must be called before x.render()"
                )
            else:
                # If we get here, x must be a string.
                if _escape_strings:
                    html_ += line_prefix + ("  " * indent) + _normalize_text(child)
                else:
                    html_ += line_prefix + ("  " * indent) + child

            if line_prefix == "":
                line_prefix = eol
        return HTML(html_)

    def get_dependencies(self, *, dedup: bool = True) -> List["HTMLDependency"]:
        """
        Get any dependencies needed to render the HTML.

        Parameters
        ----------
        dedup
            Whether to deduplicate the dependencies.
        """

        deps: List[HTMLDependency] = []
        for x in self:
            if isinstance(x, HTMLDependency):
                deps.append(x)
            elif isinstance(x, Tag):
                # When we recurse, don't deduplicate at every node. We only need to do
                # that once, at the top level.
                deps.extend(x.get_dependencies(dedup=False))

        if dedup:
            return _resolve_dependencies(deps)
        else:
            return deps

    def show(self, renderer: Literal["auto", "ipython", "browser"] = "auto") -> object:
        """
        Preview as a complete HTML document.

        Parameters
        ----------
        renderer
            The renderer to use.
        """
        _tag_show(self, renderer)

    def __str__(self) -> str:
        return str(self.get_html_string())

    def __eq__(self, other: Any) -> bool:
        return _equals_impl(self, other)

    def __repr__(self) -> str:
        return repr(self.get_html_string())

    def _repr_html_(self) -> str:
        return str(self.get_html_string())


# =============================================================================
# TagAttrs class
# =============================================================================
class TagAttrs(Dict[str, str]):
    """
    A dictionary-like object that can be used to store attributes for a tag.

    Parameters
    ----------
    *args
        The initial attributes.
    **kwargs
        More attributes.
    """

    def __init__(self, *args: Mapping[str, TagAttrArg], **kwargs: TagAttrArg) -> None:
        super().__init__()
        self.update(*args, **kwargs)

    def __setitem__(self, name: str, value: TagAttrArg) -> None:
        val = self._normalize_attr_value(value)
        if val is not None:
            nm = self._normalize_attr_name(name)
            super().__setitem__(nm, val)

    # Note: typing is ignored because the type checker thinks this is an incompatible
    # override. It's possible that we could find a way to override so that it's happy.
    def update(  # type: ignore
        self, *args: Mapping[str, TagAttrArg], **kwargs: TagAttrArg
    ) -> None:
        if kwargs:
            args = args + (kwargs,)

        attrz: Dict[str, Union[str, HTML]] = {}
        for arg in args:
            for k, v in arg.items():
                val = self._normalize_attr_value(v)
                if val is None:
                    continue
                nm = self._normalize_attr_name(k)

                # Preserve the HTML() when combining two HTML() attributes
                if nm in attrz:
                    val = attrz[nm] + HTML(" ") + val

                attrz[nm] = val

        super().update(attrz)

    @staticmethod
    def _normalize_attr_name(x: str) -> str:
        # e.g., foo_Bar_ -> foo-Bar
        if x.endswith("_"):
            x = x[:-1]
        return x.replace("_", "-")

    @staticmethod
    def _normalize_attr_value(x: TagAttrArg) -> Optional[str]:
        if x is None or x is False:
            return None
        if x is True:
            return ""
        if isinstance(x, (int, float)):
            return str(x)
        if isinstance(x, (HTML, str)):
            return x
        raise TypeError(
            f"Invalid type for attribute: {type(x)}."
            + "Consider calling str() on this value before treating it as a tag attribute."
        )


# =============================================================================
# Tag class
# =============================================================================
class Tag:
    """
    The HTML tag class.

    Parameters
    -----------
    _name
        The tag's name.
    *args
        Children for the tag.
    children
        Children for the tag.
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

    Example
    --------
    >>> from htmltools import div
    >>> x = div("hello", id="foo", class_="bar")
    >>> x
    <div id="foo" class="bar">hello</div>
    >>> x.show()
    """

    name: str
    attrs: TagAttrs
    children: TagList

    def __init__(
        self,
        _name: str,
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> None:
        self.name = _name

        # As a workaround for Python not allowing for numerous keyword
        # arguments of the same name, we treat any dictionaries that appear
        # within children as attributes (i.e., treat them like kwargs).
        arguments = _flatten(args)
        if children:
            arguments.extend(_flatten(children))

        attrs = [x for x in arguments if isinstance(x, dict)]
        self.attrs = TagAttrs(*attrs, **kwargs)

        kids = [x for x in arguments if not isinstance(x, dict)]
        self.children = TagList(*kids)

    def __call__(self, *args: TagChildArg, **kwargs: TagAttrArg) -> "Tag":
        self.children.extend(args)
        self.attrs.update(**kwargs)
        return self

    def __copy__(self: TagT) -> TagT:
        cls = self.__class__
        cp = cls.__new__(cls)
        # Any instance fields (like .children, and _attrs for the tag subclass) are
        # shallow-copied.
        new_dict = {key: copy(value) for key, value in self.__dict__.items()}
        cp.__dict__.update(new_dict)
        return cp

    def insert(self, index: SupportsIndex, x: TagChildArg) -> None:
        """
        Insert tag children before a given index.
        """

        self.children.insert(index, x)

    def extend(self, x: Iterable[TagChildArg]) -> None:
        """
        Extend the children by appending an iterable of children.
        """

        self.children.extend(x)

    def append(self, *args: TagChildArg) -> None:
        """
        Append tag children to the end of the list.
        """

        self.children.append(*args)

    def add_class(self, x: str) -> "Tag":
        """
        Add an HTML class attribute.

        Parameters
        ----------
        x
            The class name to add.

        Returns
        -------
        The modified tag.
        """
        cls = self.attrs.get("class")
        if cls:
            x = cls + " " + x
        self.attrs["class"] = x
        return self

    def has_class(self, class_: str) -> bool:
        """
        Check if the tag has a particular class.

        Parameters
        ----------
        class_
            The class name to check for.

        Returns
        -------
        ``True`` if the tag has the class, ``False`` otherwise.
        """
        cls = self.attrs.get("class")
        if cls:
            return class_ in cls.split(" ")
        else:
            return False

    def tagify(self: TagT) -> TagT:
        """
        Convert any tagifiable children to Tag/TagList objects.
        """

        cp = copy(self)
        cp.children = cp.children.tagify()
        return cp

    def get_html_string(self, indent: int = 0, eol: str = "\n") -> "HTML":
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
                val = _html_escape(val, attr=True)
            html_ += f' {key}="{val}"'

        # Dependencies are ignored in the HTML output
        children = [x for x in self.children if not isinstance(x, MetadataNode)]

        # Don't enclose JSX/void elements if there are no children
        if len(children) == 0 and self.name in _VOID_TAG_NAMES:
            return HTML(html_ + "/>")

        # Other empty tags are enclosed
        html_ += ">"
        close = "</" + self.name + ">"
        if len(children) == 0:
            return HTML(html_ + close)

        # Inline a single/empty child text node
        if len(children) == 1 and isinstance(children[0], str):
            if self.name in _NO_ESCAPE_TAG_NAMES:
                return HTML(html_ + children[0] + close)
            else:
                return HTML(html_ + _normalize_text(children[0]) + close)

        # Write children
        # TODO: inline elements should eat ws?
        html_ += eol
        html_ += self.children.get_html_string(
            indent + 1, eol, _escape_strings=(self.name not in _NO_ESCAPE_TAG_NAMES)
        )
        return HTML(html_ + eol + indent_str + close)

    def render(self) -> RenderedHTML:
        """
        Get string representation as well as it's HTML dependencies.
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

    def get_dependencies(self, dedup: bool = True) -> List["HTMLDependency"]:
        """
        Get any HTML dependencies.
        """
        return self.children.get_dependencies(dedup=dedup)

    def show(self, renderer: Literal["auto", "ipython", "browser"] = "auto") -> object:
        """
        Preview as a complete HTML document.

        Parameters
        ----------
        renderer
            The renderer to use.
        """
        _tag_show(self, renderer)

    def __str__(self) -> str:
        return str(self.get_html_string())

    def __repr__(self) -> str:
        return repr(self.get_html_string())

    def _repr_html_(self) -> str:
        return str(self.get_html_string())

    def __eq__(self, other: Any) -> bool:
        return _equals_impl(self, other)


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

# =============================================================================
# HTMLDocument class
# =============================================================================
class HTMLDocument:
    """
    Create an HTML document.

    Parameters
    ----------
    *args
        Children to add to the document.
    **kwargs
        Attributes to set on the document (i.e., the root <html> tag).

    Example
    -------
    >>> from htmltools import HTMLDocument, h1, tags
    >>> HTMLDocument(h1("Hello"), tags.meta(name="description", content="test"), lang = "en")
    """

    def __init__(
        self,
        *args: TagChildArg,
        **kwargs: TagAttrArg,
    ) -> None:
        self._content: TagList = TagList(*args)
        self._html_attr_args: Dict[str, TagAttrArg] = kwargs

    def __copy__(self) -> "HTMLDocument":
        cls = self.__class__
        cp = cls.__new__(cls)
        # Any instance fields (like .children, and _attrs for the tag subclass) are
        # shallow-copied.
        new_dict = {key: copy(value) for key, value in self.__dict__.items()}
        cp.__dict__.update(new_dict)
        return cp

    def append(self, *args: TagChildArg) -> None:
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

        with open(file, "w") as f:
            f.write(rendered["html"])
        return file

    # Take the stored content, and generate an <html> tag which contains the correct
    # <head> and <body> content. HTMLDependency items will be extracted out of the body
    # and inserted into the <head>.
    # - lib_prefix: A directoy prefix to add to <script src="[lib_prefix]/script.js">
    #   and <link rel="[lib_prefix]/style.css"> tags.
    def _gen_html_tag_tree(
        self, lib_prefix: Optional[str], include_version: bool
    ) -> Tag:
        content: TagList = self._content
        html: Tag
        body: Tag

        if (
            len(content) == 1
            and isinstance(content[0], Tag)
            and cast(Tag, content[0]).name == "html"
        ):
            html = cast(Tag, content[0])
            html.attrs.update(**self._html_attr_args)
            html = html.tagify()
            html = HTMLDocument._hoist_head_content(html, lib_prefix, include_version)
            return html

        if (
            len(content) == 1
            and isinstance(content[0], Tag)
            and cast(Tag, content[0]).name == "body"
        ):
            body = cast(Tag, content[0])
        else:
            body = Tag("body", content)

        body = body.tagify()

        html = Tag("html", Tag("head"), body, **self._html_attr_args)
        html = HTMLDocument._hoist_head_content(html, lib_prefix, include_version)
        return html

    # Given an <html> tag object, copies the top node, then extracts dependencies from
    # the tree, and inserts the content from those dependencies into the <head>, such as
    # <link> and <script> tags.
    @staticmethod
    def _hoist_head_content(
        x: Tag, lib_prefix: Optional[str], include_version: bool
    ) -> Tag:
        if x.name != "html":
            raise ValueError(f"Expected <html> tag, got <{x.name}>.")

        res = copy(x)

        # <head> needs to be a direct child of <html>, but not necessarily the first
        # child (it would be suprising if you weren't able to, for example, have a
        # HTMLDependency() as the first child of <html>).
        head_index: Optional[int] = None
        for i, child in enumerate(res.children):
            if isinstance(child, Tag) and child.name == "head":
                head_index = i
                break

        if head_index is None:
            res.insert(0, Tag("head"))
            head_index = 0

        res.children[head_index] = copy(res.children[head_index])
        head = cast(Tag, res.children[head_index])
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


# =============================================================================
# HTML strings
# =============================================================================
class HTML(str):
    """
    Mark a string as raw HTML. This will prevent the string from being escaped when
    rendered inside an HTML tag.

    Example
    -------
    >>> from htmltools import HTML, div
    >>> div("<p>Hello</p>")
    <div>&lt;p&gt;Hello&lt;/p&gt;</div>
    >>> div(HTML("<p>Hello</p>"))
    <div><p>Hello</p></div>
    """

    def __str__(self) -> str:
        return self.as_string()

    # HTML() + HTML() should return HTML()
    def __add__(self, other: Union[str, "HTML"]) -> str:
        res = str.__add__(self, other)
        return HTML(res) if isinstance(other, HTML) else res

    def __repr__(self) -> str:
        return self.as_string()

    def _repr_html_(self) -> str:
        return self.as_string()

    def as_string(self) -> str:
        return self + ""


# =============================================================================
# HTML dependencies
# =============================================================================
class HTMLDependencySource(TypedDict):
    package: NotRequired[str]
    subdir: str


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

    Example
    -------
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
    source: Optional[HTMLDependencySource]
    script: List[ScriptItem]
    stylesheet: List[StylesheetItem]
    meta: List[MetaItem]
    all_files: bool
    head: Optional[TagList]

    def __init__(
        self,
        name: str,
        version: Union[str, Version],
        *,
        source: Optional[HTMLDependencySource] = None,
        script: Union[ScriptItem, List[ScriptItem]] = [],
        stylesheet: Union[StylesheetItem, List[StylesheetItem]] = [],
        all_files: bool = False,
        meta: Union[MetaItem, List[MetaItem]] = [],
        head: TagChildArg = None,
    ) -> None:
        self.name = name
        self.version = Version(version) if isinstance(version, str) else version
        self.source = source

        if isinstance(script, dict):
            script = [script]
        self._validate_dicts(script, ["src"])
        self.script = script

        if isinstance(stylesheet, dict):
            stylesheet = [stylesheet]
        self._validate_dicts(stylesheet, ["href"])
        self.stylesheet = stylesheet

        # Ensures a rel='stylesheet' default
        for s in self.stylesheet:
            if "rel" not in s:
                s["rel"] = "stylesheet"

        if isinstance(meta, dict):
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

        pkg = src.get("package", None)
        if pkg is None:
            source = os.path.realpath(src["subdir"])
        else:
            source = os.path.join(_package_dir(pkg), src["subdir"])

        href = self.name
        if include_version:
            href += "-" + str(self.version)
        href = os.path.join(lib_prefix, href) if lib_prefix else href
        return {"source": source, "href": href}

    def as_html_tags(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> TagList:
        """
        Render the dependency as a ``TagList()``.
        """
        d = self.as_dict(lib_prefix=lib_prefix, include_version=include_version)
        metas = [Tag("meta", **m) for m in self.meta]
        links = [Tag("link", **s) for s in d["stylesheet"]]
        scripts = [Tag("script", **s) for s in d["script"]]
        return TagList(*metas, *links, *scripts, self.head)

    def as_dict(
        self, *, lib_prefix: Optional[str] = "lib", include_version: bool = True
    ) -> Dict[str, Any]:
        """
        Returns a dict of the dependency's attributes.
        """

        paths = self.source_path_map(
            lib_prefix=lib_prefix, include_version=include_version
        )

        stylesheets = deepcopy(self.stylesheet)
        for s in stylesheets:
            href = urllib.parse.quote(s["href"])
            s.update(
                {
                    "href": os.path.join(paths["href"], href),
                    "rel": "stylesheet",
                }
            )

        scripts = deepcopy(self.script)
        for s in scripts:
            src = urllib.parse.quote(s["src"])
            s.update({"src": os.path.join(paths["href"], src)})

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
            src_files = list(Path(paths["source"]).glob("*"))
            src_files = [str(x) for x in src_files]
        else:
            src_files = [
                *[s["src"] for s in self.script],
                *[s["href"] for s in self.stylesheet],
            ]

        # Verify they all exist
        for f in src_files:
            src_file = os.path.join(paths["source"], f)
            if not os.path.isfile(src_file):
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
            shutil.copy2(src_file, target_file)

    def _validate_dicts(self, ld: Iterable[object], req_attr: List[str] = []) -> None:
        for d in ld:
            self._validate_dict(d, req_attr)

    def _validate_dict(self, d: object, req_attr: List[str] = []) -> None:
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


def _resolve_dependencies(deps: List[HTMLDependency]) -> List[HTMLDependency]:
    map: Dict[str, HTMLDependency] = {}
    for dep in deps:
        if dep.name not in map:
            map[dep.name] = dep
        else:
            if dep.version > map[dep.name].version:
                map[dep.name] = dep

    return list(map.values())


def head_content(*args: TagChildArg) -> HTMLDependency:
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

    Example
    -------
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


# =============================================================================
# Utility functions
# =============================================================================

# Convert a list of TagChildArg objects to a list of TagChild objects. Does not alter
# input object.
def _tagchildargs_to_tagchilds(x: Iterable[TagChildArg]) -> List[TagChild]:
    result = _flatten(x)
    for i, child in enumerate(result):
        if isinstance(child, (int, float)):
            result[i] = str(child)
        elif not isinstance(child, (Tagifiable, Tag, MetadataNode, str)):
            raise TypeError(
                f"Invalid tag child type: {type(child)}. "
                + "Consider calling str() on this value before treating it as a tag child."
            )

    # At this point, we know that all items in new_children must be valid TagChild
    # objects, because None, int, float, and TagList objects have been removed. (Note
    # that the TagList objects that have been flattened are TagList which are NOT
    # tags.)
    return cast(List[TagChild], result)


def _tag_show(
    self: Union[TagList, "Tag"],
    renderer: Literal["auto", "ipython", "browser"] = "auto",
) -> object:
    if renderer == "auto":
        try:
            import IPython

            ipy = IPython.get_ipython()  # type: ignore
            renderer = "ipython" if ipy else "browser"
        except ImportError:
            renderer = "browser"

    # TODO: can we get htmlDependencies working in IPython?
    if renderer == "ipython":
        from IPython.core.display import display_html

        # https://github.com/ipython/ipython/pull/10962
        return display_html(
            str(self), raw=True, metadata={"text/html": {"isolated": True}}
        )  # type: ignore

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


def _normalize_text(txt: str) -> str:
    if isinstance(txt, HTML):
        return txt
    else:
        return _html_escape(txt, attr=False)


def _equals_impl(x: Any, y: Any) -> bool:
    if not isinstance(y, type(x)):
        return False
    for key in x.__dict__.keys():
        if getattr(x, key, None) != getattr(y, key, None):
            return False
    return True

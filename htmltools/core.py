import os
import sys
import shutil
import tempfile
from pathlib import Path
from copy import copy, deepcopy
from urllib.parse import quote
import webbrowser
from datetime import date, datetime
from typing import (
    Iterable,
    Optional,
    Union,
    List,
    Dict,
    Callable,
    Any,
    TypeVar,
    cast,
)

if sys.version_info >= (3, 8):
    from typing import TypedDict, SupportsIndex, Protocol, runtime_checkable
else:
    from typing_extensions import TypedDict, SupportsIndex, Protocol, runtime_checkable

from packaging.version import parse as version_parse
from packaging.version import Version

from .util import (
    unique,
    ensure_http_server,
    package_dir,
    _normalize_attr_name,  # type: ignore
    _html_escape,  # type: ignore
    _flatten,  # type: ignore
)

__all__ = (
    "TagList",
    "Tag",
    "HTMLDocument",
    "html",
    "HTMLDependency",
    "TagAttrArg",
    "TagChildArg",
    "TagChild",
    "TagFunction",
)


class RenderedHTML(TypedDict):
    dependencies: List["HTMLDependency"]
    html: str


T = TypeVar("T")

TagT = TypeVar("TagT", bound="Tag")

# Types of objects that can be a child of a tag.
TagChild = Union["Tagifiable", "Tag", "HTMLDependency", str]

# Types that can be passed as args to TagList() and tag functions.
TagChildArg = Union[TagChild, "TagList", int, float, None, Iterable["TagChildArg"]]

# Types that can be passed in as attributes to tag functions.
TagAttrArg = Union[str, int, float, date, datetime, bool, None]


# Objects with tagify() methods are considered Tagifiable.
@runtime_checkable
class Tagifiable(Protocol):
    def tagify(self) -> Union["Tag", "HTMLDependency", str]:
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
# TagList
# =============================================================================
class TagList(List[TagChild]):
    def __init__(self, *args: TagChildArg) -> None:
        super().__init__(_tagchildargs_to_tagchilds(args))

    def extend(self, x: Iterable[TagChildArg]) -> None:
        super().extend(_tagchildargs_to_tagchilds(x))

    def append(self, *args: TagChildArg) -> None:  # type: ignore
        # Note that if x is a list or tag_list, it could be flattened into a list of
        # TagChildArg or TagChild objects, and the list.append() method only accepts one
        # item, so we need to wrap it into a list and send it to .extend().
        self.extend(args)

    def insert(self, index: SupportsIndex, x: TagChildArg) -> None:
        self[index:index] = _tagchildargs_to_tagchilds([x])

    def tagify(self) -> "TagList":
        cp = copy(self)
        for i, child in enumerate(cp):
            if isinstance(child, Tagifiable):
                cp[i] = child.tagify()
            elif isinstance(child, HTMLDependency):
                cp[i] = copy(child)
        return cp

    def walk(
        self,
        pre: Optional[Callable[[TagChild], TagChild]] = None,
        post: Optional[Callable[[TagChild], TagChild]] = None,
    ) -> "TagList":
        """
        Walk a TagContainer tree, and apply a function to each node. The node in the
        tree will be replaced with the value returned from `pre()` or `post()`. If the
        function alters a node, then it will be reflected in the original object that
        `.walk()` was called on.
        """
        cp = copy(self)
        for i, child in enumerate(cp):
            cp[i] = _walk(child, pre, post)
        return cp

    def save_html(self, file: str, libdir: str = "lib") -> str:
        return HTMLDocument(self).save_html(file, libdir)

    def render(self) -> RenderedHTML:
        deps = self.get_dependencies()
        return {"dependencies": deps, "html": self.get_html_string()}

    def get_html_string(self, indent: int = 0, eol: str = "\n") -> "html":
        n = len(self)
        html_ = ""
        for i, x in enumerate(self):
            if isinstance(x, Tag):
                html_ += x.get_html_string(indent, eol)  # type: ignore
            elif isinstance(x, HTMLDependency):
                continue
            elif isinstance(x, Tagifiable):
                raise RuntimeError(
                    "Encountered a non-tagified object. x.tagify() must be called before x.render()"
                )
            else:
                # If we get here, x must be a string.
                html_ += ("  " * indent) + normalize_text(x)
            if i < n - 1:
                html_ += eol
        return html(html_)

    def get_dependencies(self, *, dedup: bool = True) -> List["HTMLDependency"]:
        deps: List[HTMLDependency] = []
        for x in self:
            if isinstance(x, HTMLDependency):
                deps.append(x)
            elif isinstance(x, Tag):
                # When we recurse, don't deduplicate at every node. We only need to do
                # that once, at the top level.
                deps.extend(x.get_dependencies(dedup=False))

        if dedup:
            unames = unique([d.name for d in deps])
            resolved: List[HTMLDependency] = []
            for nm in unames:
                latest = max([d.version for d in deps if d.name == nm])
                deps_ = [d for d in deps if d.name == nm]
                for d in deps_:
                    if d.version == latest and d not in resolved:
                        resolved.append(d)
            return resolved
        else:
            return deps

    def show(self, renderer: str = "auto") -> Any:
        _tag_show(self, renderer)

    def __str__(self) -> str:
        return self.get_html_string()

    def __eq__(self, other: Any) -> bool:
        return equals_impl(self, other)


# =============================================================================
# Tag class
# =============================================================================
class Tag:
    """
    Create an HTML tag.

    Methods:
    --------
        show: Render and preview as HTML.
        save_html: Save the HTML to a file.
        append: Add children (or attributes) _after_ any existing children (or attributes).
        insert: Add children (or attributes) into a specific child (or attribute) index.
        get_attrs: Get a dictionary of attributes.
        get_attr: Get the value of an attribute.
        has_attr: Check if an attribute is present.
        has_class: Check if the class attribte contains a particular class.
        render: Render the tag as HTML.

    Attributes:
    -----------
        name: The name of the tag
        children: A list of children

     Examples:
    ---------
        >>> print(div(h1('Hello htmltools'), tags.p('for python'), class_ = 'mydiv'))
        >>> print(tag("MyJSXComponent"))
    """

    def __init__(
        self,
        _name: str,
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> None:
        self.children: TagList = TagList()
        self.name: str = _name
        self.attrs: Dict[str, str] = {}

        self.children.extend(args)
        if children:
            self.children.extend(children)

        self.set_attr(**kwargs)
        # http://dev.w3.org/html5/spec/single-page.html#void-elements
        self._is_void = _name in [
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
        ]

    def __call__(self, *args: TagChildArg, **kwargs: TagAttrArg) -> "Tag":
        self.children.extend(args)
        self.set_attr(**kwargs)
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
        self.children.insert(index, x)

    def extend(self, x: Iterable[TagChildArg]) -> None:
        self.children.extend(x)

    def append(self, *args: TagChildArg) -> None:
        self.children.append(*args)

    def get_attr(self, key: str) -> Optional[str]:
        return self.attrs.get(key)

    def set_attr(self, **kwargs: TagAttrArg) -> None:
        for key, val in kwargs.items():
            if val is None or val is False:
                continue
            elif val is True:
                val = ""
            elif isinstance(val, html):
                # If it's html, make sure not to call str() on it, because we want to
                # preserve the html class wrapper.
                pass
            else:
                val = str(val)

            key = _normalize_attr_name(key)
            self.attrs[key] = val

    def has_attr(self, key: str) -> bool:
        return _normalize_attr_name(key) in self.attrs

    def add_class(self, x: str) -> "Tag":
        if "class" in self.attrs:
            self.attrs["class"] += " " + x
        else:
            self.attrs["class"] = x
        return self

    def has_class(self, class_: str) -> bool:
        attr = self.attrs.get("class", None)
        if attr is None:
            return False
        return class_ in attr.split(" ")

    def walk(
        self: TagChild,
        pre: Optional[Callable[[TagChild], TagChild]] = None,
        post: Optional[Callable[[TagChild], TagChild]] = None,
    ) -> TagChild:
        """
        Walk a TagContainer tree, and apply a function to each node. The node in the
        tree will be replaced with the value returned from `pre()` or `post()`. If the
        function alters a node, then it will be reflected in the original object that
        `.walk()` was called on.
        """
        return _walk(self, pre, post)

    def tagify(self: TagT) -> TagT:
        # TODO: Does this result in extra copies of the NodeList?
        cp = copy(self)
        cp.children = cp.children.tagify()
        return cp

    def get_html_string(self, indent: int = 0, eol: str = "\n") -> "html":
        indent_str = "  " * indent
        html_ = indent_str + "<" + self.name

        # Write attributes
        for key, val in self.attrs.items():
            if not isinstance(val, html):
                val = _html_escape(val)
            html_ += f' {key}="{val}"'

        # Dependencies are ignored in the HTML output
        children = [x for x in self.children if not isinstance(x, HTMLDependency)]

        # Don't enclose JSX/void elements if there are no children
        if len(children) == 0 and self._is_void:
            return html(html_ + "/>")

        # Other empty tags are enclosed
        html_ += ">"
        close = "</" + self.name + ">"
        if len(children) == 0:
            return html(html_ + close)

        # Inline a single/empty child text node
        if len(children) == 1 and isinstance(children[0], str):
            return html(html_ + normalize_text(children[0]) + close)

        # Write children
        # TODO: inline elements should eat ws?
        html_ += eol
        html_ += self.children.get_html_string(indent + 1, eol)
        return html(html_ + eol + indent_str + close)

    def render(self) -> RenderedHTML:
        deps = self.get_dependencies()
        return {"dependencies": deps, "html": self.get_html_string()}

    def save_html(self, file: str, libdir: str = "lib") -> str:
        return HTMLDocument(self).save_html(file, libdir)

    def get_dependencies(self, dedup: bool = True) -> List["HTMLDependency"]:
        return self.children.get_dependencies(dedup=dedup)

    def show(self, renderer: str = "auto") -> Any:
        _tag_show(self, renderer)

    def __str__(self) -> str:
        return self.get_html_string()

    def __repr__(self) -> str:
        return tag_repr_impl(self.name, self.attrs, self.children)

    def __eq__(self, other: Any) -> bool:
        return equals_impl(self, other)


# =============================================================================
# Document class
# =============================================================================
class HTMLDocument:
    """
    Create an HTML document.

    Examples:
    ---------
        >>> print(HTMLDocument(h1("Hello"), tags.meta(name="description", content="test"), lang = "en"))
    """

    def __init__(
        self,
        *args: TagChildArg,
        **kwargs: TagAttrArg,
    ) -> None:
        self.html: Tag

        if len(args) == 1 and isinstance(args[0], Tag) and args[0].name == "html":
            self.html = args[0]
            return

        if len(args) == 1 and isinstance(args[0], Tag) and args[0].name == "body":
            body = args[0]
        else:
            body = Tag("body", *args)

        head = Tag("head", _extract_head_content(body))
        self.html = Tag("html", head, body, **kwargs)

    def render(self) -> RenderedHTML:
        res = HTMLDocument._insert_head_content(self.html)
        rendered = res.render()
        rendered["html"] = "<!DOCTYPE html>\n" + rendered["html"]
        return rendered

    def save_html(self, file: str, libdir: str = "lib") -> str:
        # Copy dependencies to libdir (relative to the file)
        dir = str(Path(file).resolve().parent)
        libdir = os.path.join(dir, libdir)

        def copy_dep(d: TagChild) -> TagChild:
            if isinstance(d, HTMLDependency):
                d = d.copy_to(libdir, False)
                d = d.make_relative(dir, False)
            return d

        res = self.html.tagify()
        res.walk(copy_dep)
        res = HTMLDocument._insert_head_content(res)
        rendered = res.render()
        rendered["html"] = "<!DOCTYPE html>\n" + rendered["html"]
        with open(file, "w") as f:
            f.write(rendered["html"])
        return file

    @staticmethod
    def _insert_head_content(x: Tag) -> Tag:
        deps: List[HTMLDependency] = x.get_dependencies()
        res = copy(x)
        res.children[0] = copy(res.children[0])
        head = cast(Tag, res.children[0])
        head.insert(
            0, [Tag("meta", charset="utf-8"), *[d.as_html_tags() for d in deps]]
        )
        return res


# Given a Tag object, extract content that is inside of <head> tags, and return it in a
# TagList.
def _extract_head_content(x: Tag) -> TagList:
    head_content: TagList = TagList()

    # Given a TagChild, remove all <head> tags, recursively.
    def remove_head_content(item: TagChild) -> TagChild:
        if isinstance(item, Tag):
            for i, child in enumerate(item.children):
                if isinstance(child, Tag) and child.name == "head":
                    head_content.append(child)
                    item.children.pop(i)
        return item

    x.walk(remove_head_content)
    return head_content


# =============================================================================
# HTML strings
# =============================================================================
class html(str):
    """
    Mark a string as raw HTML.

    Example:
    -------
    >>> print(div("<p>Hello</p>"))
    >>> print(div(html("<p>Hello</p>")))
    """

    def __new__(cls, *args: str) -> "html":
        return super().__new__(cls, "\n".join(args))

    def __str__(self) -> "html":
        return html(self)

    # html() + html() should return html()
    def __add__(self, other: Union[str, "html"]) -> str:
        res = str.__add__(self, other)
        return html(res) if isinstance(other, html) else res


# =============================================================================
# HTML dependencies
# =============================================================================
class HTMLDependency:
    """
    Create an HTML dependency.

    Example:
    -------
    >>> x = div("foo", HTMLDependency(name = "bar", version = "1.0", src = ".", script = "lib/bar.js"))
    >>> x.render()
    """

    def __init__(
        self,
        name: str,
        version: Union[str, Version],
        src: Union[str, Dict[str, str]],
        script: Optional[Union[str, List[str], List[Dict[str, str]]]] = None,
        stylesheet: Optional[Union[str, List[str], List[Dict[str, str]]]] = None,
        package: Optional[str] = None,
        all_files: bool = False,
        meta: Optional[List[Dict[str, str]]] = None,
        head: Optional[str] = None,
    ) -> None:
        self.name: str = name
        self.version: Version = (
            version if isinstance(version, Version) else version_parse(version)
        )
        self.src: Dict[str, str] = src if isinstance(src, dict) else {"file": src}
        self.script: List[Dict[str, str]] = self._as_dicts(script, "src")
        self.stylesheet: List[Dict[str, str]] = self._as_dicts(stylesheet, "href")
        # Ensures a rel='stylesheet' default
        for i, s in enumerate(self.stylesheet):
            if "rel" not in s:
                self.stylesheet[i].update({"rel": "stylesheet"})
        self.package: Optional[str] = package
        self.all_files: bool = all_files
        self.meta: List[Dict[str, str]] = meta if meta else []
        self.head: Optional[str] = head

    # I don't think we need hrefFilter (seems rmarkdown was the only one that needed
    # it)?
    # https://github.com/search?l=r&q=%22hrefFilter%22+user%3Acran+language%3AR&ref=searchresults&type=Code&utf8=%E2%9C%93
    #
    # This method is used to get an HTML tag representation of the HTMLDependency
    # object. It is _not_ used by `tagify()`; instead, it's used when generating HEAD
    # content for HTML.
    def as_html_tags(
        self, src_type: Optional[str] = None, encode_path: Callable[[str], str] = quote
    ) -> TagList:
        # Prefer the first listed src type if not specified
        if not src_type:
            src_type = list(self.src.keys())[0]

        src = self.src.get(src_type, None)
        if not src:
            raise Exception(
                f"HTML dependency {self.name}@{self.version} has no '{src_type}' definition"
            )

        # Assume href is already URL encoded
        src = encode_path(src) if src_type == "file" else src

        sheets = deepcopy(self.stylesheet)
        for s in sheets:
            s.update({"href": os.path.join(src, encode_path(s["href"]))})

        script: List[Dict[str, str]] = deepcopy(self.script)
        for s in script:
            s.update({"src": os.path.join(src, encode_path(s["src"]))})

        metas: List[Tag] = [Tag("meta", **m) for m in self.meta]
        links: List[Tag] = [Tag("link", **s) for s in sheets]
        scripts: List[Tag] = [Tag("script", **s) for s in script]
        head = html(self.head) if self.head else None
        return TagList(*metas, *links, *scripts, head)

    def copy_to(self, path: str, must_work: bool = True) -> "HTMLDependency":
        src = self.src["file"]
        version = str(self.version)
        if not src:
            if must_work:
                raise Exception(
                    f"Failed to copy HTML dependency {self.name}@{version} to {path} because its local source directory doesn't exist"
                )
            else:
                return self
        if not path or path == "/":
            raise Exception("path cannot be empty or '/'")

        if self.package:
            src = os.path.join(package_dir(self.package), src)

        # Collect all the source files
        if self.all_files:
            src_files = list(Path(src).glob("*"))
        else:
            src_files = _flatten(
                [[s["src"] for s in self.script], [s["href"] for s in self.stylesheet]]
            )

        # setup the target directory
        # TODO: add option to exclude version
        target = os.path.join(path, self.name + "@" + version)
        if os.path.exists(target):
            shutil.rmtree(target)
        Path(target).mkdir(parents=True, exist_ok=True)

        # copy all the files
        for f in src_files:
            src_f = os.path.join(src, f)
            if not os.path.isfile(src_f):
                raise Exception(
                    f"Failed to copy HTML dependency {self.name}@{version} to {path} because {src_f} doesn't exist"
                )
            tgt_f = os.path.join(target, f)
            os.makedirs(os.path.dirname(tgt_f), exist_ok=True)
            shutil.copy2(src_f, tgt_f)

        # return a new instance of this class with the new path
        kwargs = deepcopy(self.__dict__)
        kwargs["src"]["file"] = str(Path(target).resolve())
        return HTMLDependency(**kwargs)

    def make_relative(self, path: str, must_work: bool = True) -> "HTMLDependency":
        src = self.src["file"]
        if not src:
            if must_work:
                raise Exception(
                    f"Failed to make HTML dependency {self.name}@{self.version} files relative to {path} since a local source directory doesn't exist"
                )
            else:
                return self

        src = Path(src)
        if not src.is_absolute():
            raise Exception(
                "Failed to make HTML dependency {self.name}@{self.version} relative because its local source directory is not already absolute (call .copy_to() before .make_relative())"
            )

        kwargs = deepcopy(self.__dict__)
        kwargs["src"]["file"] = str(src.relative_to(Path(path).resolve()))
        return HTMLDependency(**kwargs)

    def _as_dicts(self, val: Any, attr: str) -> List[Dict[str, str]]:
        if val is None:
            return []
        if isinstance(val, str):
            return [{attr: val}]
        if isinstance(val, list):
            return [{attr: i} if isinstance(i, str) else i for i in val]
        raise Exception(
            f"Invalid type for {repr(val)} in HTML dependency {self.name}@{self.version}"
        )

    def __repr__(self):
        return f'<HTMLDependency "{self.name}@{self.version}">'

    def __str__(self):
        return str(self.as_html_tags())

    def __eq__(self, other: Any) -> bool:
        return equals_impl(self, other)


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

    # At this point, we know that all items in new_children must be valid TagChild
    # objects, because None, int, float, and TagList objects have been removed. (Note
    # that the TagList objects that have been flattened are TagList which are NOT
    # tags.)
    return cast(List[TagChild], result)


def _walk(
    x: TagChild,
    pre: Optional[Callable[[TagChild], TagChild]] = None,
    post: Optional[Callable[[TagChild], TagChild]] = None,
) -> TagChild:
    if pre:
        x = pre(x)

    if isinstance(x, Tag):
        for i, child in enumerate(x.children):
            x.children[i] = _walk(child, pre, post)

    if post:
        x = post(x)

    return x


def _tag_show(self: Union[TagList, "Tag"], renderer: str = "auto") -> Any:
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


def tag_repr_impl(name: str, attrs: Dict[str, str], children: TagList) -> str:
    x = "<" + name
    n_attrs = len(attrs)
    if attrs.get("id"):
        x += "#" + attrs["id"]
        n_attrs -= 1
    if attrs.get("class"):
        x += "." + attrs["class"].replace(" ", ".")
        n_attrs -= 1
    x += " with "
    if n_attrs > 0:
        x += f"{n_attrs} other attributes and "
    n = len(children)
    x += "1 child>" if n == 1 else f"{n} children>"
    return x


def normalize_text(txt: str) -> str:
    if isinstance(txt, html):
        return txt
    else:
        return _html_escape(txt, attr=False)


def equals_impl(x: Any, y: Any) -> bool:
    if not isinstance(y, type(x)):
        return False
    for key in x.__dict__.keys():
        if getattr(x, key, None) != getattr(y, key, None):
            return False
    return True

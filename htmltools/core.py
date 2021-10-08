import os
import sys
import shutil
import tempfile
import re
from pathlib import Path
from copy import copy, deepcopy
from urllib.parse import quote
import webbrowser
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
    from typing import TypedDict, Protocol, runtime_checkable
else:
    from typing_extensions import TypedDict, Protocol, runtime_checkable

from packaging.version import parse as version_parse
from packaging.version import Version

from .util import (
    unique,
    ensure_http_server,
    package_dir,
    _encode_attr_name,  # type: ignore
    _html_escape,  # type: ignore
)

__all__ = (
    "tag_list",
    "tag",
    "html_document",
    "html",
    "html_dependency",
    "TagAttr",
    "TagChildArg",
    "TagChild",
)

T = TypeVar("T")

TagListT = TypeVar("TagListT", bound="tag_list")

# Types of objects that can be a child of a tag.
TagChild = Union["Tagifiable", "tag", "html_dependency", str]

# A duck type: objects with tagify() methods are considered Tagifiable.
@runtime_checkable
class Tagifiable(Protocol):
    def tagify(self) -> Union["tag_list", "tag", "html_dependency", str]:
        ...


# Types that can be passed as args to tag_list() and tag functions.
TagChildArg = Union[TagChild, "tag_list", int, float, None, List["TagChildArg"]]


class RenderedHTML(TypedDict):
    dependencies: List["html_dependency"]
    html: str


class tag_list:
    """
    Create a list (i.e., fragment) of HTML content

    Methods:
    --------
        show: Render and preview as HTML.
        save_html: Save the HTML to a file.
        append: Add content _after_ any existing children.
        insert: Add content after a given child index.
        tagify: Recursively convert all children to tag or tag-like objects, of type
          RenderedTagChild.
        render: Render the tag tree as an HTML string and also retrieve any dependencies.

    Attributes:
    -----------
        children: A list of child tags.

    Examples:
    ---------
        >>> print(tag_list(h1('Hello htmltools'), tags.p('for python')))
    """

    def __init__(self, *args: TagChildArg) -> None:
        self.children: List[TagChild] = []
        self.extend(args)

    def __copy__(self: TagListT) -> TagListT:
        cls = self.__class__
        cp = cls.__new__(cls)
        # Any instance fields (like .children, and _attrs for the tag subclass) are
        # shallow-copied.
        new_dict = {key: copy(value) for key, value in self.__dict__.items()}
        cp.__dict__.update(new_dict)
        return cp

    def extend(self, x: Iterable[TagChildArg]) -> None:
        self.children.extend(_tagchildargs_to_tagchilds(x))

    def append(self, *args: TagChildArg) -> None:
        self.extend(args)

    def insert(self, index: int = 0, *args: TagChildArg) -> None:
        self.children.insert(index, *_tagchildargs_to_tagchilds(args))

    def tagify(self: TagListT) -> TagListT:
        # Make a shallow copy, then recurse into children. We don't want to make a deep
        # copy, because then each time it recursed, it would create an unnecessary deep
        # copy. Additionally, children that aren't tag objects (but which have a
        # tagify() method which would return a tag object) might be unnecessarily
        # copied.
        cp = copy(self)
        for i, child in enumerate(cp.children):
            if isinstance(child, Tagifiable):
                cp.children[i] = child.tagify()
            elif isinstance(child, html_dependency):
                cp.children[i] = copy(child)
        return cp

    def walk(
        self,
        pre: Optional[Callable[[TagChild], TagChild]] = None,
        post: Optional[Callable[[TagChild], TagChild]] = None,
    ) -> TagChild:
        return _walk(self, pre, post)

    def render(self) -> RenderedHTML:
        deps = self._get_dependencies()
        return {"dependencies": deps, "html": self._get_html_string()}

    def save_html(self, file: str, libdir: str = "lib") -> str:
        return html_document(self).save_html(file, libdir)

    def _get_html_string(self, indent: int = 0, eol: str = "\n") -> "html":
        n = len(self.children)
        html_ = ""
        for i, x in enumerate(self.children):
            if isinstance(x, tag):
                html_ += x._get_html_string(indent, eol)  # type: ignore
            elif isinstance(x, html_dependency):
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

    def _get_dependencies(self) -> List["html_dependency"]:
        deps: List[html_dependency] = []
        for x in self.children:
            if isinstance(x, html_dependency):
                deps.append(x)
            elif isinstance(x, tag):
                deps.extend(x._get_dependencies())

        unames = unique([d.name for d in deps])
        resolved: List[html_dependency] = []
        for nm in unames:
            latest = max([d.version for d in deps if d.name == nm])
            deps_ = [d for d in deps if d.name == nm]
            for d in deps_:
                if d.version == latest and d not in resolved:
                    resolved.append(d)
        return resolved

    def show(self, renderer: str = "auto") -> Any:
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

    def __str__(self) -> str:
        return self._get_html_string()

    def __eq__(self, other: Any) -> bool:
        return equals_impl(self, other)

    def __bool__(self) -> bool:
        return len(self.children) > 0

    def __repr__(self) -> str:
        return tag_repr_impl("tag_list", {}, self.children)


from datetime import date, datetime

TagAttr = Union[str, bool, float, date, datetime, List[str], None]
TagAttrs = Dict[str, List[TagAttr]]


class tag(tag_list):
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
        **kwargs: TagAttr,
    ) -> None:
        self.children: List[TagChild] = []
        self.extend(args)
        if children:
            self.extend(children)

        self.name: str = _name
        self.attrs: Dict[str, str] = {}
        self.append(**kwargs)
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

    def __call__(self, *args: TagChildArg, **kwargs: TagAttr) -> "tag":
        self.append(*args, **kwargs)
        return self

    def append(self, *args: TagChildArg, **kwargs: TagAttr) -> None:
        if args:
            super().append(*args)
        for k, v in kwargs.items():
            v_list = _flatten(v if isinstance(v, list) else [v])
            res: List[str] = []
            for x in v_list:
                if x is False:  # _flatten() has already dropped None
                    continue
                if x is True:
                    res.append("")
                elif isinstance(x, html):
                    res.append(x)
                else:
                    res.append(_html_escape(str(x), attr=True))
            if len(res) > 0:
                k_ = _encode_attr_name(k)
                v_old = self.attrs.get(k_, None)
                v_new = " ".join(res)
                self.attrs[k_] = v_new if v_old is None else v_old + " " + v_new

    def has_attr(self, key: str) -> bool:
        return key in self.attrs

    def has_class(self, class_: str) -> bool:
        attr = self.attrs.get("class", None)
        if attr is None:
            return False
        return class_ in attr.split(" ")

    def _get_html_string(self, indent: int = 0, eol: str = "\n") -> "html":
        indent_str = "  " * indent
        html_ = indent_str + "<" + self.name

        # write attributes (boolean attributes should be empty strings)
        for key, val in self.attrs.items():
            html_ += f' {key}="{val}"'

        # Dependencies are ignored in the HTML output
        children = [x for x in self.children if not isinstance(x, html_dependency)]

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
        html_ += super()._get_html_string(indent + 1, eol)
        return html(html_ + eol + indent_str + close)

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return tag_repr_impl(self.name, self.attrs, self.children)


# --------------------------------------------------------
# Document class
# --------------------------------------------------------
class html_document(tag):
    """
    Create an HTML document.

    Examples:
    ---------
        >>> print(html_document(h1("Hello"), tags.meta(name="description", content="test"), lang = "en"))
    """

    def __init__(
        self, body: tag_list, head: Optional[tag_list] = None, **kwargs: TagAttr
    ) -> None:
        super().__init__("html", **kwargs)

        if not (isinstance(head, tag) and head.name == "head"):
            head = tag("head", head)
        if not (isinstance(body, tag) and body.name == "body"):
            body = tag("body", body)

        self.append(head, body)

    def render(self) -> RenderedHTML:
        deps: List[html_dependency] = self._get_dependencies()

        child0_children: List[TagChild] = []
        if isinstance(self.children[0], tag):
            child0_children = self.children[0].children

        head = tag(
            "head",
            tag("meta", charset="utf-8"),
            *[d.as_html_tags() for d in deps],
            *child0_children,
        )
        body = self.children[1]
        return {
            "dependencies": deps,
            "html": "<!DOCTYPE html>\n" + str(tag("html", head, body)),
        }

    def save_html(self, file: str, libdir: str = "lib") -> str:
        # Copy dependencies to libdir (relative to the file)
        dir = str(Path(file).resolve().parent)
        libdir = os.path.join(dir, libdir)

        def copy_dep(d: TagChild) -> TagChild:
            if isinstance(d, html_dependency):
                d = d.copy_to(libdir, False)
                d = d.make_relative(dir, False)
            return d

        res = self.tagify()
        res.walk(copy_dep)
        res = res.render()
        with open(file, "w") as f:
            f.write(res["html"])
        return file


# --------------------------------------------------------
# html strings
# --------------------------------------------------------
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


# --------------------------------------------------------
# html dependencies
# --------------------------------------------------------
class html_dependency:
    """
    Create an HTML dependency.

    Example:
    -------
    >>> x = div("foo", html_dependency(name = "bar", version = "1.0", src = ".", script = "lib/bar.js"))
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
    # This method is used to get an HTML tag representation of the html_dependency
    # object. It is _not_ used by `tagify()`; instead, it's used when generating HEAD
    # content for HTML.
    def as_html_tags(
        self, src_type: Optional[str] = None, encode_path: Callable[[str], str] = quote
    ) -> tag_list:
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

        metas: List[tag] = [tag("meta", **m) for m in self.meta]
        links: List[tag] = [tag("link", **s) for s in sheets]
        scripts: List[tag] = [tag("script", **s) for s in script]
        head = html(self.head) if self.head else None
        return tag_list(*metas, *links, *scripts, head)

    def copy_to(self, path: str, must_work: bool = True) -> "html_dependency":
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
        return html_dependency(**kwargs)

    def make_relative(self, path: str, must_work: bool = True) -> "html_dependency":
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
        return html_dependency(**kwargs)

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
        return f'<html_dependency "{self.name}@{self.version}">'

    def __str__(self):
        return str(self.as_html_tags())

    def __eq__(self, other: Any) -> bool:
        return equals_impl(self, other)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

# Walk a tag_list tree, and apply a function to each node. The node in the tree will be
# replaced with the value returned from `pre()` or `post()`. Note that the
def _walk(
    x: TagChild,
    pre: Optional[Callable[[TagChild], TagChild]] = None,
    post: Optional[Callable[[TagChild], TagChild]] = None,
) -> TagChild:
    if pre:
        x = pre(x)

    if isinstance(x, tag_list):
        for i, child in enumerate(x.children):
            x.children[i] = _walk(child, pre, post)

    if post:
        x = post(x)

    return x


# Convert a list of TagChildArg objects to a list of TagChild objects. Does not alter
# input object.
def _tagchildargs_to_tagchilds(x: Iterable[TagChildArg]) -> List[TagChild]:
    result = _flatten(x, taglist_=True)
    for i, child in enumerate(result):
        if isinstance(child, (int, float)):
            result[i] = str(child)

    # At this point, we know that all items in new_children must be valid TagChild
    # objects, because None, int, float, and tag_list objects have been removed. (Note
    # that the tag_list objects that have been flattened are tag_lists which are NOT
    # tags.)
    return cast(List[TagChild], result)


# Flatten a arbitrarily nested list and remove None. Does not alter input object.
#  - taglist_: if True, also flatten objects with class tag_list (but not subclasses
#    like objects with class tag).
#
# Note that this function is in this file instead of util.py because the tag_list check
# would result in a circular dependency.
def _flatten(x: Iterable[Union[T, None]], taglist_: bool = False) -> List[T]:
    result: List[T] = []
    _flatten_recurse(x, result, taglist_)  # type: ignore
    return result


# Having this separate function and passing along `result` is faster than defining
# a closure inside of `flatten()` (and not passing `result`).
def _flatten_recurse(
    x: Iterable[Union[T, None]], result: List[T], taglist_: bool = False
) -> None:
    for item in x:
        if isinstance(item, (list, tuple)):
            # Don't yet know how to specify recursive generic types, so we'll tell
            # the type checker to ignore this line.
            _flatten_recurse(item, result, taglist_)  # type: ignore
        elif taglist_ and type(item) == tag_list:
            _flatten_recurse(item.children, result, taglist_)  # type: ignore
        elif item is not None:
            result.append(item)


def tag_repr_impl(name: str, attrs: Dict[str, str], children: List[TagChild]) -> str:
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

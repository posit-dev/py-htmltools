from typing import Callable, Iterable, List, Dict, Union, Optional, Any, cast, Tuple
import copy
import re

from .core import (
    TagList,
    TagAttrArg,
    Tag,
    TagChild,
    TagChildArg,
    Tagifiable,
    html,
    MetadataNode,
    HTMLDependency,
)
from .versions import versions

__all__ = (
    "jsx",
    "jsx_tag_create",
    "JSXTag",
)


class JSXTag:
    def __init__(
        self,
        _name: str,
        *args: TagChildArg,
        allowedProps: Optional[List[str]] = None,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: object,
    ) -> None:
        if allowedProps:
            for k in kwargs.keys():
                if k not in allowedProps:
                    raise NotImplementedError(f"{k} is not a valid prop for {_name}")

        self.children: TagList = TagList()
        self.name: str = _name
        # Unlike HTML tags, JSX tag attributes can be anything.
        self.attrs: Dict[str, object] = {}

        self.children.extend(args)
        if children:
            self.children.extend(children)

        self.set_attr(**kwargs)

    def extend(self, x: Iterable[TagChildArg]) -> None:
        self.children.extend(x)

    def append(self, *args: TagChildArg) -> None:
        self.children.append(*args)

    def get_attr(self, key: str) -> Any:
        return self.attrs.get(key)

    def set_attr(self, **kwargs: object) -> None:
        for key, val in kwargs.items():
            key = _normalize_jsx_attr_name(key)
            # Parse CSS strings into a dict (because React requires it)
            if key == "style" and isinstance(val, str):
                val = cast(
                    List[Tuple[str, str]],
                    [tuple(x.split(":")) for x in val.split(";") if re.search(":", x)],
                )
                val = dict(val)
            self.attrs[key] = val

    def has_attr(self, key: str) -> bool:
        return _normalize_jsx_attr_name(key) in self.attrs

    def tagify(self) -> Tag:
        metadata_nodes: List[MetadataNode] = []

        # This function is recursively applied to the attributes and children. It does
        # two things: For attrs/children that are Tagifiable but NOT Tags or JSXTags, it
        # calls .tagify(), so that we have a fully tagified tree. Then it collects any
        # metadata nodes. This could be done in two separate passes, but it's more
        # efficient to do it in one pass.
        def tagify_tagifiable_and_get_metadata(x: Any) -> Any:
            if isinstance(x, Tagifiable) and not isinstance(x, (Tag, JSXTag)):
                x = x.tagify()
            else:
                x = copy.copy(x)
            if isinstance(x, MetadataNode):
                metadata_nodes.append(x)
            return x

        cp = copy.copy(self)
        _walk_attrs_and_children(cp, tagify_tagifiable_and_get_metadata)

        # When _render_react_js()  is called on a JSXTag object, we'll recurse, but
        # instead of calling the standard Tag.get_html_string() method to format the
        # object, we'll recurse using _render_react_js(), which descends into the tree
        # and formats objects appropriately for inside of a JSX element.
        js = "\n".join(
            [
                "(function() {",
                "  var container = new DocumentFragment();",
                "  ReactDOM.render(",
                _render_react_js(self, 2, "\n"),
                "  , container);",
                "  document.currentScript.after(container);",
                "})();",
            ]
        )

        return Tag(
            "script",
            type="text/javascript",
            children=[
                html("\n" + js + "\n"),
                _lib_dependency("react", script={"src": "react.production.min.js"}),
                _lib_dependency(
                    "react-dom", script={"src": "react-dom.production.min.js"}
                ),
                *metadata_nodes,
            ],
        )

    def __str__(self) -> str:
        return str(self.tagify())


def _walk_attrs_and_children(x: Any, fn: Callable[[Any], Any]) -> Any:
    x = fn(x)

    if isinstance(x, Tag):
        for i, child in enumerate(x.children):
            x.children[i] = _walk_attrs_and_children(child, fn)
    elif isinstance(x, JSXTag):
        for key, value in x.attrs.items():
            x.attrs[key] = _walk_attrs_and_children(value, fn)
        for i, child in enumerate(x.children):
            x.children[i] = _walk_attrs_and_children(child, fn)
    elif isinstance(x, Tagifiable):
        # Don't do anything here?
        pass

    return x


# Return a string representing the rendered HTML for the given JSXTag object. The
# metadata_nodes object collects MetadataNode objects in the tree, and is altered by
# reference as a side-effect of this function.
def _render_react_js(x: TagChild, indent: int, eol: str) -> str:
    indent_str = "  " * indent

    if isinstance(x, MetadataNode):
        return ""
    elif isinstance(x, str):
        return indent_str + '"' + x.replace('"', '\\"') + '"'

    if isinstance(x, JSXTag):
        nm = x.name
    elif isinstance(x, Tag):
        nm = "'" + x.name + "'"
    else:
        raise TypeError("x must be a tag or JSXTag object. Did you run tagify()?")

    res: str = indent_str + "React.createElement("

    if len(x.attrs) == 0 and len(x.children) == 0:
        return res + nm + ")"

    res += f"{eol}{indent_str}  {nm}, "

    res += "{"
    is_first_attr = True
    for k, v in x.attrs.items():
        if not is_first_attr:
            res += ", "
        is_first_attr = False
        v = _serialize_attr(v)
        res += f'"{k}": {v}'
    res += "}"

    if len(x.children) == 0:
        return res + ")"

    for child in x.children:
        child_str = _render_react_js(child, indent + 1, eol)
        if child_str != "":
            res += "," + eol + child_str

    return res + eol + indent_str + ")"


# Unfortunately we can't use json.dumps() here because I don't know how to
# avoid quoting jsx(), jsx_tag(), tag(), etc.
def _serialize_attr(x: object) -> str:
    if x is None:
        return "null"
    if isinstance(x, Tag) or isinstance(x, JSXTag):
        return _render_react_js(x, 0, "\n")
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join([_serialize_attr(y) for y in x]) + "]"
    if isinstance(x, dict):
        return "{" + ", ".join([y + ": " + _serialize_attr(x[y]) for y in x]) + "}"
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, (jsx, int, float)):
        return str(x)
    return '"' + str(x).replace('"', '\\"') + '"'


def _normalize_jsx_attr_name(x: str) -> str:
    if x.endswith("_"):
        x = x[:-1]
    return x.replace("_", "-")


def jsx_tag_create(
    _name: str, allowedProps: Optional[List[str]] = None
) -> Callable[..., JSXTag]:
    pieces = _name.split(".")
    if pieces[-1][:1] != pieces[-1][:1].upper():
        raise NotImplementedError("JSX tags must be lowercase")

    def jsx_tag_instantiate(
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> JSXTag:
        return JSXTag(
            _name, *args, allowedProps=allowedProps, children=children, **kwargs
        )

    jsx_tag_instantiate.__name__ = _name

    return jsx_tag_instantiate


# --------------------------------------------------------
# jsx expressions
# --------------------------------------------------------
class jsx(str):
    """
    Mark a string as a JSX expression.

    Example:
    -------
    >>> Foo = jsx_tag_create("Foo")
    >>> print(Foo(prop = "A string", jsxProp = jsx("() => console.log('here')")))
    """

    def __new__(cls, *args: str) -> "jsx":
        return super().__new__(cls, "\n".join(args))

    # html() + html() should return html()
    def __add__(self, other: Union[str, "jsx"]) -> str:
        res = str.__add__(self, other)
        return jsx(res) if isinstance(other, jsx) else res


def _lib_dependency(
    pkg: str, script: Dict[str, str], **kwargs: object
) -> HTMLDependency:
    return HTMLDependency(
        name=pkg,
        version=versions[pkg],
        source={"package": "htmltools", "subdir": "lib/" + pkg},
        script=script,
        **kwargs,
    )

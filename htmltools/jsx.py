from typing import Callable, Iterable, List, Dict, Union, Optional, Any

from .core import (
    TagList,
    TagAttrArg,
    Tag,
    TagChild,
    TagChildArg,
    Tagifiable,
    html,
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
            self.attrs[key] = val

    def has_attr(self, key: str) -> bool:
        return _normalize_jsx_attr_name(key) in self.attrs

    def tagify(self) -> Tag:
        # When ._get_html_string()  is called on a JsxTag object, we'll recurse, but
        # instead of calling the standard tag._get_html_string() method to format the
        # object, we'll recurse using _get_react_html_string(), which descends into the
        # tree and formats objects appropriately for inside of a JSX element.
        js = "\n".join(
            [
                "(function() {",
                "  var container = new DocumentFragment();",
                "  ReactDOM.render(",
                _get_react_js(self, 2, "\n"),
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
            ],
        )

    def __str__(self) -> str:
        return str(self.tagify())


def _get_react_js(x: TagChild, indent: int = 0, eol: str = "\n") -> str:
    indent_str = "  " * indent

    if isinstance(x, HTMLDependency):
        raise RuntimeError("Shouldn't get here")
    elif isinstance(x, str):
        return indent_str + '"' + x.replace('"', '\\"') + '"'

    res = indent_str + "React.createElement("

    if isinstance(x, JSXTag):
        nm = x.name
    elif isinstance(x, Tag):
        nm = "'" + x.name + "'"
    else:
        raise TypeError("x must be a tag or JsxTag object. Did you run tagify()?")

    attrs = x.attrs
    children = [child for child in x.children if not isinstance(child, HTMLDependency)]

    if len(attrs) == 0 and len(children) == 0:
        return res + nm + ")"

    res += f"{eol}{indent_str}  {nm}, "

    res += "{"
    is_first_attr = True
    for k, v in attrs.items():
        if not is_first_attr:
            res += ", "
        is_first_attr = False
        v = _serialize_attr(v)
        res += f'"{k}": {v}'
    res += "}"

    if len(children) == 0:
        return res + ")"

    for child in children:
        if not (isinstance(child, Tag) or isinstance(child, JSXTag)) and isinstance(
            child, Tagifiable
        ):
            # This is for unknown Tagifiable objects (not Tag or JsxTag). One potential
            # issue is that if `child` becomes a
            child = child.tagify()
        res += "," + eol
        res += _get_react_js(child, indent + 1, eol)

    return res + eol + indent_str + ")"


# Unfortunately we can't use json.dumps() here because I don't know how to
# avoid quoting jsx(), jsx_tag(), tag(), etc.
def _serialize_attr(x: object) -> str:
    if x is None:
        return "null"
    if isinstance(x, Tag) or isinstance(x, JSXTag):
        return _get_react_js(x)
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join([_serialize_attr(y) for y in x]) + "]"
    if isinstance(x, dict):
        return "{" + ", ".join([y + ": " + _serialize_attr(x[y]) for y in x]) + "}"
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, (jsx, int, float)):
        return str(x)
    return '"' + str(x).replace('"', '\\"') + '"'


def _serialize_style_attr(x: object) -> str:
    styles: Dict[str, str] = {}
    vals = x if isinstance(x, list) else [x]
    for v in vals:
        if isinstance(v, dict):
            styles.update(v)
        elif isinstance(v, str):
            rules = [tuple(x.split(":")) for x in v.split(";")]
            styles.update(dict(rules))
        else:
            raise RuntimeError(
                "Invalid value for style attribute (must be a string or dictionary)"
            )
    return _serialize_attr(x)


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
    >>> Foo = jsx_tag("Foo")
    >>> print(Foo(myProp = "<p>Hello</p>"))
    >>> print(Foo(myProp = jsx("<p>Hello</p>")))
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

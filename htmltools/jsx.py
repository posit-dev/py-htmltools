from typing import Callable, List, Dict, Union, Optional, Any

from .core import TagAttrArg, Tag, TagChild, TagChildArg, html, HTMLDependency

from .versions import versions
from .util import _normalize_attr_name  # type: ignore

__all__ = (
    "jsx",
    "jsx_tag",
    "JsxTagAttrArg",
    "JsxTagAttrArgs",
)

JsxTagAttrArg = Union[TagAttrArg, Tag, Dict[str, Any]]
JsxTagAttrArgs = Dict[str, List[JsxTagAttrArg]]


class JsxTag(Tag):
    def __init__(
        self,
        _name: str,
        *args: TagChildArg,
        allowedProps: Optional[List[str]] = None,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> None:
        if allowedProps:
            for k in kwargs.keys():
                if k not in allowedProps:
                    raise NotImplementedError(f"{k} is not a valid prop for {_name}")

        super().__init__(_name, *args, children=children)

        # JSX attrs can be full-on JSON objects whereas html attrs
        # always get encoded as string, so use a different property to hold them
        self.jsx_attrs: JsxTagAttrArgs = {}

        # Add these html dependencies to the end, to reduce possible confusion when
        # users index into the children.
        self.append(
            _lib_dependency("react", script="react.production.min.js"),
            _lib_dependency("react-dom", script="react-dom.production.min.js"),
            **kwargs,
        )

    def append(self, *args: TagChildArg, **kwargs: JsxTagAttrArg) -> None:
        if args:
            self.extend(args)
        for k, v in kwargs.items():
            k_ = _normalize_attr_name(k)
            if not self.jsx_attrs.get(k_):
                self.jsx_attrs[k_] = []
            self.jsx_attrs[k_].append(v)

    def get_html_string(self, indent: int = 0, eol: str = "\n") -> "html":
        # When ._get_html_string()  is called on a JsxTag object, we'll recurse, but
        # instead of calling the standard tag._get_html_string() method to format the
        # object, we'll recurse using _get_react_html_string(), which descends into the
        # tree and formats objects appropriately for inside of a JSX element.
        js = "\n".join(
            [
                "(function() {",
                "  var container = new DocumentFragment();",
                "  ReactDOM.render(",
                _get_react_js(self, 2, eol),
                "  , container);",
                "  document.currentScript.after(container);",
                "})();",
            ]
        )
        html_ = Tag(
            "script", type="text/javascript", children=[html("\n" + js + "\n")]
        ).get_html_string(indent=indent)

        return html_


def _get_react_js(x: TagChild, indent: int = 0, eol: str = "\n") -> str:
    indent_str = "  " * indent

    if isinstance(x, HTMLDependency):
        raise RuntimeError("Shouldn't get here")
    elif isinstance(x, str):
        return indent_str + '"' + x.replace('"', '\\"') + '"'

    res = indent_str + "React.createElement("

    if isinstance(x, JsxTag):
        nm = x.name
    elif isinstance(x, Tag):
        nm = "'" + x.name + "'"
    else:
        raise TypeError("x must be a tag or JsxTag object. Did you run tagify()?")

    attrs = _get_jsx_attrs(x) if isinstance(x, JsxTag) else _get_html_attrs(x)
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

        v_ = v.replace(eol, "")
        res += f'"{k}": {v_}'
    res += "}"

    if len(children) == 0:
        return res + ")"

    for child in children:
        res += "," + eol
        res += _get_react_js(child, indent + 1, eol)

    return res + eol + indent_str + ")"


def _get_jsx_attrs(x: JsxTag) -> Dict[str, str]:
    res: Dict[str, str] = {}
    for key, vals in x.jsx_attrs.items():
        func = _serialize_style_attr if key == "style" else _serialize_attr
        valz = [func(v) for v in vals]
        res[key] = valz[0] if len(valz) == 1 else "[" + ", ".join(valz) + "]"
    return res


def _get_html_attrs(x: Tag) -> Dict[str, str]:
    res: Dict[str, str] = {}
    for key, val in x.attrs.items():
        func = _serialize_style_attr if key == "style" else _serialize_attr
        res[key] = func(val)
    return res


# Unfortunately we can't use json.dumps() here because I don't know how to
# avoid quoting jsx(), jsx_tag(), tag(), etc.
def _serialize_attr(x: JsxTagAttrArg) -> str:
    if x is None:
        return "null"
    if isinstance(x, Tag):
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


def _serialize_style_attr(x: JsxTagAttrArg) -> str:
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


def jsx_tag(
    _name: str, allowedProps: Optional[List[str]] = None
) -> Callable[..., JsxTag]:
    pieces = _name.split(".")
    if pieces[-1][:1] != pieces[-1][:1].upper():
        raise NotImplementedError("JSX tags must be lowercase")

    def jsx_tag_create(
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> JsxTag:
        return JsxTag(
            _name, *args, allowedProps=allowedProps, children=children, **kwargs
        )

    jsx_tag_create.__name__ = _name

    return jsx_tag_create


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


def _lib_dependency(pkg: str, **kwargs: object) -> HTMLDependency:
    return HTMLDependency(
        name=pkg, version=versions[pkg], package="htmltools", src="lib/" + pkg, **kwargs
    )

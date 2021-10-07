from typing import Callable, List, Dict, Union, Optional, Any, cast

from .core import (
    TagAttr,
    tag,
    TagChild,
    TagChildArg,
    lib_dependency,
    html,
    html_dependency,
)

__all__ = (
    "jsx",
    "jsx_tag",
    "JsxTagAttr",
    "JsxTagAttrs",
)

JsxTagAttr = Union[TagAttr, tag, Dict[str, Any]]
JsxTagAttrs = Dict[str, List[JsxTagAttr]]


class JsxTag(tag):
    def __init__(
        self,
        _name: str,
        *args: TagChildArg,
        allowedProps: Optional[List[str]] = None,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttr,
    ) -> None:

        # TODO: check allowedProps here

        super().__init__(
            _name,
            *args,
            children=children,
            **kwargs,
        )

        # Add these html dependencies to the end, to reduce possible confusion when
        # users index into the children.
        self.append(
            lib_dependency("react", script="react.production.min.js"),
            lib_dependency("react-dom", script="react-dom.production.min.js"),
        )

    def _get_html_string(self, indent: int = 0, eol: str = "\n") -> "html":
        # When ._get_html_string()  is called on a JsxTag object, we'll recurse, but
        # instead of calling the standard tag._get_html_string() method to format the
        # object, we'll recurse using _get_react_html_string(), which descends into the
        # tree and formats objects appropriately for inside of a JSX element.
        js = "\n".join(
            [
                "(function() {",
                "  var container = new DocumentFragment();",
                "  ReactDOM.render(",
                _get_react_html_string(self, indent + 1, eol),
                "  , container);",
                "  document.currentScript.after(container);",
                "})();",
            ]
        )
        html_ = tag(
            "script", type="text/javascript", children=[html("\n" + js + "\n")]
        )._get_html_string(indent=indent)

        return html_


def _get_react_html_string(x: TagChild, indent: int = 0, eol: str = "\n") -> str:
    indent_str = "  " * indent

    if isinstance(x, html_dependency):
        raise RuntimeError("Shouldn't get here")
    elif isinstance(x, str):
        return indent_str + '"' + x.replace('"', '\\"') + '"'

    res = indent_str + "React.createElement("

    if isinstance(x, JsxTag):
        res += x.name + "," + eol
    elif isinstance(x, tag):
        res += "'" + x.name + "'," + eol
    else:
        raise TypeError("x must be a tag or JsxTag object. Did you run tagify()?")

    attrs = cast(JsxTagAttrs, x._attrs)

    res += indent_str + "  " + "{"
    for key, vals in attrs.items():
        res += f'"{key}": '
        # React doesn't allow style to be a string, so convert them into objects
        if key == "style" and isinstance(vals, str):
            valz = {}
            for prop in [x.split(":") for x in vals.split(";")]:
                if len(prop) == 2:
                    valz[prop[0]] = prop[1]
            vals = valz
        # If this tag is jsx, then it should be a list (otherwise, it's a string)
        if isinstance(vals, list):
            for i, v in enumerate(vals):
                vals[i] = _serialize_attr(v)
            res += vals[0] if len(vals) == 1 else "[" + ", ".join(vals) + "]"
        else:
            res += _serialize_attr(vals)
        res += ", "
    res += "}," + eol

    for child in x.children:
        if isinstance(child, html_dependency):
            continue
        res += _get_react_html_string(child, indent + 1, eol)
        res += ", " + eol

    res += indent_str + ")"

    return res


def jsx_tag(
    _name: str, allowedProps: Optional[List[str]] = None
) -> Callable[..., JsxTag]:
    pieces = _name.split(".")
    if pieces[-1][:1] != pieces[-1][:1].upper():
        raise NotImplementedError("JSX tags must be lowercase")

    def jsx_tag_create(
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttr,
    ) -> JsxTag:
        return JsxTag(
            _name, *args, allowedProps=allowedProps, children=children, **kwargs
        )

    jsx_tag_create.__name__ = _name

    return jsx_tag_create


def _serialize_attr(x: JsxTagAttr) -> str:
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join([_serialize_attr(y) for y in x]) + "]"
    if isinstance(x, dict):
        return "{" + ", ".join([y + ": " + _serialize_attr(x[y]) for y in x]) + "}"
    if isinstance(x, jsx):
        return str(x)
    if isinstance(x, bool):
        return str(x).lower()

    return '"' + str(x).replace('"', '\\"') + '"'


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

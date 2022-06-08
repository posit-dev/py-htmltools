"""
WARNING: this is a highly experimental/unsupported/private module for JSX/React
components. Although JSXTag currently allows for HTML tags on attributes and children,
that's an issue for HTML() and <script> tags, so using normal HTML tags inside JSX
components may become unsupported in a future version (see #26 and #28)
"""

from typing import (
    Callable,
    Iterable,
    List,
    Dict,
    Mapping,
    Union,
    Optional,
    Any,
    cast,
    Tuple,
)
import copy
import re

from ._core import (
    TagList,
    TagAttrArg,
    Tag,
    TagChild,
    TagChildArg,
    Tagifiable,
    HTML,
    MetadataNode,
    HTMLDependency,
)
from ._versions import versions

# CPS 6/8/2022: this module is currently too experimental to be recommended for use.
# It's not clear that it's worth the effort to support it, and if we do, we may want to
# remove the ability to nest HTML() and <script> tags inside JSXTag/JSXTagAttrArg
__all__ = (
    # "jsx",
    # "jsx_tag_create",
    # "JSXTag",
    # "JSXTagAttrArg",
)

# A JSX tag attribute can be anything.
JSXTagAttrArg = object


class JSXTagAttrs(Dict[str, object]):
    def __init__(self, **kwargs: object) -> None:
        super().__init__()
        self.update(**kwargs)

    def __setitem__(self, name: str, value: object) -> None:
        nm = self._normalize_attr_name(name)
        super().__setitem__(nm, value)

    # Note: typing is ignored because the type checker thinks this is an incompatible
    # override. It's possible that we could find a way to override so that it's happy.
    def update(  # type: ignore
        self, __m: Mapping[str, object] = {}, **kwargs: object
    ) -> None:
        self._update(__m)
        self._update(kwargs)

    def _update(self, __m: Mapping[str, object]) -> None:
        attrs: Dict[str, object] = {}
        for key, val in __m.items():
            attrs[self._normalize_attr_name(key)] = val
        super().update(**attrs)

    @staticmethod
    def _normalize_attr_name(x: str) -> str:
        if x.endswith("_"):
            x = x[:-1]
        return x.replace("_", "-")


class JSXTag:
    """
    Create a JSX tag.

    Warning
    -------
    This class shouldn't be used directly to create a JSX tag. Instead, use the
    jsx_tag_create() function.

    See Also
    --------
    jsx_tag_create
    """

    def __init__(
        self,
        _name: str,
        *args: TagChildArg,
        allowedProps: Optional[List[str]] = None,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: object,
    ) -> None:

        pieces = _name.split(".")
        if pieces[-1][:1] != pieces[-1][:1].upper():
            raise NotImplementedError("JSX tags must be start with a capital letter.")

        if allowedProps:
            for k in kwargs.keys():
                if k not in allowedProps:
                    raise NotImplementedError(f"{k} is not a valid prop for {_name}")

        self.name: str = _name
        # Unlike HTML tags, JSX tag attributes can be anything.
        self.attrs: JSXTagAttrs = JSXTagAttrs(**kwargs)
        self.children: TagList = TagList()

        self.children.extend(args)
        if children:
            self.children.extend(children)

    def extend(self, x: Iterable[TagChildArg]) -> None:
        self.children.extend(x)

    def append(self, *args: TagChildArg) -> None:
        self.children.append(*args)

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
        component = _render_react_js(self, 2, "\n")

        # Ideally, we'd use document.currentScript.after() to insert the component
        # directly after the script tag, but when dynamically rendered via jQuery (i.e.,
        # @render_ui()), the script tag actually executes in <head>, which makes the
        # document.currentScript reference basically useless for this purpose. So,
        # instead, to make this work when dynamically rendered, this script queries for
        # the first JSXTag script that hasn't yet rendered, and insert the component
        # there. It seems like this should work fine as long as these script tags are
        # synchronously executed in order, but if we ever need them to render
        # asynchronously, it might make sense to use a unique ID for each script tag
        # instead.
        js = "\n".join(
            [
                "(function() {",
                "  var container = new DocumentFragment();",
                "  ReactDOM.render(",
                component,
                "  , container);",
                "  var thisScript = document.querySelector('script[data-needs-render]');",
                f"  if (!thisScript) throw new Error('Failed to render JSXTag(\"{self.name}\")');",
                "  thisScript.after(container);",
                "  thisScript.removeAttribute('data-needs-render');",
                "})();",
            ]
        )

        return Tag(
            "script",
            type="text/javascript",
            data_needs_render=True,
            children=[
                HTML("\n" + js + "\n"),
                _lib_dependency("react", script={"src": "react.production.min.js"}),
                _lib_dependency(
                    "react-dom", script={"src": "react-dom.production.min.js"}
                ),
                *metadata_nodes,
            ],
        )

    def __str__(self) -> str:
        return str(self.tagify())

    def __repr__(self) -> str:
        return self.__str__()

    def _repr_html_(self) -> str:
        return self.__str__()


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
        if k == "style":
            v = _serialize_style_attr(v)
        else:
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
        return "{" + ", ".join([f'"{y}": ' + _serialize_attr(x[y]) for y in x]) + "}"
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, (jsx, int, float)):
        return str(x)
    return '"' + str(x).replace('"', '\\"') + '"'


def _serialize_style_attr(x: object) -> str:
    if x is None:
        return "{}"
    # Parse CSS strings into a dict (because React requires it)
    if isinstance(x, str):
        x = cast(
            List[Tuple[str, str]],
            [tuple(y.split(":")) for y in x.split(";") if re.search(":", y)],
        )
        x = dict(x)
    if isinstance(x, dict):
        return _serialize_attr(x)
    else:
        raise TypeError("The style attribute must be a dict() or string.")


def jsx_tag_create(
    name: str, allowedProps: Optional[List[str]] = None
) -> Callable[..., JSXTag]:
    """
    Create a function that creates a JSXTag object.

    Parameters
    ----------
    name
        The name of the JSX tag (should be camelCase and start with a capital letter).
    allowedProps
        A list of allowed properties for the tag. If ``None``, all properties are
        allowed.

    Returns
    -------
    JSXTag

    Examples
    --------
    >>> from htmltools import jsx_tag_create
    >>> MyTag = jsx_tag_create("MyTag")
    >>> MyTag(id="foo", class_="bar")
    <script type="text/javascript">
    (function() {
      var container = new DocumentFragment();
      ReactDOM.render(
        React.createElement(
          MyTag, {"id": "foo", "class": "bar"})
      , container);
      document.currentScript.after(container);
    })();
    </script>
    """

    def create_tag(
        *args: TagChildArg,
        children: Optional[List[TagChildArg]] = None,
        **kwargs: TagAttrArg,
    ) -> JSXTag:
        return JSXTag(
            name, *args, allowedProps=allowedProps, children=children, **kwargs
        )

    create_tag.__name__ = name

    return create_tag


# --------------------------------------------------------
# jsx expressions
# --------------------------------------------------------
class jsx(str):
    """
    Mark a string as a JSX expression.

    Example
    -------
    >>> Foo = JSXTag("Foo")
    >>> Foo(prop = "A string", jsxProp = jsx("() => console.log('here')"))
    <script type="text/javascript">
    (function() {
      var container = new DocumentFragment();
      ReactDOM.render(
        React.createElement(
          Foo, {"prop": "A string", "jsxProp": () => console.log('here')})
      , container);
      document.currentScript.after(container);
    })();
    </script>
    """

    def __new__(cls, *args: str) -> "jsx":
        return super().__new__(cls, "\n".join(args))

    # jsx() + jsx() should return jsx()
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

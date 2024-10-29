__version__ = "0.6.0"

from . import svg, tags
from ._core import TagAttrArg  # pyright: ignore[reportUnusedImport] # noqa: F401
from ._core import TagChildArg  # pyright: ignore[reportUnusedImport] # noqa: F401
from ._core import (
    HTML,
    HTMLDependency,
    HTMLDocument,
    HTMLTextDocument,
    MetadataNode,
    RenderedHTML,
    ReprHtml,
    Tag,
    TagAttrs,
    TagAttrValue,
    TagChild,
    TagFunction,
    Tagifiable,
    TagList,
    TagNode,
    consolidate_attrs,
    head_content,
    is_tag_child,
    is_tag_node,
    wrap_displayhook_handler,
)
from ._util import css, html_escape
from .tags import (
    a,
    br,
    code,
    div,
    em,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    hr,
    img,
    p,
    pre,
    span,
    strong,
)

__all__ = (
    "svg",
    "tags",
    "HTML",
    "HTMLDependency",
    "HTMLDocument",
    "HTMLTextDocument",
    "MetadataNode",
    "RenderedHTML",
    "Tag",
    "TagAttrs",
    "TagAttrValue",
    "TagChild",
    "TagFunction",
    "Tagifiable",
    "TagList",
    "TagNode",
    "ReprHtml",
    "consolidate_attrs",
    "head_content",
    "is_tag_child",
    "is_tag_node",
    "wrap_displayhook_handler",
    "css",
    "html_escape",
    "a",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "p",
    "pre",
    "span",
    "strong",
)


import typing as _typing

# Setting this will control how HTML dependencies are rendered. Normally they are not
# visible, but if set to "json", they will be serialized as JSON in a <script> tag.
html_dependency_render_mode: _typing.Literal["json", "invisible"] = "invisible"

__version__ = "0.1.2"

from . import svg, tags
from ._core import (
    HTML,
    HTMLDependency,
    HTMLDocument,
    MetadataNode,
    RenderedHTML,
    Tag,
    TagAttrArg,
    TagChild,
    TagChildArg,
    TagFunction,
    Tagifiable,
    TagList,
    head_content,
)
from ._jsx import JSXTag, JSXTagAttrArg, jsx, jsx_tag_create
from ._util import css
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
    "jsx",
    "jsx_tag_create",
    "JSXTag",
    "JSXTagAttrArg",
    "css",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "br",
    "div",
    "span",
    "pre",
    "code",
    "img",
    "strong",
    "em",
    "hr",
    "tags",
    "svg",
)

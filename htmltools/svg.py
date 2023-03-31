# Do not edit by hand; this file is generated by ./scripts/generate_tags.py
# fmt: off

"""
Functions for creating SVG tags.
"""

from __future__ import annotations

from ._core import Tag, TagAttrs, TagAttrValue, TagChild


def a(*args: TagChild | TagAttrs, _inline: bool = True, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <a> tag.

    Creates the <a> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/a

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("a", *args, _inline=_inline, **kwargs)


def animate(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <animate> tag.

    Creates the <animate> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/animate

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("animate", *args, _inline=_inline, **kwargs)


def animateMotion(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <animateMotion> tag.

    Creates the <animateMotion> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/animateMotion

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("animateMotion", *args, _inline=_inline, **kwargs)


def animateTransform(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <animateTransform> tag.

    Creates the <animateTransform> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/animateTransform

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("animateTransform", *args, _inline=_inline, **kwargs)


def circle(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <circle> tag.

    Creates the <circle> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/circle

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("circle", *args, _inline=_inline, **kwargs)


def clipPath(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <clipPath> tag.

    Creates the <clipPath> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/clipPath

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("clipPath", *args, _inline=_inline, **kwargs)


def defs(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <defs> tag.

    Creates the <defs> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/defs

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("defs", *args, _inline=_inline, **kwargs)


def desc(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <desc> tag.

    Creates the <desc> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/desc

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("desc", *args, _inline=_inline, **kwargs)


def discard(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <discard> tag.

    Creates the <discard> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/discard

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("discard", *args, _inline=_inline, **kwargs)


def ellipse(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <ellipse> tag.

    Creates the <ellipse> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/ellipse

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("ellipse", *args, _inline=_inline, **kwargs)


def feBlend(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feBlend> tag.

    Creates the <feBlend> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feBlend

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feBlend", *args, _inline=_inline, **kwargs)


def feColorMatrix(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feColorMatrix> tag.

    Creates the <feColorMatrix> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feColorMatrix

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feColorMatrix", *args, _inline=_inline, **kwargs)


def feComponentTransfer(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feComponentTransfer> tag.

    Creates the <feComponentTransfer> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feComponentTransfer

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feComponentTransfer", *args, _inline=_inline, **kwargs)


def feComposite(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feComposite> tag.

    Creates the <feComposite> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feComposite

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feComposite", *args, _inline=_inline, **kwargs)


def feConvolveMatrix(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feConvolveMatrix> tag.

    Creates the <feConvolveMatrix> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feConvolveMatrix

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feConvolveMatrix", *args, _inline=_inline, **kwargs)


def feDiffuseLighting(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feDiffuseLighting> tag.

    Creates the <feDiffuseLighting> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feDiffuseLighting

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feDiffuseLighting", *args, _inline=_inline, **kwargs)


def feDisplacementMap(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feDisplacementMap> tag.

    Creates the <feDisplacementMap> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feDisplacementMap

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feDisplacementMap", *args, _inline=_inline, **kwargs)


def feDistantLight(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feDistantLight> tag.

    Creates the <feDistantLight> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feDistantLight

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feDistantLight", *args, _inline=_inline, **kwargs)


def feDropShadow(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feDropShadow> tag.

    Creates the <feDropShadow> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feDropShadow

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feDropShadow", *args, _inline=_inline, **kwargs)


def feFlood(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feFlood> tag.

    Creates the <feFlood> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feFlood

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feFlood", *args, _inline=_inline, **kwargs)


def feFuncA(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feFuncA> tag.

    Creates the <feFuncA> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feFuncA

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feFuncA", *args, _inline=_inline, **kwargs)


def feFuncB(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feFuncB> tag.

    Creates the <feFuncB> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feFuncB

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feFuncB", *args, _inline=_inline, **kwargs)


def feFuncG(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feFuncG> tag.

    Creates the <feFuncG> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feFuncG

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feFuncG", *args, _inline=_inline, **kwargs)


def feFuncR(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feFuncR> tag.

    Creates the <feFuncR> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feFuncR

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feFuncR", *args, _inline=_inline, **kwargs)


def feGaussianBlur(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feGaussianBlur> tag.

    Creates the <feGaussianBlur> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feGaussianBlur

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feGaussianBlur", *args, _inline=_inline, **kwargs)


def feImage(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feImage> tag.

    Creates the <feImage> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feImage

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feImage", *args, _inline=_inline, **kwargs)


def feMerge(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feMerge> tag.

    Creates the <feMerge> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feMerge

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feMerge", *args, _inline=_inline, **kwargs)


def feMergeNode(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feMergeNode> tag.

    Creates the <feMergeNode> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feMergeNode

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feMergeNode", *args, _inline=_inline, **kwargs)


def feMorphology(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feMorphology> tag.

    Creates the <feMorphology> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feMorphology

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feMorphology", *args, _inline=_inline, **kwargs)


def feOffset(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feOffset> tag.

    Creates the <feOffset> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feOffset

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feOffset", *args, _inline=_inline, **kwargs)


def fePointLight(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <fePointLight> tag.

    Creates the <fePointLight> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/fePointLight

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("fePointLight", *args, _inline=_inline, **kwargs)


def feSpecularLighting(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feSpecularLighting> tag.

    Creates the <feSpecularLighting> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feSpecularLighting

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feSpecularLighting", *args, _inline=_inline, **kwargs)


def feSpotLight(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feSpotLight> tag.

    Creates the <feSpotLight> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feSpotLight

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feSpotLight", *args, _inline=_inline, **kwargs)


def feTile(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feTile> tag.

    Creates the <feTile> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feTile

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feTile", *args, _inline=_inline, **kwargs)


def feTurbulence(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <feTurbulence> tag.

    Creates the <feTurbulence> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/feTurbulence

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("feTurbulence", *args, _inline=_inline, **kwargs)


def filter(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <filter> tag.

    Creates the <filter> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/filter

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("filter", *args, _inline=_inline, **kwargs)


def foreignObject(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <foreignObject> tag.

    Creates the <foreignObject> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/foreignObject

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("foreignObject", *args, _inline=_inline, **kwargs)


def g(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <g> tag.

    Creates the <g> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/g

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("g", *args, _inline=_inline, **kwargs)


def hatch(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <hatch> tag.

    Creates the <hatch> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/hatch

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("hatch", *args, _inline=_inline, **kwargs)


def hatchpath(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <hatchpath> tag.

    Creates the <hatchpath> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/hatchpath

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("hatchpath", *args, _inline=_inline, **kwargs)


def image(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <image> tag.

    Creates the <image> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/image

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("image", *args, _inline=_inline, **kwargs)


def line(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <line> tag.

    Creates the <line> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/line

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("line", *args, _inline=_inline, **kwargs)


def linearGradient(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <linearGradient> tag.

    Creates the <linearGradient> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/linearGradient

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("linearGradient", *args, _inline=_inline, **kwargs)


def marker(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <marker> tag.

    Creates the <marker> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/marker

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("marker", *args, _inline=_inline, **kwargs)


def mask(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <mask> tag.

    Creates the <mask> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/mask

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("mask", *args, _inline=_inline, **kwargs)


def metadata(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <metadata> tag.

    Creates the <metadata> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/metadata

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("metadata", *args, _inline=_inline, **kwargs)


def mpath(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <mpath> tag.

    Creates the <mpath> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/mpath

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("mpath", *args, _inline=_inline, **kwargs)


def path(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <path> tag.

    Creates the <path> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/path

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("path", *args, _inline=_inline, **kwargs)


def pattern(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <pattern> tag.

    Creates the <pattern> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/pattern

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("pattern", *args, _inline=_inline, **kwargs)


def polygon(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <polygon> tag.

    Creates the <polygon> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/polygon

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("polygon", *args, _inline=_inline, **kwargs)


def polyline(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <polyline> tag.

    Creates the <polyline> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/polyline

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("polyline", *args, _inline=_inline, **kwargs)


def radialGradient(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <radialGradient> tag.

    Creates the <radialGradient> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/radialGradient

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("radialGradient", *args, _inline=_inline, **kwargs)


def rect(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <rect> tag.

    Creates the <rect> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/rect

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("rect", *args, _inline=_inline, **kwargs)


def script(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <script> tag.

    Creates the <script> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/script

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("script", *args, _inline=_inline, **kwargs)


def set(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <set> tag.

    Creates the <set> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/set

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("set", *args, _inline=_inline, **kwargs)


def stop(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <stop> tag.

    Creates the <stop> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/stop

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("stop", *args, _inline=_inline, **kwargs)


def style(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <style> tag.

    Creates the <style> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/style

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("style", *args, _inline=_inline, **kwargs)


def svg(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <svg> tag.

    Creates the <svg> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/svg

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("svg", *args, _inline=_inline, **kwargs)


def switch(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <switch> tag.

    Creates the <switch> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/switch

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("switch", *args, _inline=_inline, **kwargs)


def symbol(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <symbol> tag.

    Creates the <symbol> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/symbol

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("symbol", *args, _inline=_inline, **kwargs)


def text(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <text> tag.

    Creates the <text> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/text

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("text", *args, _inline=_inline, **kwargs)


def textPath(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <textPath> tag.

    Creates the <textPath> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/textPath

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("textPath", *args, _inline=_inline, **kwargs)


def title(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <title> tag.

    Creates the <title> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/title

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("title", *args, _inline=_inline, **kwargs)


def tspan(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <tspan> tag.

    Creates the <tspan> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/tspan

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("tspan", *args, _inline=_inline, **kwargs)


def use(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <use> tag.

    Creates the <use> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/use

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("use", *args, _inline=_inline, **kwargs)


def view(*args: TagChild | TagAttrs, _inline: bool = False, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <view> tag.

    Creates the <view> SVG element. Learn more at https://developer.mozilla.org/en-US/docs/Web/SVG/Element/view

    Parameters
    ----------
    *args
        Child elements to this tag.
    _inline
        Whether this tag should be rendered as an inline tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("view", *args, _inline=_inline, **kwargs)

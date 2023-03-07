#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
from urllib.request import urlopen

tag_template = '''
def {name}(*args: TagChild | TagAttrs, **kwargs: TagAttrValue) -> Tag:
    """
    Create a <{name}> tag.

    {desc}

    Parameters
    ----------
    *args
        Child elements to this tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("{name}", *args, **kwargs)
'''


def generate_tag_code(url: str) -> str:
    with urlopen(url) as u:
        tags: list[dict[str, str]] = json.loads(u.read().decode())

    code = ""
    for x in tags:
        # TODO: still provide this, but with underscores?
        if x["name"] == "del":
            continue
        # The descriptions sometimes have multiple lines, with inconsistent indentation
        # on lines after the first. We need to make the indentation consistently four
        # spaces, or else it will confuse Sphinx when generating docs.
        if "\n" in x["desc"]:
            x["desc"] = re.sub("\n\\s+", "\n    ", x["desc"])

        code += "\n" + tag_template.format(name=x["name"], desc=x["desc"])
    return code


# TODO: change known-tags to main once this gets merged
# https://github.com/rstudio/htmltools/pull/286
base_url = "https://raw.githubusercontent.com/rstudio/htmltools/known-tags/scripts"

html_tag_code = generate_tag_code(os.path.join(base_url, "html_tags.json"))
svg_tag_code = generate_tag_code(os.path.join(base_url, "svg_tags.json"))

html_src = f'''\
# Do not edit by hand; this file is generated by ./scripts/generate_tags.py
# fmt: off

"""
Functions for creating HTML tags.
"""

from __future__ import annotations

from ._core import Tag, TagAttrs, TagAttrValue, TagChild

__all__ = (
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
)
{html_tag_code}'''

svg_src = f'''\
# Do not edit by hand; this file is generated by ./scripts/generate_tags.py
# fmt: off

"""
Functions for creating SVG tags.
"""

from __future__ import annotations

from ._core import Tag, TagAttrs, TagAttrValue, TagChild
{svg_tag_code}'''

html_src_file = os.path.join(os.path.dirname(__file__), "../htmltools/tags.py")
svg_src_file = os.path.join(os.path.dirname(__file__), "../htmltools/svg.py")

with open(html_src_file, "w") as f:
    f.write(html_src)

with open(svg_src_file, "w") as f:
    f.write(svg_src)

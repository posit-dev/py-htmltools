import os
from tempfile import TemporaryDirectory
import textwrap
from typing import Union

from htmltools import *


def saved_html(x: Union[Tag, HTMLDocument]) -> str:
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        x.save_html(f)
        return open(f, "r").read()


def test_html_document_head_hoisting():
    doc = HTMLDocument(
        div(
            "Hello,",
            tags.head(tags.script("alert('1')"), tags.style("span {color: red;}")),
            span("world", tags.head(tags.script("alert('2')"))),
        )
    )
    print(doc.render()["html"])
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script>alert('1')</script>
            <style>span {color: red;}</style>
            <script>alert('2')</script>
          </head>
          <body>
            <div>
              Hello,
              <span>world</span>
            </div>
          </body>
        </html>"""
    )
    # In this case, render()["html"] and save_html() should produce the same thing.
    # That's not always true, like when there are html dependencies.
    assert doc.render()["html"] == saved_html(doc)

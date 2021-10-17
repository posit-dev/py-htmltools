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


def test_tagify_first():
    # A Tagifiable object which returns a Tag with an HTMLDependency when `tagify()` is
    # called.
    class DelayedDep:
        dep = HTMLDependency(
            "testdep",
            "1.0",
            source={"package": "htmltools", "subdir": "libtest/testdep"},
            script={"src": "testdep.js"},
            stylesheet={"href": "testdep.css"},
        )

        def tagify(self):
            return div("delayed dependency", self.dep)

    x = TagList(div("Hello", DelayedDep()), "world")

    assert x.get_dependencies() == []
    assert x.tagify().get_dependencies() == [DelayedDep.dep]

    result = x.tagify().render()
    assert result["dependencies"] == [DelayedDep.dep]

    result = HTMLDocument(x).render()
    assert result["dependencies"] == [DelayedDep.dep]
    assert result["html"].find('<script src="testdep-1.0/testdep.js">') != -1
    assert (
        result["html"].find('<link href="testdep-1.0/testdep.css" rel="stylesheet"/>')
        != -1
    )

    result = HTMLDocument(x).render(lib_prefix="mylib")
    assert result["dependencies"] == [DelayedDep.dep]
    assert result["html"].find('<script src="mylib/testdep-1.0/testdep.js">') != -1
    assert (
        result["html"].find(
            '<link href="mylib/testdep-1.0/testdep.css" rel="stylesheet"/>'
        )
        != -1
    )

    # When save_html() is called, check content and make sure dependency files are
    # copied to the right place.
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        x.save_html(f)

        html = open(f, "r").read()
        html.find('<script src="testdep-1.0/testdep.js">') != -1
        assert (
            html.find('<link href="testdep-1.0/testdep.css" rel="stylesheet"/>') != -1
        )

        testdep_files = os.listdir(os.path.join(tmpdir, "testdep-1.0"))
        testdep_files.sort()
        assert testdep_files == ["testdep.css", "testdep.js"]

    # Same as previous, except save_html() is called with a different libdir.
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        x.save_html(f, "mylib")

        html = open(f, "r").read()
        html.find('<script src="mylib/testdep-1.0/testdep.js">') != -1
        assert (
            html.find('<link href="mylib/testdep-1.0/testdep.css" rel="stylesheet"/>')
            != -1
        )

        testdep_files = os.listdir(os.path.join(tmpdir, "mylib", "testdep-1.0"))
        testdep_files.sort()
        assert testdep_files == ["testdep.css", "testdep.js"]

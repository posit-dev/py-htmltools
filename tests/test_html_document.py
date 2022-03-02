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


def test_html_document_html_input():
    # HTMLDocument with an <html> tag.
    doc = HTMLDocument(
        tags.html(
            tags.head(tags.title("Title")),
            tags.body(div("Body content"), head_content("abcd")),
            myattr="value",
        ),
        lang="en",
    )
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html myattr="value" lang="en">
          <head>
            <meta charset="utf-8"/>
            <title>Title</title>
            <script type="application/html-dependencies">headcontent_88d4266fd4e6338d13b845fcf289579d209c897823b9217da3e161936f031589[0.0]</script>
            abcd
          </head>
          <body>
            <div>Body content</div>
          </body>
        </html>"""
    )

    # HTMLDocument with a <body> tag.
    doc = HTMLDocument(
        tags.body(div("Body content"), head_content("abcd")),
        lang="en",
    )
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">headcontent_88d4266fd4e6338d13b845fcf289579d209c897823b9217da3e161936f031589[0.0]</script>
            abcd
          </head>
          <body>
            <div>Body content</div>
          </body>
        </html>"""
    )

    # HTMLDocument with a TagList.
    doc = HTMLDocument(
        TagList(div("Body content"), head_content("abcd")),
        lang="en",
    )
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">headcontent_88d4266fd4e6338d13b845fcf289579d209c897823b9217da3e161936f031589[0.0]</script>
            abcd
          </head>
          <body>
            <div>Body content</div>
          </body>
        </html>"""
    )


def test_html_document_head_hoisting():
    doc = HTMLDocument(
        div(
            "Hello,",
            head_content(
                tags.script("alert('1')"),
                tags.style("span {color: red;}"),
            ),
            span("world", head_content(tags.script("alert('2')"))),
            head_content(tags.script("alert('2')")),
        )
    )

    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">headcontent_30f3d4728150b01fae1b01ebae18b85a4bef02f3181870a56e1dc7ff1f8edd1e[0.0];headcontent_6841afc257df6c2d7be0dfbc893c02ba25b805c16f224d373303fd58ba37697e[0.0]</script>
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

    result = HTMLDocument(x).render(lib_prefix=None)
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
        html.find('<script src="lib/testdep-1.0/testdep.js">') != -1
        assert (
            html.find('<link href="lib/testdep-1.0/testdep.css" rel="stylesheet"/>')
            != -1
        )

        testdep_files = os.listdir(os.path.join(tmpdir, "lib", "testdep-1.0"))
        testdep_files.sort()
        assert testdep_files == ["testdep.css", "testdep.js"]

    # Same as previous, except save_html() is called with a different libdir.
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        x.save_html(f, libdir="mylib", include_version=False)

        html = open(f, "r").read()
        html.find('<script src="mylib/testdep/testdep.js">') != -1
        assert (
            html.find('<link href="mylib/testdep/testdep.css" rel="stylesheet"/>') != -1
        )

        testdep_files = os.listdir(os.path.join(tmpdir, "mylib", "testdep"))
        testdep_files.sort()
        assert testdep_files == ["testdep.css", "testdep.js"]

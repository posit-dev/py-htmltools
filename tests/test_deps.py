import os
from tempfile import TemporaryDirectory
from typing import Union
import textwrap

from htmltools import *


def saved_html(x: Union[Tag, HTMLDocument], libdir: str = "lib") -> str:
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        x.save_html(f, libdir=libdir)
        return open(f, "r").read()


def test_dep_resolution(snapshot):
    a1_1 = HTMLDependency("a", "1.1", {"href": "/"}, script="a1.js")
    a1_2 = HTMLDependency("a", "1.2", {"href": "/"}, script="a2.js")
    a1_2_1 = HTMLDependency("a", "1.2.1", {"href": "/"}, script="a3.js")
    b1_0_0 = HTMLDependency("b", "1.0.0", {"href": "/"}, script="b1.js")
    b1_0_1 = HTMLDependency("b", "1.0.1", {"href": "/"}, script="b2.js")
    c1_0 = HTMLDependency("c", "1.0", {"href": "/"}, script="c1.js")
    test = TagList(*[a1_1, b1_0_0, b1_0_1, a1_2, a1_2_1, b1_0_0, b1_0_1, c1_0])
    assert HTMLDocument(test).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script src="lib/a-1.2.1/a3.js"></script>
            <script src="lib/b-1.0.1/b2.js"></script>
            <script src="lib/c-1.0/c1.js"></script>
          </head>
          <body></body>
        </html>"""
    )

    assert HTMLDocument(test).render(libdir="libfoo")["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script src="libfoo/a-1.2.1/a3.js"></script>
            <script src="libfoo/b-1.0.1/b2.js"></script>
            <script src="libfoo/c-1.0/c1.js"></script>
          </head>
          <body></body>
        </html>"""
    )


# Test out renderTags and findDependencies when tags are inline
def test_inline_deps(snapshot):
    a1_1 = HTMLDependency("a", "1.1", {"href": "/"}, script="a1.js")
    a1_2 = HTMLDependency("a", "1.2", {"href": "/"}, script="a2.js")
    tests = [
        TagList(a1_1, div("foo"), "bar"),
        TagList(a1_1, div("foo"), a1_2, "bar"),
        div(a1_1, div("foo"), "bar"),
        TagList([a1_1, div("foo")], "bar"),
        div([a1_1, div("foo")], "bar"),
    ]
    html_ = "\n\n".join([HTMLDocument(t).render()["html"] for t in tests])
    snapshot.assert_match(html_, "inline_deps.txt")


def test_append_deps(snapshot):
    a1_1 = HTMLDependency("a", "1.1", {"href": "/"}, script="a1.js")
    a1_2 = HTMLDependency("a", "1.2", {"href": "/"}, script="a2.js")
    b1_2 = HTMLDependency("b", "1.0", {"href": "/"}, script="b1.js")
    x = div(a1_1, b1_2)
    x.append(a1_2)
    y = div(a1_1)
    y.append([a1_2, b1_2])
    z = div()
    z.append([a1_1, b1_2])
    z.append(a1_2)
    tests = [x, y, z]
    html_ = "\n\n".join([HTMLDocument(t).render()["html"] for t in tests])
    snapshot.assert_match(html_, "append_deps.txt")


def test_script_input(snapshot):
    def fake_dep(**kwargs):
        return HTMLDependency("a", "1.0", src={"file": "srcpath"}, **kwargs)

    dep1 = fake_dep(script="js/foo bar.js", stylesheet="css/bar foo.css")
    dep2 = fake_dep(script=["js/foo bar.js"], stylesheet=["css/bar foo.css"])
    dep3 = fake_dep(
        script=[{"src": "js/foo bar.js"}], stylesheet=[{"href": "css/bar foo.css"}]
    )
    assert dep1 == dep2 == dep3
    # Make sure repeated calls to as_html() repeatedly encode
    test = TagList([dep1, dep2, dep3])
    for i in range(2):
        assert HTMLDocument(test).render()["html"] == textwrap.dedent(
            """\
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset="utf-8"/>
                <link href="lib/a-1.0/css/bar%20foo.css" rel="stylesheet"/>
                <script src="lib/a-1.0/js/foo%20bar.js"></script>
              </head>
              <body></body>
            </html>"""
        )
        print(HTMLDocument(test).render()["html"])


def test_src_and_href():
    td = HTMLDependency(
        name="test",
        version="0.0.1",
        src="libtest/testdep",  # Equivalent to {"file": "libtest/testdep"}
        package="htmltools",
        script="testdep.js",
        stylesheet="testdep.css",
    )

    td2 = HTMLDependency(
        name="testdep2",
        version="0.2.1",
        src={"href": "libtest/dep2"},
        package="htmltools",
        script="td2.js",
        stylesheet="td2.css",
    )

    doc = HTMLDocument(TagList(td))
    assert doc.render()["html"] == saved_html(doc)
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <link href="lib/test-0.0.1/testdep.css" rel="stylesheet"/>
            <script src="lib/test-0.0.1/testdep.js"></script>
          </head>
          <body></body>
        </html>"""
    )

    doc = HTMLDocument(TagList(td2))
    # assert doc.render()["html"] == saved_html(doc)  # Currently errors out
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <link href="lib/testdep2-0.2.1/td2.css" rel="stylesheet"/>
            <script src="lib/testdep2-0.2.1/td2.js"></script>
          </head>
          <body></body>
        </html>"""
    )

    doc = HTMLDocument(TagList(td, td2))
    # assert doc.render()["html"] == saved_html(doc)  # Currently errors out
    assert doc.render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <link href="lib/test-0.0.1/testdep.css" rel="stylesheet"/>
            <script src="lib/test-0.0.1/testdep.js"></script>
            <link href="lib/testdep2-0.2.1/td2.css" rel="stylesheet"/>
            <script src="lib/testdep2-0.2.1/td2.js"></script>
          </head>
          <body></body>
        </html>"""
    )

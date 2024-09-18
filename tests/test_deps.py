import tempfile
import textwrap
from pathlib import Path

from htmltools import HTMLDependency, HTMLDocument, TagList, div, tags


def test_init_errors():
    HTMLDependency("a", "1.1", source=None)

    try:
        HTMLDependency("a", "1.1", source=4)  # type: ignore
    except TypeError as e:
        assert "to be a dict" in str(e)

    try:
        HTMLDependency("a", "1.1", source={"not": "valid"})  # type: ignore
    except TypeError as e:
        assert "to have either" in str(e)


def test_dep_resolution():
    a1_1 = HTMLDependency("a", "1.1", source={"subdir": "foo"}, script={"src": "a1.js"})
    a1_2 = HTMLDependency(
        "a", "1.2", source={"href": "http://a.test.com"}, script={"src": "a2.js"}
    )
    a1_2_1 = HTMLDependency(
        "a", "1.2.1", source={"subdir": "foo"}, script={"src": "a3.js"}
    )
    b1_9 = HTMLDependency("b", "1.9", source={"subdir": "foo"}, script={"src": "b1.js"})
    b1_10 = HTMLDependency(
        "b", "1.10", source={"href": "http://b.test.com"}, script={"src": "b2.js"}
    )
    c1_0 = HTMLDependency("c", "1.0", source={"subdir": "foo"}, script={"src": "c1.js"})
    test = TagList(a1_1, b1_9, b1_10, a1_2, a1_2_1, b1_9, b1_10, c1_0)
    assert HTMLDocument(test).render(lib_prefix=None)["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">a[1.2.1];b[1.10];c[1.0]</script>
            <script src="a-1.2.1/a3.js"></script>
            <script src="http://b.test.com/b2.js"></script>
            <script src="c-1.0/c1.js"></script>
          </head>
          <body></body>
        </html>"""
    )

    assert HTMLDocument(test).render(lib_prefix="libfoo")["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">a[1.2.1];b[1.10];c[1.0]</script>
            <script src="libfoo/a-1.2.1/a3.js"></script>
            <script src="http://b.test.com/b2.js"></script>
            <script src="libfoo/c-1.0/c1.js"></script>
          </head>
          <body></body>
        </html>"""
    )


# Test out renderTags and findDependencies when tags are inline
def test_inline_deps(snapshot):
    a1_1 = HTMLDependency("a", "1.1", source={"subdir": "foo"}, script={"src": "a1.js"})
    a1_2 = HTMLDependency("a", "1.2", source={"subdir": "foo"}, script={"src": "a2.js"})
    tests = [
        TagList(a1_1, div("foo"), "bar"),
        TagList(a1_1, div("foo"), a1_2, "bar"),
        div(a1_1, div("foo"), "bar"),
        TagList([a1_1, div("foo")], "bar"),
        div([a1_1, div("foo")], "bar"),
    ]
    html_ = "\n\n".join(
        [HTMLDocument(t).render(lib_prefix=None)["html"] for t in tests]
    )
    assert html_ == snapshot


def test_append_deps():
    a1_1 = HTMLDependency("a", "1.1", source={"subdir": "foo"}, script={"src": "a1.js"})
    a1_2 = HTMLDependency(
        "a", "1.2", source={"href": "http://foo.com"}, script={"src": "a2.js"}
    )
    b1_0 = HTMLDependency("b", "1.0", source={"subdir": "foo"}, script={"src": "b1.js"})

    expected_result = textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">a[1.2];b[1.0]</script>
            <script src="http://foo.com/a2.js"></script>
            <script src="b-1.0/b1.js"></script>
          </head>
          <body>
            <div></div>
          </body>
        </html>"""
    )

    x = div(a1_1, b1_0)
    x.append(a1_2)
    assert HTMLDocument(x).render(lib_prefix=None)["html"] == expected_result

    y = div(a1_1)
    y.append([a1_2, b1_0])
    assert HTMLDocument(y).render(lib_prefix=None)["html"] == expected_result

    z = div()
    z.append([a1_1, b1_0])
    z.append(a1_2)
    assert HTMLDocument(z).render(lib_prefix=None)["html"] == expected_result


def test_script_input():
    def fake_dep(**kwargs):
        return HTMLDependency(
            "a", "1.0", source={"package": None, "subdir": "srcpath"}, **kwargs
        )

    dep1 = fake_dep(
        script={"src": "js/foo bar.js"}, stylesheet={"href": "css/bar foo.css"}
    )
    dep2 = fake_dep(
        script=[{"src": "js/foo bar.js"}], stylesheet=[{"href": "css/bar foo.css"}]
    )
    assert dep1 == dep2
    # Make sure repeated calls to as_html() repeatedly encode
    test = TagList([dep1, dep2])
    for _ in range(2):
        assert HTMLDocument(test).render()["html"] == textwrap.dedent(
            """\
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset="utf-8"/>
                <script type="application/html-dependencies">a[1.0]</script>
                <link href="lib/a-1.0/css/bar%20foo.css" rel="stylesheet"/>
                <script src="lib/a-1.0/js/foo%20bar.js"></script>
              </head>
              <body></body>
            </html>"""
        )


def test_head_output():
    a = HTMLDependency(
        "a",
        "1.0",
        source={"subdir": "foo"},
        head=tags.script("1 && 1"),
    )
    assert a.as_html_tags().get_html_string() == "<script>1 && 1</script>"

    b = HTMLDependency(
        "a",
        "1.0",
        source={"subdir": "foo"},
        head="<script>1 && 1</script>",
    )
    assert b.as_html_tags().get_html_string() == "<script>1 && 1</script>"

    assert (
        b.serialize_to_script_json(indent=4).get_html_string()
        == """<script type="application/json" data-html-dependency="">{
    "name": "a",
    "version": "1.0",
    "source": {
        "subdir": "foo"
    },
    "script": [],
    "stylesheet": [],
    "meta": [],
    "all_files": false,
    "head": "<script>1 && 1<\\/script>"
}</script>"""
    )


def test_meta_output():
    a = HTMLDependency(
        "a",
        "1.0",
        source={"subdir": "foo"},
        script={"src": "a1.js"},
        meta={"name": "viewport", "content": "width=device-width, initial-scale=1"},
    )

    b = HTMLDependency(
        "b",
        "2.0",
        source={"subdir": "foo"},
        meta=[{"name": "x", "content": "x-value"}, {"name": "y", "content": "y-value"}],
    )

    assert str(a.as_html_tags()) == textwrap.dedent(
        """\
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <script src="lib/a-1.0/a1.js"></script>"""
    )
    assert str(b.as_html_tags()) == textwrap.dedent(
        """\
        <meta name="x" content="x-value"/>
        <meta name="y" content="y-value"/>"""
    )

    # Combine the two in an HTMLDocument and render; all meta tags should show up.
    combined_html = HTMLDocument(TagList(a, b)).render()["html"]
    assert (
        combined_html.find(
            '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
        )
        != -1
    )
    assert combined_html.find('<meta name="x" content="x-value"/>') != -1
    assert combined_html.find('<meta name="y" content="y-value"/>') != -1


def test_source_dep_as_dict():
    a = HTMLDependency(
        "a",
        "1.0",
        source={"package": "htmltools", "subdir": "bar"},
        script={"src": "a1.js"},
        meta={"name": "viewport", "content": "width=device-width, initial-scale=1"},
    )
    assert a.as_dict() == {
        "name": "a",
        "version": "1.0",
        "script": [{"src": "lib/a-1.0/a1.js"}],
        "stylesheet": [],
        "meta": [
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
        "head": None,
    }

    b = HTMLDependency(
        "b",
        "2.0",
        source={"package": "htmltools", "subdir": "bar"},
        stylesheet=[{"href": "b1.css"}, {"href": "b2.css"}],
        head=tags.script("1 && 1"),
    )
    assert b.as_dict(lib_prefix=None) == {
        "name": "b",
        "version": "2.0",
        "script": [],
        "stylesheet": [
            {"href": "b-2.0/b1.css", "rel": "stylesheet"},
            {"href": "b-2.0/b2.css", "rel": "stylesheet"},
        ],
        "meta": [],
        "head": "<script>1 && 1</script>",
    }


def test_url_dep_as_dict():
    u = HTMLDependency(
        "u",
        "1.1",
        source={"href": "https://example.com"},
        script={"src": "u1.js"},
        stylesheet={"href": "u1.css"},
        meta={"name": "viewport", "content": "width=device-width, initial-scale=1"},
    )
    assert u.as_dict() == {
        "name": "u",
        "version": "1.1",
        "script": [{"src": "https://example.com/u1.js"}],
        "stylesheet": [{"href": "https://example.com/u1.css", "rel": "stylesheet"}],
        "meta": [
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
        "head": None,
    }

    v = HTMLDependency(
        "v",
        "2.1",
        source={"href": "https://test.com/subdir/trailing/slash/"},
        stylesheet=[{"href": "v1.css"}, {"href": "v2.css"}],
        head=tags.script("1 && 1"),
    )
    assert v.as_dict(lib_prefix=None) == {
        "name": "v",
        "version": "2.1",
        "script": [],
        "stylesheet": [
            {
                "href": "https://test.com/subdir/trailing/slash/v1.css",
                "rel": "stylesheet",
            },
            {
                "href": "https://test.com/subdir/trailing/slash/v2.css",
                "rel": "stylesheet",
            },
        ],
        "meta": [],
        "head": "<script>1 && 1</script>",
    }


def test_copy_to():
    with tempfile.TemporaryDirectory() as tmpdir1:
        dep1 = HTMLDependency(
            "w",
            "1.0",
            source={"package": "htmltools", "subdir": "libtest/testdep"},
            all_files=True,
        )
        dep1.copy_to(tmpdir1)
        assert (Path(tmpdir1) / "w-1.0" / "testdep.css").exists()
        assert (Path(tmpdir1) / "w-1.0" / "testdep.js").exists()

    with tempfile.TemporaryDirectory() as tmpdir2:
        dep2 = HTMLDependency(
            "w",
            "1.0",
            source={"package": "htmltools", "subdir": "libtest/testdep"},
            all_files=False,
        )
        dep2.copy_to(tmpdir2)
        assert not (Path(tmpdir2) / "w-1.0" / "testdep.css").exists()
        assert not (Path(tmpdir2) / "w-1.0" / "testdep.js").exists()

    with tempfile.TemporaryDirectory() as tmpdir3:
        dep3 = HTMLDependency(
            "w",
            "1.0",
            source={"package": "htmltools", "subdir": "libtest/testdep"},
            stylesheet={"href": "testdep.css"},
            all_files=False,
        )
        dep3.copy_to(tmpdir3)
        assert (Path(tmpdir3) / "w-1.0" / "testdep.css").exists()
        assert not (Path(tmpdir3) / "w-1.0" / "testdep.js").exists()

    with tempfile.TemporaryDirectory() as tmpdir4:
        dep4 = HTMLDependency(
            "w",
            "1.0",
            source={"package": "htmltools", "subdir": "libtest/testdep"},
            stylesheet={"href": "testdep.css"},
            script={"src": "testdep.js"},
            all_files=False,
        )
        dep4.copy_to(tmpdir4)
        assert (Path(tmpdir4) / "w-1.0" / "testdep.css").exists()
        assert (Path(tmpdir4) / "w-1.0" / "testdep.js").exists()

    with tempfile.TemporaryDirectory() as tmpdir5:
        path_testdep_nested = Path(__file__).parent / "assets" / "testdep-nested"
        dep5 = HTMLDependency(
            "w",
            "1.0",
            source={"subdir": str(path_testdep_nested)},
            all_files=True,
        )
        dep5.copy_to(tmpdir5)
        assert (Path(tmpdir5) / "w-1.0" / "css" / "my-styles.css").exists()
        assert (Path(tmpdir5) / "w-1.0" / "js" / "my-js.js").exists()

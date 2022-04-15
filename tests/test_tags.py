import os
import copy
from tempfile import TemporaryDirectory
from typing import Any, Union, Callable
import textwrap

from htmltools import *


def expect_html(x: Any, expected: str):
    assert str(x) == expected


def saved_html(x: Union[Tag, HTMLDocument], **kwargs) -> str:
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        x.save_html(f, **kwargs)
        return open(f, "r").read()


def test_basic_tag_api():
    children = [
        h1("hello"),
        h2("world"),
        "text",
        1,
        2.1,
        None,
        ["list", ["here"]],
    ]
    props = dict(class_="foo", for_="bar", id="baz", bool="")
    x1 = div(*children, **props)
    x2 = div(**props, children=children)
    x3 = div(**props)(*children)
    x4 = div()
    x4.append(*children)
    x4.attrs.update(**props)
    assert x1 == x2 == x3 == x4
    assert x1.attrs["id"] == "baz"
    assert x1.attrs["bool"] == ""
    assert str(x1) == textwrap.dedent(
        """\
        <div class="foo" for="bar" id="baz" bool="">
          <h1>hello</h1>
          <h2>world</h2>
          text
          1
          2.1
          list
          here
        </div>"""
    )
    assert x1.attrs["class"] == "foo"
    x1.add_class("bar")
    assert x1.attrs["class"] == "foo bar"
    assert x1.has_class("foo") and x1.has_class("bar") and not x1.has_class("missing")
    x5 = TagList()
    x5.append(a())
    x5.insert(0, span())
    expect_html(x5, "<span></span>\n<a></a>")


def test_tag_attrs_update():
    # Update with dict
    x = div(a=1)
    x.attrs.update({"b": "2", "c": "C"})
    assert x.attrs == {"a": "1", "b": "2", "c": "C"}

    # Update with kwargs
    x = div(a=1)
    x.attrs.update(b=2, c="C")
    assert x.attrs == {"a": "1", "b": "2", "c": "C"}

    # Update with dict and kwargs
    x = div(a=1)
    x.attrs.update({"b": "2"}, c="C")
    assert x.attrs == {"a": "1", "b": "2", "c": "C"}


def test_tag_multiple_repeated_attrs():
    x = div({"class": "foo", "class_": "bar"}, class_="baz")
    y = div({"class": "foo"}, {"class_": "bar"}, class_="baz")
    z = div({"class": "foo"}, {"class": "bar"}, class_="baz")
    w = div({"class": "foo"}, children=[{"class_": "bar"}], class_="baz")
    assert x.attrs == {"class": "foo bar baz"}
    assert y.attrs == {"class": "foo bar baz"}
    assert z.attrs == {"class": "foo bar baz"}
    assert w.attrs == {"class": "foo bar baz"}
    x.attrs.update({"class": "bap", "class_": "bas"}, class_="bat")
    assert x.attrs == {"class": "bap bas bat"}
    x.attrs.update({"class": HTML("&")}, class_=HTML("<"))
    assert str(x) == '<div class="& <"></div>'
    x.attrs.update({"class": HTML("&")}, class_="<")
    # Combining HTML() with non-HTML() currently forces everything to be escaped,
    # but it'd be good to change this behavior if we can manage to change it
    # in general https://github.com/rstudio/py-htmltools/issues/15
    assert str(x) == '<div class="&amp; &lt;"></div>'


def test_tag_shallow_copy():
    dep = HTMLDependency(
        "a", "1.1", source={"package": None, "subdir": "foo"}, script={"src": "a1.js"}
    )
    x = div(tags.i("hello", prop="value"), "world", dep, class_="myclass")
    y = copy.copy(x)
    y.children[0].children[0] = "HELLO"
    y.children[0].attrs["prop"] = "VALUE"
    y.children[1] = "WORLD"
    y.attrs["class"] = "MYCLASS"
    y.children[2].name = "A"

    # With a shallow copy(), the .attrs and .children are shallow copies, but if a
    # child is modified in place, then the the original child is modified as well.
    assert x is not y
    assert x.attrs == {"class": "myclass"}
    assert x.children is not y.children
    # If a mutable child is modified in place, both x and y see the changes.
    assert x.children[0] is y.children[0]
    assert x.children[0].children[0] == "HELLO"
    # Immutable children can't be changed in place.
    assert x.children[1] is not y.children[1]
    assert x.children[1] == "world"
    assert x.children[1] is not y.children[1]
    # An HTMLDependency is mutable, so it is modified in place.
    assert x.children[2].name == "A"
    assert y.children[2].name == "A"
    assert x.children[2] is y.children[2]


def test_tagify_deep_copy():
    # Each call to .tagify() should do a shallow copy, but since it recurses, the result
    # is a deep copy.
    dep = HTMLDependency(
        "a", "1.1", source={"package": None, "subdir": "foo"}, script={"src": "a1.js"}
    )
    x = div(tags.i("hello", prop="value"), "world", dep, class_="myclass")

    y = x.tagify()
    y.children[0].children[0] = "HELLO"
    y.children[0].attrs["prop"] = "VALUE"
    y.children[1] = "WORLD"
    y.attrs["class"] = "MYCLASS"
    y.children[2].name = "A"

    assert x.attrs == {"class": "myclass"}
    assert y.attrs == {"class": "MYCLASS"}
    assert x.children[0].attrs == {"prop": "value"}
    assert y.children[0].attrs == {"prop": "VALUE"}
    assert x.children[0].children[0] == "hello"
    assert y.children[0].children[0] == "HELLO"
    assert x.children[1] == "world"
    assert y.children[1] == "WORLD"
    assert x.children[2].name == "a"
    assert y.children[2].name == "A"
    assert x.children[2] is not y.children[2]


def test_tag_writing():
    expect_html(TagList("hi"), "hi")
    expect_html(TagList("one", "two", TagList("three")), "one\ntwo\nthree")
    expect_html(tags.b("one"), "<b>one</b>")
    expect_html(tags.b("one", "two"), "<b>\n  one\n  two\n</b>")
    expect_html(TagList(["one"]), "one")
    expect_html(TagList([TagList("one")]), "one")
    expect_html(TagList(tags.br(), "one"), "<br/>\none")
    assert str(
        tags.b("one", "two", span("foo", "bar", span("baz")))
    ) == textwrap.dedent(
        """\
            <b>
              one
              two
              <span>
                foo
                bar
                <span>baz</span>
              </span>
            </b>"""
    )
    expect_html(tags.area(), "<area/>")


def test_tag_repr():
    assert repr(div()) == str(div())
    assert repr(div("foo", "bar", id="id")) == str(div("foo", "bar", id="id"))
    assert repr(div(id="id", class_="cls", foo="bar")) == str(
        div(id="id", class_="cls", foo="bar")
    )


def test_tag_escaping():
    # Regular text is escaped
    expect_html(div("<a&b>"), "<div>&lt;a&amp;b&gt;</div>")
    # Children wrapped in HTML() isn't escaped
    expect_html(div(HTML("<a&b>")), "<div><a&b></div>")
    # Attributes are HTML escaped
    expect_html(div("text", class_="<a&b>"), '<div class="&lt;a&amp;b&gt;">text</div>')
    expect_html(div("text", class_="'ab'"), '<div class="&apos;ab&apos;">text</div>')
    # Unless they are wrapped in HTML()
    expect_html(div("text", class_=HTML("<a&b>")), '<div class="<a&b>">text</div>')

    # script and style tags are not escaped
    assert str(tags.script("a && b > 3")) == "<script>a && b > 3</script>"
    assert (
        str(tags.script("a && b", "x > 3")) == "<script>\n  a && b\n  x > 3\n</script>"
    )
    assert str(tags.script("a && b\nx > 3")) == "<script>a && b\nx > 3</script>"
    assert str(tags.style("a && b > 3")) == "<style>a && b > 3</style>"


def test_html_save():
    assert saved_html(div()) == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
          </head>
          <body>
            <div></div>
          </body>
        </html>"""
    )

    dep = HTMLDependency(
        "foo",
        "1.0",
        source={"package": "htmltools", "subdir": "libtest"},
        stylesheet={"href": "testdep/testdep.css"},
        script={"src": "testdep/testdep.js"},
    )
    assert saved_html(div("foo", dep), libdir="") == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">foo[1.0]</script>
            <link href="foo-1.0/testdep/testdep.css" rel="stylesheet"/>
            <script src="foo-1.0/testdep/testdep.js"></script>
          </head>
          <body>
            <div>foo</div>
          </body>
        </html>"""
    )

    doc = HTMLDocument(
        div("foo", dep), tags.meta(name="description", content="test"), lang="en"
    )
    assert saved_html(doc) == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">foo[1.0]</script>
            <link href="lib/foo-1.0/testdep/testdep.css" rel="stylesheet"/>
            <script src="lib/foo-1.0/testdep/testdep.js"></script>
          </head>
          <body>
            <div>foo</div>
            <meta name="description" content="test"/>
          </body>
        </html>"""
    )


# Walk a Tag tree, and apply a function to each node. The node in the tree will be
# replaced with the value returned from `fn()`. If the function alters a node, then it
# will be reflected in the original object that `.walk_mutate()` was called on.
#
# Note that if we were to export this function (perhaps in a class method), some other
# possible variants are:
# * Instead of one `fn`, take `pre` and `post` functions.
# * Allow functions that return `TagChildArg`, and then flatten/convert those to
#   `TagChild`.
# * Provide a `_walk` function that doesn't mutate the tree. It would return `None`, and
#   `fn` should return `None`. This could be useful when `fn` just collects things from
#   the tree.
def _walk_mutate(x: TagChild, fn: Callable[[TagChild], TagChild]) -> TagChild:
    x = fn(x)
    if isinstance(x, Tag):
        for i, child in enumerate(x.children):
            x.children[i] = _walk_mutate(child, fn)
    elif isinstance(x, list):
        for i, child in enumerate(x):
            x[i] = _walk_mutate(child, fn)
    return x


def test_tag_walk():
    # walk() alters the tree in place, and also returns the altered object.
    x = div("hello ", tags.i("world"))
    y = div("The value of x is: ", x)

    def alter(x: TagChild) -> TagChild:
        if isinstance(x, str):
            return x.upper()
        elif isinstance(x, Tag):
            x.attrs["a"] = "foo"
            if x.name == "i":
                x.name = "b"

        return x

    res = _walk_mutate(x, alter)

    assert y.children[1] is x
    assert x is res

    assert x.attrs.get("a") == "foo"
    assert x.children[0] == "HELLO "
    assert x.children[1].name == "b"
    assert x.children[1].attrs.get("a") == "foo"
    assert x.children[1].children[0] == "WORLD"


def test_taglist_flatten():
    x = div(1, TagList(2, TagList(span(3), 4)))
    assert list(x.children) == ["1", "2", span("3"), "4"]

    x = TagList(1, TagList(2, TagList(span(3), 4)))
    assert list(x) == ["1", "2", span("3"), "4"]


def test_taglist_insert():
    x = TagList(1, 2, 3, 4)
    x.insert(2, "new")
    assert list(x) == ["1", "2", "new", "3", "4"]

    x = TagList(1, 2, 3, 4)
    x.insert(2, TagList("new"))
    assert list(x) == ["1", "2", "new", "3", "4"]

    x = TagList(1, 2, 3, 4)
    x.insert(2, TagList("new", "new2"))
    assert list(x) == ["1", "2", "new", "new2", "3", "4"]


def test_taglist_tagifiable():
    # When a TagList contains a Tagifiable object which returns a TagList, make sure it
    # gets flattened into the original TagList.
    class Foo:
        def __init__(self, *args) -> None:
            self._content = TagList(*args)

        def tagify(self) -> TagList:
            return self._content.tagify()

    x = TagList(1, Foo(), 2)
    assert list(x.tagify()) == ["1", "2"]

    x = TagList(1, Foo("foo"), 2)
    assert list(x.tagify()) == ["1", "foo", "2"]

    x = TagList(1, Foo("foo", span("bar")), 2)
    assert list(x.tagify()) == ["1", "foo", span("bar"), "2"]

    # Recursive tagify()
    x = TagList(1, Foo("foo", Foo("bar")), 2)
    assert list(x.tagify()) == ["1", "foo", "bar", "2"]

    # Make sure it works for Tag objects as well.
    x = div(1, Foo("foo", Foo("bar")), 2)
    assert list(x.tagify().children) == ["1", "foo", "bar", "2"]


def test_attr_vals():
    attrs = {
        "none": None,
        "false": False,
        "true": True,
        "str": "a",
        "int": 1,
        "float": 1.2,
    }
    test = TagList(div(**attrs), div(class_="foo").add_class("bar"))

    assert (
        str(test)
        == """<div true="" str="a" int="1" float="1.2"></div>
<div class="foo bar"></div>"""
    )


def test_tag_normalize_attr():
    x = div(class_="class_", x__="x__", x_="x_", x="x")
    assert x.attrs == {"class": "class_", "x-": "x__", "x": "x_ x"}

    x = div(foo_bar="baz")
    assert x.attrs == {"foo-bar": "baz"}


def test_metadata_nodes_gone():
    # Make sure MetadataNodes don't result in a blank line.
    assert str(div(span("Body content"), head_content("abc"))) == textwrap.dedent(
        """\
        <div>
          <span>Body content</span>
        </div>"""
    )

    assert (
        str(TagList(span("Body content"), MetadataNode()))
        == "<span>Body content</span>"
    )

import copy
import os
import textwrap
from tempfile import TemporaryDirectory
from typing import Any, Callable, Union, cast

import pytest

from htmltools import (
    HTML,
    HTMLDependency,
    HTMLDocument,
    MetadataNode,
    Tag,
    TagFunction,
    TagList,
    TagNode,
    a,
    div,
    h1,
    h2,
    head_content,
    span,
    tags,
)


def cast_tag(x: Any) -> Tag:
    assert isinstance(x, Tag)
    return x


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
    x1 = div(*children, _add_ws=div().add_ws, **props)
    x2 = div()
    x2.append(*children)
    x2.attrs.update(**props)
    assert x1 == x2
    assert x1.attrs["id"] == "baz"
    assert x1.attrs["bool"] == ""
    assert str(x1) == textwrap.dedent(
        """\
        <div class="foo" for="bar" id="baz" bool="">
          <h1>hello</h1>
          <h2>world</h2>
          text12.1listhere
        </div>"""
    )
    assert x1.attrs["class"] == "foo"
    x1.add_class("bar")
    assert x1.attrs["class"] == "foo bar"
    x1.add_class("baz", prepend=True)
    assert x1.attrs["class"] == "baz foo bar"
    assert (
        x1.has_class("baz")
        and x1.has_class("foo")
        and x1.has_class("bar")
        and not x1.has_class("missing")
    )
    # Add odd white space
    x1.attrs["class"] = " " + str(x1.attrs["class"]) + " "
    x1.remove_class(" foo")  # leading space
    assert x1.has_class("bar") and not x1.has_class("foo") and x1.has_class("baz")
    x1.remove_class("baz ")  # trailing space
    assert x1.attrs["class"] == "bar"
    x1.remove_class("  bar ")  # lots of white space
    assert "class" not in x1.attrs.keys()

    x3 = TagList()
    x3.append(a())
    x3.insert(0, span())
    expect_html(x3, "<span></span><a></a>")

    x4 = div()

    x4.add_style(None)  # type: ignore[reportGeneralTypeIssues]
    x4.add_style(False)  # type: ignore[reportGeneralTypeIssues]
    assert "style" not in x4.attrs.keys()
    try:
        x4.add_style("color: red")
        raise AssertionError("Expected ValueError for missing semicolon")
    except ValueError as e:
        assert "must end with a semicolon" in str(e)

    x4.add_style("color: red;")
    x4.add_style("color: green;")
    x4.add_style("color: blue;", prepend=True)
    assert x4.attrs["style"] == "color: blue; color: red; color: green;"

    x5 = div()
    x5.add_style("color: &purple;")
    assert isinstance(x5.attrs["style"], str)
    assert x5.attrs["style"] == "color: &purple;"
    x5.add_style(HTML("color: &green;"))
    assert isinstance(x5.attrs["style"], HTML)
    assert x5.attrs["style"] == HTML("color: &amp;purple; color: &green;")

    x6 = div()
    x6.add_style("color: &red;")
    assert isinstance(x6.attrs["style"], str)
    assert x6.attrs["style"] == "color: &red;"
    x6.add_style(HTML("color: &green;"), prepend=True)
    assert isinstance(x6.attrs["style"], HTML)
    assert x6.attrs["style"] == HTML("color: &green; color: &amp;red;")
    assert isinstance(x6.attrs["style"], HTML)
    x6.add_style(HTML("color: &blue;"))
    assert x6.attrs["style"] == HTML("color: &green; color: &amp;red; color: &blue;")


def test_tag_list_dict():
    # Dictionaries allowed at top level
    x1 = div("a", {"b": "B"}, "c")
    assert x1.attrs == {"b": "B"}
    assert str(x1) == '<div b="B">\n  ac\n</div>'

    # List args can't contain dictionaries
    with pytest.raises(TypeError):
        div(["a", {"b": "B"}], "c")  # type: ignore

    # Nested list args can't contain dictionaries
    with pytest.raises(TypeError):
        div(["a", ["b", {"c": "C"}]], "d")  # type: ignore

    # `children` can't contain dictionaries
    with pytest.raises(TypeError):
        div({"class": "foo"}, children=[{"class_": "bar"}], class_="baz")  # type: ignore


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
    foo_attrs = div({"class": "foo"}).attrs
    bar_attrs = div({"class": "bar"}).attrs
    x = div({"class": "foo", "class_": "bar"}, class_="baz")
    y = div(foo_attrs, {"class_": "bar"}, class_="baz")
    z = div({"class": "foo"}, bar_attrs, class_="baz")
    assert x.attrs == {"class": "foo bar baz"}
    assert y.attrs == {"class": "foo bar baz"}
    assert z.attrs == {"class": "foo bar baz"}
    x.attrs.update({"class": "bap", "class_": "bas"}, class_="bat")
    assert x.attrs == {"class": "bap bas bat"}


def test_non_escaped_text_is_escaped_when_added_to_html():
    x = HTML("&") + " &"
    x_str = str(x)
    assert isinstance(x, HTML)
    assert x_str == "& &amp;"


def test_html_equals_html():
    x = "<h1>a top level</h1>\n"
    a = HTML(x)
    b = HTML(x)
    assert a == b
    assert a == x
    assert x == b
    assert x == x  # for completeness


def test_html_adds_str_or_html():
    # first = "first"
    # second = "second"
    # firstsecond = first + second

    amp = "&"
    esc_amp = "&amp;"

    none = amp + amp
    first_html = HTML(amp) + amp
    second_html = amp + HTML(amp)

    both_html = HTML(amp) + HTML(amp)

    assert TagList(none).get_html_string() == f"{esc_amp}{esc_amp}"
    assert isinstance(none, str)

    assert TagList(first_html).get_html_string() == f"{amp}{esc_amp}"
    assert isinstance(first_html, HTML)

    assert TagList(second_html).get_html_string() == f"{esc_amp}{amp}"
    assert isinstance(second_html, HTML)

    assert TagList(both_html).get_html_string() == f"{amp}{amp}"
    assert isinstance(both_html, HTML)


def test_tag_shallow_copy():
    dep = HTMLDependency(
        "a", "1.1", source={"package": None, "subdir": "foo"}, script={"src": "a1.js"}
    )
    x = div(tags.i("hello", prop="value"), "world", dep, class_="myclass")
    y = copy.copy(x)
    cast_tag(y.children[0]).children[0] = "HELLO"
    cast_tag(y.children[0]).attrs["prop"] = "VALUE"
    y.children[1] = "WORLD"
    y.attrs["class"] = "MYCLASS"
    cast(HTMLDependency, y.children[2]).name = "A"

    # With a shallow copy(), the .attrs and .children are shallow copies, but if a
    # child is modified in place, then the the original child is modified as well.
    assert x is not y
    assert x.attrs == {"class": "myclass"}
    assert x.children is not y.children
    # If a mutable child is modified in place, both x and y see the changes.
    assert x.children[0] is y.children[0]
    assert cast_tag(x.children[0]).children[0] == "HELLO"
    # Immutable children can't be changed in place.
    assert x.children[1] is not y.children[1]
    assert x.children[1] == "world"
    assert x.children[1] is not y.children[1]
    # An HTMLDependency is mutable, so it is modified in place.
    assert cast(HTMLDependency, x.children[2]).name == "A"
    assert cast(HTMLDependency, y.children[2]).name == "A"
    assert x.children[2] is y.children[2]


def test_tagify_deep_copy():
    # Each call to .tagify() should do a shallow copy, but since it recurses, the result
    # is a deep copy.
    dep = HTMLDependency(
        "a", "1.1", source={"package": None, "subdir": "foo"}, script={"src": "a1.js"}
    )
    x = div(tags.i("hello", prop="value"), "world", dep, class_="myclass")

    y = x.tagify()
    cast_tag(y.children[0]).children[0] = "HELLO"
    cast_tag(y.children[0]).attrs["prop"] = "VALUE"
    y.children[1] = "WORLD"
    y.attrs["class"] = "MYCLASS"
    cast(HTMLDependency, y.children[2]).name = "A"

    assert x.attrs == {"class": "myclass"}
    assert y.attrs == {"class": "MYCLASS"}
    assert cast_tag(x.children[0]).attrs == {"prop": "value"}
    assert cast_tag(y.children[0]).attrs == {"prop": "VALUE"}
    assert cast_tag(x.children[0]).children[0] == "hello"
    assert cast_tag(y.children[0]).children[0] == "HELLO"
    assert x.children[1] == "world"
    assert y.children[1] == "WORLD"
    assert cast(HTMLDependency, x.children[2]).name == "a"
    assert cast(HTMLDependency, y.children[2]).name == "A"
    assert x.children[2] is not y.children[2]


def test_tag_writing():
    expect_html(TagList("hi"), "hi")
    expect_html(TagList("one", "two", TagList("three")), "onetwothree")
    expect_html(tags.b("one"), "<b>one</b>")
    expect_html(tags.b("one", "two"), "<b>onetwo</b>")
    expect_html(TagList(["one"]), "one")
    expect_html(TagList([TagList("one")]), "one")
    expect_html(TagList(tags.br(), "one"), "<br/>one")
    assert (
        str(tags.b("one", "two", span("foo", "bar", span("baz"))))
        == "<b>onetwo<span>foobar<span>baz</span></span></b>"
    )
    expect_html(tags.area(), "<area/>")


def test_tag_inline():
    # Empty inline/block tags
    expect_html(div(), "<div></div>")
    expect_html(span(), "<span></span>")

    # Inline/block tags with one item
    expect_html(div("a"), "<div>a</div>")
    expect_html(span("a"), "<span>a</span>")

    # Inline tags with two children
    expect_html(
        span("a", "b"),
        "<span>ab</span>",
    )
    expect_html(
        span(span("a"), "b"),
        "<span><span>a</span>b</span>",
    )
    expect_html(
        span("a", span("b")),
        "<span>a<span>b</span></span>",
    )
    expect_html(
        span(span("a"), span("b")),
        "<span><span>a</span><span>b</span></span>",
    )

    # Block tags with two inline children
    expect_html(
        div("a", "b"),
        textwrap.dedent(
            """\
            <div>
              ab
            </div>"""
        ),
    )
    expect_html(
        div(span("a"), "b"),
        textwrap.dedent(
            """\
            <div>
              <span>a</span>b
            </div>"""
        ),
    )
    expect_html(
        div("a", span("b")),
        textwrap.dedent(
            """\
            <div>
              a<span>b</span>
            </div>"""
        ),
    )
    expect_html(
        div(span("a"), span("b")),
        textwrap.dedent(
            """\
            <div>
              <span>a</span><span>b</span>
            </div>"""
        ),
    )

    # Block tags with one block and one inline child
    expect_html(
        div("a", div("b")),
        textwrap.dedent(
            """\
            <div>
              a
              <div>b</div>
            </div>"""
        ),
    )
    expect_html(
        div(span("a"), div("b")),
        textwrap.dedent(
            """\
            <div>
              <span>a</span>
              <div>b</div>
            </div>"""
        ),
    )
    expect_html(
        div(div("a"), "b"),
        textwrap.dedent(
            """\
            <div>
              <div>a</div>
              b
            </div>"""
        ),
    )
    expect_html(
        div(div("a"), span("b")),
        textwrap.dedent(
            """\
            <div>
              <div>a</div>
              <span>b</span>
            </div>"""
        ),
    )

    # Block tag with two block children
    expect_html(
        div(div("a"), div("b")),
        textwrap.dedent(
            """\
            <div>
              <div>a</div>
              <div>b</div>
            </div>"""
        ),
    )

    # Block tag with three children; mix of inline and block
    expect_html(
        div(span("a"), span("b"), div("c")),
        textwrap.dedent(
            """\
            <div>
              <span>a</span><span>b</span>
              <div>c</div>
            </div>"""
        ),
    )
    expect_html(
        div(span("a"), "b", div("c")),
        textwrap.dedent(
            """\
            <div>
              <span>a</span>b
              <div>c</div>
            </div>"""
        ),
    )
    expect_html(
        div(div("a"), "b", span("c")),
        textwrap.dedent(
            """\
            <div>
              <div>a</div>
              b<span>c</span>
            </div>"""
        ),
    )

    # More complex nesting
    expect_html(
        div(span(tags.b("a")), span(tags.b("b"))),
        textwrap.dedent(
            """\
            <div>
              <span><b>a</b></span><span><b>b</b></span>
            </div>"""
        ),
    )
    expect_html(
        span(span(tags.b("a")), span(tags.b("b")), span("c")),
        textwrap.dedent(
            """\
            <span><span><b>a</b></span><span><b>b</b></span><span>c</span></span>"""
        ),
    )
    expect_html(
        div(div(span("a")), span(tags.b("b"))),
        textwrap.dedent(
            """\
            <div>
              <div>
                <span>a</span>
              </div>
              <span><b>b</b></span>
            </div>"""
        ),
    )


def test_tag_list_ws():
    x = TagList(span("a"), "b")
    expect_html(x.get_html_string(), "<span>a</span>b")
    expect_html(x.get_html_string(add_ws=True), "<span>a</span>b")
    expect_html(x.get_html_string(indent=1, add_ws=True), "  <span>a</span>b")

    x = TagList(div("a"), "b")
    expect_html(x.get_html_string(), "<div>a</div>\nb")
    expect_html(x.get_html_string(add_ws=True), "<div>a</div>\nb")
    expect_html(x.get_html_string(indent=2, add_ws=True), "    <div>a</div>\n    b")

    x = TagList("a", "b", div("c", "d"), span("e", "f"), span("g", "h"))
    expect_html(
        x.get_html_string(),
        textwrap.dedent(
            """\
            ab
            <div>
              cd
            </div>
            <span>ef</span><span>gh</span>"""
        ),
    )
    expect_html(
        x.get_html_string(add_ws=True),
        textwrap.dedent(
            """\
            ab
            <div>
              cd
            </div>
            <span>ef</span><span>gh</span>"""
        ),
    )
    expect_html(
        x.get_html_string(indent=1, add_ws=True),
        """  ab
  <div>
    cd
  </div>
  <span>ef</span><span>gh</span>""",
    )


# This set of tests is commented out because we're not currently enforcing any
# particular behavior for invalid inline/block nesting.
# def test_tag_inline_invalid():
#     # This set of tests is for invalid inline/block nesting. Normally, block tags can
#     # contain inline or block tags, but inline tags can only contain inline tags.
#     #
#     # These tests cover the invalid cases where inline tags contain block tags.
#     expect_html(
#         span(div("a")),
#         "<span>ab</span>",
#     )
#     expect_html(
#         span(div("a"), "b"),
#         "<span>ab</span>",
#     )
#     expect_html(
#         span("a", div("b")),
#         "<span>ab</span>",
#     )
#     expect_html(
#         span(div("a"), div("b")),
#         "<span>ab</span>",
#     )


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
    # Attributes support `HTML()` values
    expect_html(div("text", class_=HTML("<a&b>")), '<div class="<a&b>">text</div>')

    # script and style tags are not escaped
    assert str(tags.script("a && b > 3")) == "<script>a && b > 3</script>"
    assert str(tags.script("a && b", "x > 3")) == "<script>\n  a && bx > 3\n</script>"
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
    assert saved_html(div("foo", dep), libdir=None) == textwrap.dedent(
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


def test_tag_str():
    # Make sure Tag.__str__() doesn't return an HTML string
    # (since, in that case, it'll render as HTML, which is suprising)
    x = str(span())
    y = repr(span())
    assert isinstance(x, str) and not isinstance(x, HTML)
    assert isinstance(y, str) and not isinstance(y, HTML)

    # Same for TagList.__str__
    x = str(TagList("foo"))
    y = str(TagList("foo"))
    assert isinstance(x, str) and not isinstance(x, HTML)
    assert isinstance(y, str) and not isinstance(y, HTML)

    x = str(HTML("foo&bar"))
    y = repr(HTML("foo&bar"))
    assert isinstance(x, str) and not isinstance(x, HTML)
    assert isinstance(y, str) and not isinstance(y, HTML)


# Walk a Tag tree, and apply a function to each node. The node in the tree will be
# replaced with the value returned from `fn()`. If the function alters a node, then it
# will be reflected in the original object that `.walk_mutate()` was called on.
#
# Note that if we were to export this function (perhaps in a class method), some other
# possible variants are:
# * Instead of one `fn`, take `pre` and `post` functions.
# * Allow functions that return `TagChild`, and then flatten/convert those to `TagNode`.
# * Provide a `_walk` function that doesn't mutate the tree. It would return `None`, and
#   `fn` should return `None`. This could be useful when `fn` just collects things from
#   the tree.
def _walk_mutate(x: TagNode, fn: Callable[[TagNode], TagNode]) -> TagNode:
    x = fn(x)
    if isinstance(x, Tag):
        for i, child in enumerate(x.children):
            x.children[i] = _walk_mutate(child, fn)
    elif isinstance(x, list):
        for i, child in enumerate(x):
            x[i] = _walk_mutate(child, fn)  # pyright: ignore[reportArgumentType]
    return x


def test_tag_walk():
    # walk() alters the tree in place, and also returns the altered object.
    x = div("hello ", tags.i("world"))
    y = div("The value of x is: ", x)

    def alter(x: TagNode) -> TagNode:
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
    assert cast_tag(x.children[1]).name == "b"
    assert cast_tag(x.children[1]).attrs.get("a") == "foo"
    assert cast_tag(x.children[1]).children[0] == "WORLD"


def test_taglist_constructor():

    # From docs.python.org/3/library/collections.html#collections.UserList:
    # > Subclasses of UserList are expected to offer a constructor which can be called
    # > with either no arguments or one argument. List operations which return a new
    # > sequence attempt to create an instance of the actual implementation class. To do
    # > so, it assumes that the constructor can be called with a single parameter, which
    # > is a sequence object used as a data source.

    x = TagList()
    assert isinstance(x, TagList)
    assert len(x) == 0
    assert x.get_html_string() == ""

    x = TagList("foo")
    assert isinstance(x, TagList)
    assert len(x) == 1
    assert x.get_html_string() == "foo"

    x = TagList(["foo", "bar"])
    assert isinstance(x, TagList)
    assert len(x) == 2
    assert x.get_html_string() == "foobar"

    # Also support multiple inputs
    x = TagList("foo", "bar")
    assert isinstance(x, TagList)
    assert len(x) == 2
    assert x.get_html_string() == "foobar"


def test_taglist_add():

    # Similar to `HTML(UserString)`, a `TagList(UserList)` should be the result when
    # adding to anything else.

    empty_arr = []
    int_arr = [1]
    tl_foo = TagList("foo")
    tl_bar = TagList("bar")

    def assert_tag_list(x: TagList, contents: list[str]) -> None:
        assert isinstance(x, TagList)
        assert len(x) == len(contents)
        for i, content_item in enumerate(contents):
            assert x[i] == content_item

        # Make sure the TagLists are not altered over time
        assert len(empty_arr) == 0
        assert len(int_arr) == 1
        assert len(tl_foo) == 1
        assert len(tl_bar) == 1
        assert int_arr[0] == 1
        assert tl_foo[0] == "foo"
        assert tl_bar[0] == "bar"

    assert_tag_list(empty_arr + tl_foo, ["foo"])
    assert_tag_list(tl_foo + empty_arr, ["foo"])
    assert_tag_list(int_arr + tl_foo, ["1", "foo"])
    assert_tag_list(tl_foo + int_arr, ["foo", "1"])
    assert_tag_list(tl_foo + tl_bar, ["foo", "bar"])
    assert_tag_list(tl_foo + "bar", ["foo", "bar"])
    assert_tag_list("foo" + tl_bar, ["foo", "bar"])


def test_taglist_methods():
    # Testing methods from https://docs.python.org/3/library/stdtypes.html#common-sequence-operations
    #
    # Operation | Result | Notes
    # --------- | ------ | -----
    # x in s    | True if an item of s is equal to x, else False | (1)
    # x not in s | False if an item of s is equal to x, else True | (1)
    # s + t     | the concatenation of s and t | (6)(7)
    # s * n or n * s | equivalent to adding s to itself n times | (2)(7)
    # s[i]      | ith item of s, origin 0 | (3)
    # s[i:j]    | slice of s from i to j | (3)(4)
    # s[i:j:k]  | slice of s from i to j with step k | (3)(5)
    # len(s)    | length of s
    # min(s)    | smallest item of s
    # max(s)    | largest item of s
    # s.index(x[, i[, j]]) | index of the first occurrence of x in s (at or after index i and before index j) | (8)
    # s.count(x) | total number of occurrences of x in s

    x = TagList("foo", "bar", "foo", "baz")
    y = TagList("a", "b", "c")

    assert "bar" in x
    assert "qux" not in x

    add = x + y
    assert isinstance(add, TagList)
    assert list(add) == ["foo", "bar", "foo", "baz", "a", "b", "c"]

    mul = x * 2
    assert isinstance(mul, TagList)
    assert list(mul) == ["foo", "bar", "foo", "baz", "foo", "bar", "foo", "baz"]

    assert x[1] == "bar"
    assert x[1:3] == TagList("bar", "foo")
    assert mul[1:6:2] == TagList("bar", "baz", "bar")

    assert len(x) == 4

    assert min(x) == "bar"  # pyright: ignore[reportArgumentType]
    assert max(x) == "foo"  # pyright: ignore[reportArgumentType]

    assert x.index("foo") == 0
    assert x.index("foo", 1) == 2
    with pytest.raises(ValueError):
        x.index("foo", 1, 1)

    assert x.count("foo") == 2
    assert mul.count("foo") == 4


def test_taglist_extend():
    x = TagList("foo")
    y = ["bar", "baz"]
    x.extend(y)
    assert isinstance(x, TagList)
    assert list(x) == ["foo", "bar", "baz"]
    assert y == ["bar", "baz"]

    x = TagList("foo")
    y = TagList("bar", "baz")
    x.extend(y)
    assert isinstance(x, TagList)
    assert list(x) == ["foo", "bar", "baz"]
    assert list(y) == ["bar", "baz"]

    x = TagList("foo")
    y = "bar"
    x.extend(y)
    assert list(x) == ["foo", "bar"]
    assert y == "bar"

    x = TagList("foo")
    x.extend(TagList("bar"))
    assert list(x) == ["foo", "bar"]


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


def test_repr_html():
    # Make sure that objects with a __repr_html__ method are rendered as HTML.
    class Foo:
        def _repr_html_(self) -> str:
            return "<span>Foo</span>"

    f = Foo()
    assert str(TagList(f)) == "<span>Foo</span>"
    assert str(span(f)) == "<span><span>Foo</span></span>"
    assert str(div(f)) == textwrap.dedent(
        """\
        <div>
          <span>Foo</span>
        </div>"""
    )


def test_types():
    # When a type checker like pyright is run on this file, this line will make sure
    # that a Tag function like `div()` matches the signature of the TagFunction Protocol
    # class.
    f: TagFunction = div  # noqa: F841

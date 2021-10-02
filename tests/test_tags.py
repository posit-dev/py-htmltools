import os
import copy
from tempfile import TemporaryDirectory

from htmltools import *
from htmltools.util import cwd


def expect_html(tag: tag, expected: str):
    assert str(tag) == expected


def test_basic_tag_api(snapshot):
    children = [h1("hello"), h2("world"), "text", None, ["list", ["here"]]]
    props = dict(class_="foo", for_="bar", id="baz", bool="")
    x1 = div(*children, **props)
    x2 = div(**props, children=children)
    x3 = div(**props)(*children)
    x4 = div()
    x4.append(*children, **props)
    assert x1 == x2 == x3 == x4
    assert x1.has_attr("id") and x1.has_attr("bool")
    assert not x1.has_attr("missing")
    snapshot.assert_match(str(x1), "basic_tag_api")
    assert x1.get_attr("class") == "foo"
    x1.append(class_="bar")
    assert x1.get_attr("class") == "foo bar"
    assert x1.has_class("foo") and x1.has_class("bar") and not x1.has_class("missing")
    x5 = tag_list()
    x5.append(a())
    x5.insert(0, span())
    expect_html(x5, "<span></span>\n<a></a>")


def test_tag_shallow_copy():
    x = div(tags.i("hello", prop="value"), "world", class_="myclass")
    y = copy.copy(x)
    y.children[0].children[0] = "HELLO"
    y.children[0]._attrs["prop"] = "VALUE"
    y.children[1] = "WORLD"
    y._attrs["class"] = "MYCLASS"

    # With a shallow copy(), the ._attrs and .children are shallow copies, but if a
    # child is modified in place, then the the original child is modified as well.
    assert x is not y
    assert x._attrs == {"class": "myclass"}
    assert x.children is not y.children
    # If a mutable child is modified in place, both x and y see the changes.
    assert x.children[0] is y.children[0]
    assert x.children[0].children[0] == "HELLO"
    # Immutable children can't be changed in place.
    assert x.children[1] is not y.children[1]
    assert x.children[1] == "world"


def test_tagify_deep_copy():
    # Each call to .tagify() should do a shallow copy, but since it recurses, the result
    # is a deep copy.
    x = div(tags.i("hello", prop="value"), "world", class_="myclass")

    y = x.tagify()
    y.children[0].children[0] = "HELLO"
    y.children[0]._attrs["prop"] = "VALUE"
    y.children[1] = "WORLD"
    y._attrs["class"] = "MYCLASS"

    assert x._attrs == {"class": "myclass"}
    assert y._attrs == {"class": "MYCLASS"}
    assert x.children[0]._attrs == {"prop": "value"}
    assert y.children[0]._attrs == {"prop": "VALUE"}
    assert x.children[0].children[0] == "hello"
    assert y.children[0].children[0] == "HELLO"
    assert x.children[1] == "world"
    assert y.children[1] == "WORLD"


def test_tag_writing(snapshot):
    expect_html(tag_list("hi"), "hi")
    expect_html(tag_list("one", "two", tag_list("three")), "one\ntwo\nthree")
    expect_html(tags.b("one"), "<b>one</b>")
    expect_html(tags.b("one", "two"), "<b>\n  one\n  two\n</b>")
    expect_html(tag_list(["one"]), "one")
    expect_html(tag_list([tag_list("one")]), "one")
    expect_html(tag_list(tags.br(), "one"), "<br/>\none")
    snapshot.assert_match(
        str(tags.b("one", "two", span("foo", "bar", span("baz")))), "tag_writing"
    )
    expect_html(tags.area(), "<area/>")


def test_tag_repr():
    assert repr(div()) == "<div with 0 children>"
    assert repr(div("foo")) == "<div with 1 child>"
    assert repr(div("foo", "bar", id="id")) == "<div#id with 2 children>"
    assert repr(div(id="id", class_="foo bar")) == "<div#id.foo.bar with 0 children>"
    assert (
        repr(div(id="id", class_="cls", foo="bar"))
        == "<div#id.cls with 1 other attributes and 0 children>"
    )


def test_tag_escaping():
    # Regular text is escaped
    expect_html(div("<a&b>"), "<div>&lt;a&amp;b&gt;</div>")
    # Children wrapped in html() isn't escaped
    expect_html(div(html("<a&b>")), "<div><a&b></div>")
    # Text in a property is escaped
    expect_html(div("text", class_="<a&b>"), '<div class="&lt;a&amp;b&gt;">text</div>')
    # Attributes wrapped in html() isn't escaped
    expect_html(div("text", class_=html("<a&b>")), '<div class="<a&b>">text</div>')


def saved_html(tag: tag):
    with TemporaryDirectory() as tmpdir:
        f = os.path.join(tmpdir, "index.html")
        tag.save_html(f)
        return open(f, "r").read()


def test_html_save(snapshot):
    snapshot.assert_match(saved_html(div()), "html_save_div")
    test_dir = os.path.dirname(__file__)
    with cwd(test_dir):
        dep = html_dependency(
            "foo", "1.0", "assets", stylesheet="css/my-styles.css", script="js/my-js.js"
        )
        # TODO: the indenting isn't quite right here
        snapshot.assert_match(saved_html(div("foo", dep)), "html_save_dep")
        desc = tags.meta(name="description", content="test")
        doc = html_document(div("foo", dep), desc, lang="en")
        snapshot.assert_match(saved_html(doc), "html_save_doc")

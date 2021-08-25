import os
from tempfile import TemporaryDirectory
from htmltools import *
from htmltools.util import cwd

def expect_html(tag: tag, expected: str):
  assert str(tag) == expected

def test_basic_tag_api():
  children = [h1("hello"), h2("world"), "text", None, ["list", ["here"]]]
  props = dict(_class_ = "foo", _for_ = "bar", id = "baz", bool="")
  x1 = div(*children, **props)
  x2 = div(**props, children = children)
  x3 = div(**props)(*children)
  x4 = div()
  x4.append_attrs(**props)
  x4.append_children(*children)
  assert x1 == x2 == x3 == x4
  assert x1.has_attr("id") and x1.has_attr("bool")
  assert not x1.has_attr("missing") 
  expect_html(x1, '<div class="foo" for="bar" id="baz" bool="">\n  <h1>hello</h1>\n  <h2>world</h2>\n  text\n  list\n  here\n</div>')
  assert x1.get_attr("class") == "foo"
  x1.append_attrs(_class_ = "bar")
  assert x1.get_attr("class") == "foo bar"
  assert x1.has_class("foo") and x1.has_class("bar") and not x1.has_class("missing") 
  x5 = tag_list()
  x5.append_children(a())
  x5.prepend_children(span())
  expect_html(x5, '<span></span>\n<a></a>')

def test_tag_writing():
  expect_html(tag_list("hi"), "hi")
  expect_html(
    tag_list("one", "two", tag_list("three")),
    "one\ntwo\nthree"
  )
  expect_html(tags.b("one"), "<b>one</b>")
  expect_html(tags.b("one", "two"), "<b>\n  one\n  two\n</b>")
  expect_html(tag_list(["one"]), "one")
  expect_html(tag_list([tag_list("one")]), "one")
  expect_html(tag_list(tags.br(), "one"), "<br/>\none")
  expect_html(
    tags.b("one", "two", span("foo", "bar", span("baz"))),
    '<b>\n  one\n  two\n  <span>\n    foo\n    bar\n    <span>baz</span>\n  </span>\n</b>'
  )
  expect_html(tags.area(), '<area/>')

def test_tag_repr():
  assert repr(div()) == '<div with 0 children>'
  assert repr(div("foo")) == '<div with 1 child>'
  assert repr(div("foo", "bar", id="id")) == '<div#id with 2 children>'
  assert repr(div(id="id", _class_="foo bar")) == '<div#id.foo.bar with 0 children>'
  assert repr(div(id="id", _class_="cls", foo="bar")) == '<div#id.cls with 1 other attributes and 0 children>'

def test_tag_escaping():
  # Regular text is escaped
  expect_html(div("<a&b>"), "<div>&lt;a&amp;b&gt;</div>")
  # Children wrapped in html() isn't escaped
  expect_html(div(html("<a&b>")), "<div><a&b></div>")
  # Text in a property is escaped
  expect_html(div("text", _class_="<a&b>"), '<div class="&lt;a&amp;b&gt;">text</div>')
  # Attributes wrapped in html() isn't escaped
  expect_html(div("text", _class_=html("<a&b>")), '<div class="<a&b>">text</div>')

def test_jsx_tags():
  expect_html(tag("Foo"), '<Foo/>')
  expect_html(tag("Foo", "bar"), '<Foo>bar</Foo>')
  # Curly braces are escaped in children by default
  expect_html(tag("Foo", "{bar}"), '<Foo>{"{"}bar{"}"}</Foo>')
  # Use jsx() for JS expressions
  expect_html(tag("Foo", jsx("bar")), '<Foo>{bar}</Foo>')
  # HTML is escaped in attributes, but curly braces are fine
  expect_html(tag("Foo", myProp="{<div/>}"), '<Foo myProp="{&lt;div/&gt;}"/>')
  # Again, use jsx() for JS expressions
  expect_html(tag("Foo", myProp=jsx("<div/>")), '<Foo myProp={<div/>}/>')


def saved_html(tag: tag):
  with TemporaryDirectory() as tmpdir:
    f = os.path.join(tmpdir, "index.html")
    tag.save_html(f)
    return open(f, "r").read()

def test_html_save():
  assert saved_html(div()) == '<!DOCTYPE html>\n<html>\n  <head>\n    <meta charset="utf-8"/>\n  </head>\n  <body>\n    <div></div>\n  </body>\n</html>'
  test_dir = os.path.dirname(__file__)
  with cwd(test_dir):
    dep = html_dependency("foo", "1.0", "assets", stylesheet="css/my-styles.css", script="js/my-js.js")
    # TODO: the indenting isn't quite right here
    assert saved_html(div("foo", dep)) == '<!DOCTYPE html>\n<html>\n  <head>\n    <meta charset="utf-8"/>\n            <link href="lib/foo%401.0/css/my-styles.css" rel="stylesheet"/>\n    <script src="lib/foo%401.0/js/my-js.js"></script>\n  </head>\n  <body>\n    <div>foo</div>\n  </body>\n</html>'
    desc = tags.meta(name="description", content="test")
    doc = html_document(div("foo", dep), desc, lang="en")
    assert saved_html(doc) == '<!DOCTYPE html>\n<html>\n  <head>\n    <meta charset="utf-8"/>\n            <link href="lib/foo%401.0/css/my-styles.css" rel="stylesheet"/>\n    <script src="lib/foo%401.0/js/my-js.js"></script>\n    <meta name="description" content="test"/>\n  </head>\n  <body>\n    <div>foo</div>\n  </body>\n</html>'

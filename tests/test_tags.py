import pytest
from htmltools import *

def expect_html(tag: tag, expected: str):
  assert str(tag) == expected

def test_basic_tag_api():
  children = [h1("hello"), h2("world"), "text", None, ["list", ["here"]]]
  props = dict(className = "foo", htmlFor = "bar", id = "baz", bool="")
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
  assert x1.get_attr("className") == "foo"
  x1.append_attrs(className = "bar")
  assert x1.get_attr("className") == "foo bar"
  assert x1.has_class("foo") and x1.has_class("bar") and not x1.has_class("missing")
  

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


def test_tag_escaping():
  # Regular text is escaped
  expect_html(div("<a&b>"), "<div>&lt;a&amp;b&gt;</div>")
  # Text in HTML() isn't escaped
  expect_html(div(html("<a&b>")), "<div><a&b></div>")
  # Text in a property is escaped
  expect_html(div("text", className = "<a&b>"), '<div class="&lt;a&amp;b&gt;">text</div>')
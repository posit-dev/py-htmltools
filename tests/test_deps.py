from htmltools import *

def expect_resolved_deps(input, output):
  actual = tag_list(*input).render()['dependencies']
  assert actual == output

def expect_html_deps(x, html_, deps):
  assert str(x) == html_
  assert x.render()['dependencies'] == deps

def test_dep_resolution():
  a1_1 = html_dependency("a", "1.1", {"href":"/"})
  a1_2 = html_dependency("a", "1.2", {"href":"/"})
  a1_2_1 = html_dependency("a", "1.2.1", {"href":"/"})
  b1_0_0 = html_dependency("b", "1.0.0", {"href":"/"})
  b1_0_1 = html_dependency("b", "1.0.1", {"href":"/"})
  c1_0 = html_dependency("c", "1.0", {"href":"/"})
  expect_resolved_deps(
    [a1_1, b1_0_0, b1_0_1, a1_2, a1_2_1, b1_0_0, b1_0_1, c1_0],
    [a1_2_1, b1_0_1, c1_0]
  )

def test_inline_deps():
  # Test out renderTags and findDependencies when tags are inline
  a1_1 = html_dependency("a", "1.1", {"href":"/"})
  a1_2 = html_dependency("a", "1.2", {"href":"/"})
  # tagLists ----------------------------------------------------------
  expect_html_deps(
    tag_list(a1_1, div("foo"), "bar"), 
    "<div>foo</div>\nbar", [a1_1]
  )
  expect_html_deps(
    tag_list(a1_1, div("foo"), a1_2, "bar"), 
    "<div>foo</div>\nbar", [a1_2]
  )
  # tags with children ------------------------------------------------
  expect_html_deps(
    div(a1_1, div("foo"), "bar"), 
    "<div>\n  <div>foo</div>\n  bar\n</div>", [a1_1]
  )
  # Passing normal lists to tagLists and tag functions  ---------------
  expect_html_deps(
    tag_list([a1_1, div("foo")], "bar"), 
    "<div>foo</div>\nbar", [a1_1]
  )
  expect_html_deps(
    div([a1_1, div("foo")], "bar"), 
    "<div>\n  <div>foo</div>\n  bar\n</div>", [a1_1]
  )

def test_append_deps():
  a1_1 = html_dependency("a", "1.1", {"href":"/"})
  a1_2 = html_dependency("a", "1.2", {"href":"/"})
  b1_2 = html_dependency("b", "1.0", {"href":"/"})
  x = div(a1_1, b1_2)
  x.append(a1_2)
  expect_html_deps(x, "<div></div>", [a1_2, b1_2])
  x = div(a1_1)
  x.append([a1_2, b1_2])
  expect_html_deps(x, "<div></div>", [a1_2, b1_2])
  x = div()
  x.append([a1_1, b1_2])
  x.append(a1_2)
  expect_html_deps(x, "<div></div>", [a1_2, b1_2])


def test_script_input():
  def fake_dep(**kwargs):
    return html_dependency("a", "1.0", "srcpath", **kwargs)
  dep1 = fake_dep(script = "js/foo bar.js", stylesheet = "css/bar foo.css")
  dep2 = fake_dep(script = ["js/foo bar.js"], stylesheet = ["css/bar foo.css"])
  dep3 = fake_dep(script = [{"src": "js/foo bar.js"}], stylesheet = [{"href": "css/bar foo.css"}])
  assert dep1 == dep2 == dep3
  # Make sure repeated calls to as_html() repeatedly encode
  for i in range(2):
    assert str(dep1) == '<link href="srcpath/css/bar%20foo.css" rel="stylesheet"/>\n<script src="srcpath/js/foo%20bar.js"></script>'

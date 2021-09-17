from htmltools import *

def expect_html(tag: tag, expected: str):
  assert str(tag) == expected

# TODO: add more tests! Also why is this not working?
#def test_jsx_tags():
#  x = jsx_tag("MyComponent")(span(), foo=jsx_tag("Foo")(), foo2=[div(), div()], bar=1, baz=jsx("foo"), style={'margin': '1rem'})
#  expect_html(x, '<script type="text/javascript">\n(function() {\n  var container = new DocumentFragment();\n  ReactDOM.render(React.createElement(MyComponent, {foo: "React.createElement(Foo, null)", foo2: "[React.createElement(\'div\', null), React.createElement(\'div\', null)]", bar: "1", baz: "foo", style: "{margin: "1rem"}", }, React.createElement(\'span\', null)), container);\n  document.currentScript.after(container);\n})();\n</script>')

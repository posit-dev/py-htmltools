import textwrap
from htmltools import *

"""name = "Eric"
age = 74
'{} is {}.'.format(name, age)'"""


def test_jsx_tags():
    Foo = jsx_tag("Foo")
    deps = Foo().tagify().get_dependencies()
    react_ver = [str(d.version) for d in deps if d.name == "react"][0]
    react_dom_ver = [str(d.version) for d in deps if d.name == "react-dom"][0]
    assert HTMLDocument(Foo()).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script src="lib/react-%s/react.production.min.js"></script>
            <script src="lib/react-dom-%s/react-dom.production.min.js"></script>
          </head>
          <body>
            <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(Foo)
          , container);
          document.currentScript.after(container);
        })();
        </script>
          </body>
        </html>"""
        % (react_ver, react_dom_ver)
    )

    Bar = jsx_tag("Bar")
    # Only the "top-level" tag gets wrapped in <script> tags
    assert HTMLDocument(Foo(Bar())).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script src="lib/react-%s/react.production.min.js"></script>
            <script src="lib/react-dom-%s/react-dom.production.min.js"></script>
          </head>
          <body>
            <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {},
              React.createElement(Bar)
            )
          , container);
          document.currentScript.after(container);
        })();
        </script>
          </body>
        </html>"""
        % (react_ver, react_dom_ver)
    )

    x = Foo(
        span(),
        "childtext",
        jsx("`childexpression`"),
        Foo(),
        [Foo(), Bar()],
        TagList(Foo(), Bar()),
        # span(Foo(span()), Bar()),
        int=1,
        float=2.0,
        bool=True,
        None_=None,
        string="string",
        list=[1, 2, 3],
        dict={"a": 1, "b": 2},
        jsxTag=Bar(),
        htmlTag=[div(), div(foo=1)],
        func=jsx("() => console.log('foo')"),
        style={"margin": "1rem"},
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"int": 1, "float": 2.0, "bool": true, "none": null, "string": "string", "list": [1, 2, 3], "dict": {a: 1, b: 2}, "jsxtag": React.createElement(Bar), "htmltag": [React.createElement('div'), React.createElement(  'div', {"foo": "1"})], "func": () => console.log('foo'), "style": {margin: "1rem"}},
              React.createElement('span'),
              "childtext",
              "`childexpression`",
              React.createElement(Foo),
              React.createElement(Foo),
              React.createElement(Bar),
              React.createElement(Foo),
              React.createElement(Bar)
            )
          , container);
          document.currentScript.after(container);
        })();
        </script>"""
    )

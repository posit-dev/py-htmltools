import textwrap
from htmltools import *


def test_jsx_tags():
    Foo = jsx_tag("Foo")
    Bar = jsx_tag("Bar")
    deps = Foo().tagify().get_dependencies()
    react_ver = [str(d.version) for d in deps if d.name == "react"][0]
    react_dom_ver = [str(d.version) for d in deps if d.name == "react-dom"][0]

    assert HTMLDocument(Foo()).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script src="react-%s/react.production.min.js"></script>
            <script src="react-dom-%s/react-dom.production.min.js"></script>
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

    # Only the "top-level" tag gets wrapped in <script> tags
    assert HTMLDocument(Foo(Bar())).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script src="react-%s/react.production.min.js"></script>
            <script src="react-dom-%s/react-dom.production.min.js"></script>
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
        span(Foo(span()), Bar()),
        int=1,
        float=2.0,
        bool=True,
        None_=None,
        string="string",
        list=[1, 2, 3],
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"int": 1, "float": 2.0, "bool": true, "None": null, "string": "string", "list": [1, 2, 3]},
              React.createElement('span'),
              "childtext",
              "`childexpression`",
              React.createElement(Foo),
              React.createElement(Foo),
              React.createElement(Bar),
              React.createElement(Foo),
              React.createElement(Bar),
              React.createElement(
                'span', {},
                React.createElement(
                  Foo, {},
                  React.createElement('span')
                ),
                React.createElement(Bar)
              )
            )
          , container);
          document.currentScript.after(container);
        })();
        </script>"""
    )

    x = Foo(
        "Hello",
        span("world"),
        dict={"a": 1, "b": 2},
        jsxTag=Bar(),
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"dict": {a: 1, b: 2}, "jsxTag": React.createElement(Bar)},
              "Hello",
              React.createElement(
                'span', {},
                "world"
              )
            )
          , container);
          document.currentScript.after(container);
        })();
        </script>"""
    )

    x = Foo(
        htmlTag=[div(), div(foo=1)],
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"htmlTag": [React.createElement('div'), React.createElement(
          'div', {"foo": "1"})]})
          , container);
          document.currentScript.after(container);
        })();
        </script>"""
    )

    x = Foo(
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
              Foo, {"func": () => console.log('foo'), "style": {margin: "1rem"}})
          , container);
          document.currentScript.after(container);
        })();
        </script>"""
    )


def test_jsx_tagifiable_children():
    # Test case where children are Tagifiable but not Tag or JsxTag objects.
    Foo = jsx_tag("Foo")

    class MyTag:
        def tagify(self):
            return span("Hello", Foo("world"))

    x = Foo(div(MyTag()))
    print(str(x))

    str(x) == textwrap.dedent(
        """\
        <script type="text/javascript">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {},
              React.createElement(
                'div', {},
                React.createElement(
                  'span', {},
                  "Hello",
                  React.createElement(
                    Foo, {},
                    "world"
                  )
                )
              )
            )
          , container);
          document.currentScript.after(container);
        })();
        </script>"""
    )

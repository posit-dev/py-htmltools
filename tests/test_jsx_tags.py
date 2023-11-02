import textwrap

from htmltools import HTMLDependency, HTMLDocument, TagList, css, div, span
from htmltools._jsx import jsx, jsx_tag_create


def test_jsx_tags():
    Foo = jsx_tag_create("Foo")
    Bar = jsx_tag_create("Bar")
    deps = Foo().tagify().get_dependencies()
    react_ver = [str(d.version) for d in deps if d.name == "react"][0]
    react_dom_ver = [str(d.version) for d in deps if d.name == "react-dom"][0]

    assert HTMLDocument(Foo()).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">react[%s];react-dom[%s]</script>
            <script src="lib/react-%s/react.production.min.js"></script>
            <script src="lib/react-dom-%s/react-dom.production.min.js"></script>
          </head>
          <body>
            <script type="text/javascript" data-needs-render="">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(Foo)
          , container);
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>
          </body>
        </html>"""
        % (react_ver, react_dom_ver, react_ver, react_dom_ver)
    )

    # Only the "top-level" tag gets wrapped in <script> tags
    assert HTMLDocument(Foo(Bar())).render()["html"] == textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8"/>
            <script type="application/html-dependencies">react[%s];react-dom[%s]</script>
            <script src="lib/react-%s/react.production.min.js"></script>
            <script src="lib/react-dom-%s/react-dom.production.min.js"></script>
          </head>
          <body>
            <script type="text/javascript" data-needs-render="">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {},
              React.createElement(Bar)
            )
          , container);
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>
          </body>
        </html>"""
        % (react_ver, react_dom_ver, react_ver, react_dom_ver)
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
        <script type="text/javascript" data-needs-render="">
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
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>"""
    )

    x = Foo(
        "Hello",
        span("world"),
        dict={"a": 1, "b": 2},
        jsxTag=Bar(),
        style=css(color="red"),
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript" data-needs-render="">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"dict": {"a": 1, "b": 2}, "jsxTag": React.createElement(Bar), "style": {"color": "red"}},
              "Hello",
              React.createElement(
                'span', {},
                "world"
              )
            )
          , container);
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>"""
    )

    x = Foo(
        htmlTag=[div(), div(foo=1)],
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript" data-needs-render="">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"htmlTag": [React.createElement('div'), React.createElement(
          'div', {"foo": "1"})]})
          , container);
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>"""
    )

    x = Foo(
        div(style=css(color="red")),
        func=jsx("() => console.log('foo')"),
        style={"margin": "1rem"},
    )
    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript" data-needs-render="">
        (function() {
          var container = new DocumentFragment();
          ReactDOM.render(
            React.createElement(
              Foo, {"func": () => console.log('foo'), "style": {"margin": "1rem"}},
              React.createElement(
                'div', {"style": {"color": "red"}})
            )
          , container);
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>"""
    )


def test_jsx_tagifiable_children():
    # Test case where children are Tagifiable but not Tag or JsxTag objects.
    Foo = jsx_tag_create("Foo")
    dep = HTMLDependency("a", "1.1", source={"subdir": "foo"}, script={"src": "a1.js"})
    dep2 = HTMLDependency("b", "1.1", source={"subdir": "foo"}, script={"src": "b1.js"})

    class TagifiableDep:
        def tagify(self):
            return dep

    class TagifiableDep2:
        def tagify(self):
            return span("Hello", Foo("world"), dep2)

    x = Foo(div(TagifiableDep(), TagifiableDep2()))
    # Make sure that calling render() doesn't alter the object in place and result in
    # output that changes from run to run.
    assert x.tagify() == x.tagify()
    assert HTMLDocument(x).render() == HTMLDocument(x).render()

    # Make sure that the dependency (which is added to the tree when MyTag.tagify() is
    # called) is properly registered. This makes sure that the JSX tag is getting the
    # dynamically-generated dependencies.
    assert dep in HTMLDocument(x).render()["dependencies"]
    assert dep2 in HTMLDocument(x).render()["dependencies"]
    assert HTMLDocument(x).render()["html"].find('<script src="a-1.1/a1.js"></script>')
    assert HTMLDocument(x).render()["html"].find('<script src="b-1.1/b1.js"></script>')

    assert str(x) == textwrap.dedent(
        """\
        <script type="text/javascript" data-needs-render="">
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
          var thisScript = document.querySelector('script[data-needs-render]');
          if (!thisScript) throw new Error('Failed to render JSXTag("Foo")');
          thisScript.after(container);
          thisScript.removeAttribute('data-needs-render');
        })();
        </script>"""
    )


def test_jsx_tag_normalize_attr():
    Foo = jsx_tag_create("Foo")
    x = Foo(class_="class_", x__="x__", x_="x_", x="x")
    assert x.attrs == {"class": "class_", "x-": "x__", "x": "x"}

    x = Foo(clAsS_="clAsS_", X__="X__")
    assert x.attrs == {"clAsS": "clAsS_", "X-": "X__"}

    x = Foo(clAsS_2="clAsS_2")
    assert x.attrs == {"clAsS-2": "clAsS_2"}


def test_jsx_tag_attrs_update():
    Foo = jsx_tag_create("Foo")

    # Update with dict
    x = Foo(a=1)
    x.attrs.update({"b": 2, "c": "C"})
    assert x.attrs == {"a": 1, "b": 2, "c": "C"}

    # Update with kwargs
    x = Foo(a=1)
    x.attrs.update(b=2, c="C")
    assert x.attrs == {"a": 1, "b": 2, "c": "C"}

    # Update with dict and kwargs
    x = Foo(a=1)
    x.attrs.update({"b": 2}, c="C")
    assert x.attrs == {"a": 1, "b": 2, "c": "C"}

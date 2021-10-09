from htmltools import *


def test_jsx_tags(snapshot):
    Foo = jsx_tag("Foo")
    snapshot.assert_match(HTMLDocument(Foo()).render()["html"], "jsx_single.txt")
    Bar = jsx_tag("Bar")
    # Only the "top-level" tag gets wrapped in <script> tags
    snapshot.assert_match(HTMLDocument(Foo(Bar())).render()["html"], "jsx_nested.txt")
    x = Foo(
        span(),
        "childtext",
        jsx("`childexpression`"),
        Foo(),
        [Foo(), Bar()],
        TagList(Foo(), Bar()),
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
    snapshot.assert_match(str(x), "jsx.txt")

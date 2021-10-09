from htmltools import *
import json


def test_dep_resolution(snapshot):
    a1_1 = HTMLDependency("a", "1.1", {"href": "/"}, script="a1.js")
    a1_2 = HTMLDependency("a", "1.2", {"href": "/"}, script="a2.js")
    a1_2_1 = HTMLDependency("a", "1.2.1", {"href": "/"}, script="a3.js")
    b1_0_0 = HTMLDependency("b", "1.0.0", {"href": "/"}, script="b1.js")
    b1_0_1 = HTMLDependency("b", "1.0.1", {"href": "/"}, script="b2.js")
    c1_0 = HTMLDependency("c", "1.0", {"href": "/"}, script="c1.js")
    test = TagList(*[a1_1, b1_0_0, b1_0_1, a1_2, a1_2_1, b1_0_0, b1_0_1, c1_0])
    snapshot.assert_match(HTMLDocument(test).render()["html"], "dep_resolution.txt")


# Test out renderTags and findDependencies when tags are inline
def test_inline_deps(snapshot):
    a1_1 = HTMLDependency("a", "1.1", {"href": "/"}, script="a1.js")
    a1_2 = HTMLDependency("a", "1.2", {"href": "/"}, script="a2.js")
    tests = [
        TagList(a1_1, div("foo"), "bar"),
        TagList(a1_1, div("foo"), a1_2, "bar"),
        div(a1_1, div("foo"), "bar"),
        TagList([a1_1, div("foo")], "bar"),
        div([a1_1, div("foo")], "bar"),
    ]
    html_ = "\n\n".join([HTMLDocument(t).render()["html"] for t in tests])
    snapshot.assert_match(html_, "inline_deps.txt")


def test_append_deps(snapshot):
    a1_1 = HTMLDependency("a", "1.1", {"href": "/"}, script="a1.js")
    a1_2 = HTMLDependency("a", "1.2", {"href": "/"}, script="a2.js")
    b1_2 = HTMLDependency("b", "1.0", {"href": "/"}, script="b1.js")
    x = div(a1_1, b1_2)
    x.append(a1_2)
    y = div(a1_1)
    y.append([a1_2, b1_2])
    z = div()
    z.append([a1_1, b1_2])
    z.append(a1_2)
    tests = [x, y, z]
    html_ = "\n\n".join([HTMLDocument(t).render()["html"] for t in tests])
    snapshot.assert_match(html_, "append_deps.txt")


def test_script_input(snapshot):
    def fake_dep(**kwargs):
        return HTMLDependency("a", "1.0", "srcpath", **kwargs)

    dep1 = fake_dep(script="js/foo bar.js", stylesheet="css/bar foo.css")
    dep2 = fake_dep(script=["js/foo bar.js"], stylesheet=["css/bar foo.css"])
    dep3 = fake_dep(
        script=[{"src": "js/foo bar.js"}], stylesheet=[{"href": "css/bar foo.css"}]
    )
    assert dep1 == dep2 == dep3
    # Make sure repeated calls to as_html() repeatedly encode
    test = TagList([dep1, dep2, dep3])
    for i in range(2):
        snapshot.assert_match(HTMLDocument(test).render()["html"], "script_input.txt")

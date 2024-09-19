from htmltools import HTML, consolidate_attrs


def test_consolidate_attrs():

    (attrs, children) = consolidate_attrs(
        {"class": "&c1"},
        0,
        # This tests `__radd__` method of `HTML` class
        {"id": "foo", "class_": HTML("&c2")},
        [1, [2]],
        3,
        class_=HTML("&c3"),
        other_attr="other",
    )

    assert attrs == {"id": "foo", "class": "&amp;c1 &c2 &c3", "other-attr": "other"}
    assert children == [0, [1, [2]], 3]

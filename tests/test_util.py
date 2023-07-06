from typing import Any

from htmltools import TagList, div, span
from htmltools._util import flatten


def test_flatten():
    assert flatten([[]]) == []
    assert flatten([1, [2], ["3", [4, None, 5, div(div()), div()]]]) == [
        1,
        2,
        "3",
        4,
        5,
        div(div()),
        div(),
    ]

    # Make sure that _flatten() doesn't alter original objects in place.
    x = [4, None, 5, div(div()), div()]
    y = ["3", x]
    assert flatten([1, [2], y]) == [1, 2, "3", 4, 5, div(div()), div()]
    assert x == [4, None, 5, div(div()), div()]
    assert y == ["3", [4, None, 5, div(div()), div()]]

    # Tuples
    x1: list[Any] = [1, [2], ("3", [4, None, 5, div(div()), div()])]
    assert flatten(x1) == [
        1,
        2,
        "3",
        4,
        5,
        div(div()),
        div(),
    ]

    # Flattening TagList. Note that the TagList itself converts its numeric children to
    # strings, so 1 and 2 become "1" and "2".
    x2: list[Any] = [0, TagList(1, 2, div(), TagList(span(div()), span())), (3, 4)]
    assert list(flatten(x2)) == [0, "1", "2", div(), span(div()), span(), 3, 4]
    assert flatten([1, [TagList("2"), 3], 4]) == [1, "2", 3, 4]

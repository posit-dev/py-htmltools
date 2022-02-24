import pytest
from htmltools import *
from htmltools._util import _flatten


def test_flatten():
    assert _flatten([[]]) == []
    assert _flatten([1, [2], ["3", [4, None, 5, div(div()), div()]]]) == [
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
    assert _flatten([1, [2], y]) == [1, 2, "3", 4, 5, div(div()), div()]
    assert x == [4, None, 5, div(div()), div()]
    assert y == ["3", [4, None, 5, div(div()), div()]]

    # Tuples
    assert _flatten([1, [2], ("3", [4, None, 5, div(div()), div()])]) == [
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
    assert list(
        _flatten([0, TagList(1, 2, div(), TagList(span(div()), span())), (3, 4)])
    ) == [0, "1", "2", div(), span(div()), span(), 3, 4]
    assert _flatten([1, [TagList("2"), 3], 4]) == [1, "2", 3, 4]

import pytest
from htmltools import *
from htmltools.util import flatten

def test_flatten():
    assert flatten([[]]) == []
    assert flatten([1, [2], ["3", [4, None, 5, div(div()), div()]]]) == [1, 2, "3", 4, 5, div(div()), div()]

    # Make sure that flatten() doesn't alter original objects in place.
    x = [4, None, 5, div(div()), div()]
    y = ["3", x]
    assert flatten([1, [2], y]) == [1, 2, "3", 4, 5, div(div()), div()]
    assert x == [4, None, 5, div(div()), div()]
    assert y == ["3", [4, None, 5, div(div()), div()]]

    # Tuples
    assert flatten([1, [2], ("3", [4, None, 5, div(div()), div()])]) == [1, 2, "3", 4, 5, div(div()), div()]

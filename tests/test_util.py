import pytest
from htmltools import *
from htmltools.util import flatten 

def test_flatten():
  assert flatten([[]]) == []
  assert flatten([1, [2], ["3", [4, None, 5, div(div()), div()]]]) == [1, 2, "3", 4, 5, div(div()), div()]
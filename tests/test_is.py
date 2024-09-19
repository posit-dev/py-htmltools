from typing import List

import pytest

from htmltools import (
    HTML,
    HTMLDependency,
    ReprHtml,
    Tag,
    TagAttrs,
    TagChild,
    TagList,
    TagNode,
    div,
    is_tag_child,
    is_tag_node,
)

tag_attr_obj: TagAttrs = {"test_key": "test_value"}


class ReprClass:

    def _repr_html_(self) -> str:
        return "repr_html"


repr_obj = ReprClass()


class OtherObj:
    pass


class TagifiableClass:
    def tagify(self) -> Tag:
        return Tag("test_element").tagify()


def test_is_repr_html():
    assert isinstance(repr_obj, ReprHtml)


tag_node_objs: List[TagNode] = [
    TagifiableClass(),
    Tag("test_element2"),
    TagList([div("div_content")]),
    HTMLDependency("test_dependency", version="1.0.0"),
    repr_obj,
    "test_string",
    HTML("test_html"),
]
tag_child_only_objs: List[TagChild] = [
    # *tag_node_objs,
    # [*tag_node_objs],
    [Tag("test_element3")],
    None,
    [],
]

not_tag_child_objs = [
    OtherObj(),
]


@pytest.mark.parametrize("obj", tag_node_objs)
def test_is_tag_node(obj):
    assert is_tag_node(obj)


@pytest.mark.parametrize(
    "obj", [[*tag_node_objs], *tag_child_only_objs, *not_tag_child_objs]
)
def test_not_is_tag_node(obj):
    assert not is_tag_node(obj)


@pytest.mark.parametrize(
    "obj", [*tag_node_objs, [*tag_node_objs], *tag_child_only_objs]
)
def test_is_tag_child(obj):
    assert is_tag_child(obj)


@pytest.mark.parametrize("obj", not_tag_child_objs)
def test_not_is_tag_child(obj):
    assert not is_tag_child(obj)

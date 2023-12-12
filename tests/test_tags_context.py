import sys
from typing import cast

import pytest

from htmltools import Tag, TagList, tags


def test_tag_context_manager():
    # This tag is here to set sys.displayhook to something that collects the contents
    # inside its `with` statement. We're interested in checking the children of
    # wrapper_tag.
    wrapper_tag = tags.body()
    with wrapper_tag:
        with tags.div():
            # Each line inside has sys.displayhook called on it, so we can check that
            # that function was replaced correctly. Note that normally when these
            # context managers are used, the evaluation environment (like Shiny Express,
            # or Jupyter) will automatically call sys.displayhook on each line.
            sys.displayhook("Hello, ")
            sys.displayhook(tags.i("big"))
            with tags.b():
                sys.displayhook("world")
            sys.displayhook("!")

        res = wrapper_tag.children[0]
        assert str(res) == "<div>\n  Hello, <i>big</i><b>world</b>!\n</div>"

        # Make sure that TagChildren are properly added to the parent.
        with tags.span():
            sys.displayhook(["a", 1, tags.b("bold")])
            sys.displayhook(TagList("c", 2, tags.i("italic")))
            sys.displayhook(3)

        res = cast(Tag, wrapper_tag.children[1])
        assert str(res) == "<span>a1<b>bold</b>c2<i>italic</i>3</span>"
        # Make sure the list and TagList were flattened when added to the parent, just
        # like if they were passed to `span([...], TagList(...))`.
        assert len(res.children) == 7


def test_tag_context_manager_type_validate():
    # Make sure Tag context managers validate types of inputs
    # Pass in objects that aren't valid TagChildren
    with pytest.raises(TypeError):
        with tags.span():
            # Pass in a set, which is not a valid TagChild
            sys.displayhook({1, 2, 3})

    with pytest.raises(TypeError):
        with tags.span():
            # Can't pass in a dictionary -- this is a TagAttrs object, but not TagChild.
            sys.displayhook({"class": "foo", "id": "bar"})

    with pytest.raises(TypeError):
        with tags.span():
            sys.displayhook("A")
            # Pass in a module object, which is not a valid TagChild
            sys.displayhook(tags)


if __name__ == "__main__":
    with tags.div():
        sys.displayhook({1, 2, 3})

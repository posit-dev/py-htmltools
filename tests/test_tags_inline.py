from htmltools import *


def test_inline_link():
    x = tags.p(
        "Here is a paragraph with ", tags.a("a link", href="http://example.com"), "."
    )
    assert (
        str(x)
        == '<p>Here is a paragraph with <a href="http://example.com">a link</a>.</p>'
    )

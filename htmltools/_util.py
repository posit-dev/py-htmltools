from __future__ import annotations

import hashlib
import importlib
import os
import re
import tempfile
from contextlib import closing
from http.server import SimpleHTTPRequestHandler
from socket import socket
from socketserver import TCPServer
from threading import Thread
from typing import Any, Hashable, Iterable, NamedTuple, Optional, TypeVar, Union

T = TypeVar("T")

HashableT = TypeVar("HashableT", bound=Hashable)

__all__ = ("css",)


def css(collapse_: str = "", **kwargs: str | float | None) -> Optional[str]:
    """
    CSS string helper

    Convenience function for building CSS style declarations (i.e. the string that goes
    into a style attribute, or the parts that go inside curly braces in a full
    stylesheet).

    Parameters
    ----------
    collapse_
        Character to use to collapse properties into a single string; likely "" (the
        default) for style attributes, and either "\n" or None for style blocks.
    **kwargs
        Named style properties, where the name is the property name and the argument is
        the property value.

    Returns
    -------
    :
        A string of CSS style declarations, or ``None`` if no properties were given.

    Example
    -------
    >>> from htmltools import css
    >>> css(font_size = "12px", backgroundColor = "red")
    'font-size:12px;background-color:red;'

    Note
    ----
    CSS uses '-' (minus) as a separator character in property names, which isn't allowed
    in Python's keyword arguments. This function allows you to use '_' (underscore) as a
    separator and/or camelCase notation instead.
    """
    res = ""
    for k, v in kwargs.items():
        if v is None:
            continue
        v = " ".join(v) if isinstance(v, list) else str(v)
        k = re.sub("_", "-", re.sub("([A-Z])", "-\\1", k).lower())
        res += k + ":" + v + ";" + collapse_
    return None if res == "" else res


# Flatten a arbitrarily nested list and remove None. Does not alter input object.
def flatten(x: Iterable[Union[T, None]]) -> list[T]:
    result: list[T] = []
    _flatten_recurse(x, result)
    return result


# Having this separate function and passing along `result` is faster than defining
# a closure inside of `flatten()` (and not passing `result`).
def _flatten_recurse(x: Iterable[T | None], result: list[T]) -> None:
    for item in x:
        if isinstance(item, (list, tuple)):
            # Don't yet know how to specify recursive generic types, so we'll tell
            # the type checker to ignore this line.
            _flatten_recurse(item, result)  # pyright: ignore[reportUnknownArgumentType]
        elif item is not None:
            result.append(item)


# similar to unique() in R (set() doesn't preserve order)
def unique(x: list[HashableT]) -> list[HashableT]:
    # This implementation requires Python 3.7+. Starting with that version, dict
    # order is guaranteed to be the same as insertion order.
    return list(dict.fromkeys(x))


HTML_ESCAPE_TABLE = {
    "&": "&amp;",
    ">": "&gt;",
    "<": "&lt;",
}

HTML_ATTRS_ESCAPE_TABLE = {
    **HTML_ESCAPE_TABLE,
    '"': "&quot;",
    "'": "&apos;",
    "\r": "&#13;",
    "\n": "&#10;",
}


def html_escape(text: str, attr: bool = False) -> str:
    table = HTML_ATTRS_ESCAPE_TABLE if attr else HTML_ESCAPE_TABLE
    if not re.search("|".join(table), text):
        return text
    for key, value in table.items():
        text = text.replace(key, value)
    return text


# Backwards compatibility with faicons 0.2.1
_html_escape = html_escape


# similar to base::system.file()
def package_dir(package: str) -> str:
    with tempfile.TemporaryDirectory():
        pkg_file = importlib.import_module(".", package=package).__file__
        if pkg_file is None:
            raise ImportError(f"Couldn't load package {package}")
        return os.path.dirname(pkg_file)


# Backwards compatibility with shinywidgets 0.1.4
_package_dir = package_dir


def hash_deterministic(s: str) -> str:
    """
    Returns a deterministic hash of the given string.
    """
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


class _HttpServerInfo(NamedTuple):
    port: int
    thread: Thread


_http_servers: dict[str, _HttpServerInfo] = {}


def ensure_http_server(path: str) -> int:
    server = _http_servers.get(path)
    if server:
        return server.port

    _http_servers[path] = start_http_server(path)
    return _http_servers[path].port


def start_http_server(path: str) -> _HttpServerInfo:
    port: int = get_open_port()
    th: Thread = Thread(target=http_server, args=(port, path), daemon=True)
    th.start()
    return _HttpServerInfo(port=port, thread=th)


def http_server(port: int, path: str):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any):
            super().__init__(*args, directory=path, **kwargs)

        def log_message(
            self, format, *args  # pyright: ignore[reportMissingParameterType]
        ):
            pass

    with TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()


def get_open_port() -> int:
    with closing(socket()) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]

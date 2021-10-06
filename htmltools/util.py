import os
import re
import importlib
import tempfile
from typing import (
    Any,
    List,
    NamedTuple,
    Union,
    TypeVar,
    Hashable,
    Dict,
    Optional,
)
from contextlib import contextmanager, closing
from http.server import SimpleHTTPRequestHandler
from socket import socket
from socketserver import TCPServer
from threading import Thread

T = TypeVar("T")

HashableT = TypeVar("HashableT", bound=Hashable)

__all__ = ["css"]


def css(collapse_: str = "", **kwargs: Union[str, float, None]) -> Optional[str]:
    res = ""
    for k, v in kwargs.items():
        if v is None:
            continue
        v = " ".join(v) if isinstance(v, list) else str(v)
        k = re.sub("[._]", "-", re.sub("([A-Z])", "-\\1", k).lower())
        if re.search("!$", k):
            v += " !important"
        res += k + ":" + v + ";" + collapse_
    return None if res == "" else res


# similar to unique() in R (set() doesn't preserve order)
def unique(x: List[HashableT]) -> List[HashableT]:
    # This implementation requires Python 3.7+. Starting with that version, dict
    # order is guaranteed to be the same as insertion order.
    return list(dict.fromkeys(x))


def html_escape(text: str, attr: bool = False) -> str:
    specials = {
        "&": "&amp;",
        ">": "&gt;",
        "<": "&lt;",
    }
    if attr:
        specials.update({'"': "&quot;", "'": "&apos;", "\r": "&#13;", "\n": "&#10;"})
    if not re.search("|".join(specials), text):
        return text
    for key, value in specials.items():
        text = text.replace(key, value)
    return text


# similar to base::system.file()
def package_dir(package: str) -> str:
    with tempfile.TemporaryDirectory():
        pkg_file = importlib.import_module(".", package=package).__file__
        return os.path.dirname(pkg_file)


class _HttpServerInfo(NamedTuple):
    port: int
    thread: Thread


_http_servers: Dict[str, _HttpServerInfo] = {}


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

        def log_message(self, format, *args):  # type: ignore
            pass

    with TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()


def get_open_port() -> int:
    with closing(socket()) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


@contextmanager
def cwd(path: str):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)

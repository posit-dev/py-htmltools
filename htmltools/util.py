import os
import re
import importlib
import tempfile
from typing import List, Tuple, Union, Any
from contextlib import contextmanager, closing
from http.server import SimpleHTTPRequestHandler
from socket import socket
from socketserver import TCPServer
from threading import Thread

# Both flatten a arbitrarily nested list *and* remove None 
def flatten(l: Union[List, Tuple]):
  f = flatten_impl(l)
  return [i for i in f if i]

# Derived from BasicProperty and BasicTypes source code
# Copyright (c) 2002-2003, Michael C. Fletcher
# http://basicproperty.sourceforge.net/
# http://rightfootin.blogspot.com/2006/09/no-builtin-flatyen-in-python.html
def flatten_impl(l: Union[List[Any], Tuple[Any]], ltypes = (list, tuple)):
  ltype = type(l)
  l = list(l)
  i = 0
  while i < len(l):
    while isinstance(l[i], ltypes):
      if not l[i]:
        l.pop(i)
        i -= 1
        break
      else:
        l[i:i + 1] = l[i]
    i += 1
  return ltype(l)

# similar to unique() in R (set() doesn't preserve order)
def unique(x: List[Any]) -> List[Any]:
  res: List[Any] = []
  for i in x:
    if i not in res:
      res.append(i)
  return res

def html_escape(text: str, attr: bool = False) -> str:
  specials = {
    "&": "&amp;",
    ">": "&gt;",
    "<": "&lt;",
  }
  if attr:
    specials.update({
      '"': "&quot;",
      "'": "&apos;",
      '\r': '&#13;',
      '\n': '&#10;'
    })
  if not re.search("|".join(specials), text):
    return text
  for key, value in specials.items():
    text = text.replace(key, value)
  return text

# similar to base::system.file()
def package_dir(package: str) -> str:
  with tempfile.TemporaryDirectory():
    pkg_file = importlib.import_module('.', package = package).__file__
    return os.path.dirname(pkg_file)


_http_servers = {}
def ensure_http_server(path: str):
  server = _http_servers.get(path)
  if server:
    return server._port
  
  _http_servers[path] = start_http_server(path)
  return _http_servers[path]._port
  
def start_http_server(path: str):
  port = get_open_port()
  th = Thread(target=http_server, args=(port, path), daemon=True)
  th.start()
  th._port = port
  return th

def http_server(port: int, path: str):
  class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=path, **kwargs)
    def log_message(self, format, *args):
      pass

  with TCPServer(("", port), Handler) as httpd:
    httpd.serve_forever()

def get_open_port():
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

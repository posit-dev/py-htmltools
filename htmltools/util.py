import os
import re
import importlib
import tempfile
from typing import List, Tuple, Union, Any
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler
import socket
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

# TODO: should be done with a try/finally?
def get_open_port():
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(("",0))
  s.listen(1)
  port = s.getsockname()[1]
  s.close()
  return port

def http_server(port: int, directory: str = None):
  class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)
    def log_message(self, format, *args):
      pass

  with TCPServer(("", port), Handler) as httpd:
    httpd.serve_forever()

def http_server_bg(port: int, directory: str=None):
  th = Thread(target=http_server, args=(port, directory), daemon=True)
  th.start()

@contextmanager
def cwd(path: str):
  oldpwd = os.getcwd()
  os.chdir(path)
  try:
    yield
  finally:
    os.chdir(oldpwd)

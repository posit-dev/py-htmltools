import os
import re
import importlib
from tempfile import TemporaryDirectory
from typing import List, Tuple, Union, Any
from contextlib import contextmanager

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


def html_escape(text: str, attr: bool = False):
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
  with TemporaryDirectory():
    pkg_file = importlib.import_module('.', package = package).__file__
    return os.path.dirname(pkg_file)

@contextmanager
def cwd(path: str):
  oldpwd = os.getcwd()
  os.chdir(path)
  try:
    yield
  finally:
    os.chdir(oldpwd)
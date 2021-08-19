import json
import os
from urllib.parse import quote
from typing import Optional, Tuple, Union, List, Dict, Callable, Any
from .util import *

# --------------------------------------------------------
# tag_list() is essentially a tag() without attributes
# --------------------------------------------------------
class tag_list():
  def __init__(self, *arguments: List) -> None:
    self.children: List = []
    if arguments: 
      self.append_children(*arguments)
  
  def append_children(self, *args: List) -> None:
    if args: 
      self.children += flatten(args)

  def _retrieve_dependencies(self) -> List['html_dependency']:
    deps = []
    for x in self.children:
      if isinstance(x, html_dependency):
        deps.append(x)
      elif isinstance(x, tag_list):
        deps += x._retrieve_dependencies()
    return deps

  def as_html(self, indent: int = 0, eol: str = '\n') -> 'html':
    return children_html(self.children, indent, eol)
    
  def render(self) -> Dict[str, Any]:
    return {
      "html": self.as_html(), 
      "dependencies": self._retrieve_dependencies()
    }
  
  # TODO: can we get htmlDependencies working in IPython?
  def show(self, renderer: str = "idisplay") -> None:
    if renderer == "idisplay":
      from IPython.core.display import display as idisplay
      from IPython.core.display import HTML as ihtml
      return idisplay(ihtml(self.as_html()))
    else:
      raise Exception(f"Unknown renderer {renderer}")

  def __str__(self) -> str:
    return self.as_html()

  def __repr__(self) -> str:
    return f'<tag_list with {len(self.children)} children>'

# --------------------------------------------------------
# Core tag logic
# --------------------------------------------------------
class tag(tag_list):
  def __init__(self, _name: str, *arguments: List, children: Optional[List] = None, **kwargs: Dict[str, str]) -> None:
    super().__init__(*arguments, children)
    self.name: str = _name
    self.attrs: List = []
    if kwargs: self.append_attrs(**kwargs)

  def __call__(self, *args: Any, **kwargs: Any) -> Any:
      self.append_attrs(**kwargs)
      self.append_children(*args)
      return self

  def append_attrs(self, **kwargs: Dict[str, str]) -> None:
    if kwargs: self.attrs.append(kwargs)

  def _get_attrs(self) -> Dict[str, str]:
    attrs = {}
    for x in self.attrs:
      for key, val in x.items():
        if val is None: continue
        val = val if isinstance(val, html) else str(val)
        attrs[key] = (self.attrs.get(key) + val) if key in attrs else val
    return attrs

  def as_html(self, indent: int = 0, eol: str = '\n') -> 'html':
    html_ = '<' + self.name

    # get/write (flattened) dictionary of attributes
    for key, val in self._get_attrs().items():
      if val is None or False: continue
      # e.g., data_foo -> data-foo
      key = key.replace('_', '-')
      # e.g., handle JSX alternatives for reserved words
      key = 'class' if key == 'className' else key
      key = 'for' if key == 'htmlFor' else key
      # escape HTML attr values (unless they're wrapped in HTML())
      val = val if isinstance(val, html) else html_escape(str(val), attr = True)
      html_ += f' {key}="{val}"'

    # Early exist for void elements http://dev.w3.org/html5/spec/single-page.html#void-elements
    if len(self.children) == 0 and self.name in ["area", "base", "br", "col", "command", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]:
      return html(html_ + ' />')

    # Early exit if no children
    html_ += '>'
    close = '</' + self.name + '>'
    if len(self.children) == 0:
      return html(html_ + close)

    # Inline a single/empty child text node
    if len(self.children) == 1 and isinstance(self.children[0], str):
      return html(html_ + normalize_text(self.children[0]) + close)

    # Write children
    html_ += eol
    html_ += children_html(self.children, indent + 1, eol)
    return html(html_ + eol + ('  ' * indent) + close)

  def __repr__(self) -> str:
    return f'<{self.name} with {len(self._get_attrs())} attributes & {len(self.children)} children>'


def children_html(children: List, indent: int = 0, eol: str = '\n') -> 'html':
  indent_ = '  ' * indent
  html_ = indent_
  n = len(children)
  for i, x in enumerate(children):
    if isinstance(x, html_dependency):
      continue
    if isinstance(x, tag):
      html_ += x.as_html(indent, eol)
    elif isinstance(x, tag_list):
      html_ += x.as_html(indent, eol)
    else:
      html_ += normalize_text(x) 
      html_ += (eol + indent_) if i < n - 1 else ''
  
  return html(html_)


# --------------------------------------------------------
# tag factory
# --------------------------------------------------------

def tag_factory_(_name: str) -> tag:
  def __init__(self, *args: List, children: Optional[List] = None, **kwargs: Dict[str, str]) -> None:
    tag.__init__(self, _name, *args, children = children, **kwargs)
  return __init__

# TODO: attribute verification?
def tag_factory(_name: str) -> tag:
  return type(_name, (tag,), {'__init__': tag_factory_(_name)})

# Generate a class for each known tag
class create_tags():
  def __init__(self) -> None:
    dir = os.path.dirname(__file__)
    with open(os.path.join(dir, 'known_tags.json')) as f:
      known_tags = json.load(f)
      # We don't have any immediate need for tags.head() since you can achieve the same effect
      # with an 'anonymous' dependency (i.e., htmlDependency(head = ....))
      known_tags.remove("head")
      for tag_ in known_tags:
        setattr(self, tag_, tag_factory(tag_))

tags = create_tags()

# --------------------------------------------------------
# html strings
# --------------------------------------------------------
class html(str):
  def __new__(cls, *args: List[str]) -> str:
    return super().__new__(cls, '\n'.join(args))

  # html() + html() should return html type
  def __add__(self, other: Union[str, 'html_dependency']) -> str:
    res = str.__add__(self, other)
    return html(res) if isinstance(other, html_dependency) else res

# --------------------------------------------------------
# html dependencies
# --------------------------------------------------------
class html_dependency():
  def __init__(self, name: str, version: str, src: Union[str, Dict[str, str]],
                     script: Optional[Union[str, List[str], List[Dict[str, str]]]] = None,
                     stylesheet: Optional[Union[str, List[str], List[Dict[str, str]]]] = None,
                     package: Optional[str] = None, all_files: bool = False,
                     meta: Optional[List[Dict[str, str]]] = None,
                     head: Optional[str] = None):
    self.name = name
    self.version = version
    self.src = src if isinstance(src, dict) else {"file": src}
    self.script = self._as_dicts(script, "src")
    self.stylesheet = self._as_dicts(stylesheet, "href")
    # Ensures a rel='stylesheet' default
    for i, s in enumerate(self.stylesheet):
      if "rel" not in s: self.stylesheet[i].update({"rel": "stylesheet"})
    self.package = package
    # TODO: implement shiny::createWebDependency()
    self.all_files = all_files
    self.meta = meta if meta else []
    self.head = head
    # TODO: do we need attachments?
    #self.attachment = attachment

  # TODO: do we really need hrefFilter? Seems rmarkdown was the only one that needed it
  # https://github.com/search?l=r&q=%22hrefFilter%22+user%3Acran+language%3AR&ref=searchresults&type=Code&utf8=%E2%9C%93
  def as_html(self, src_type: str = "file", encode_path: Callable[[str], str] = quote) -> html:
    src = self.src[src_type]
    if not src:
      raise Exception(f"HTML dependency {self.name}@{self.version} has no '{src_type}' definition")

    # Assume href is already URL encoded
    src = encode_path(src) if src_type == "file" else src

    sheets = self.stylesheet.copy()
    for i, s in enumerate(sheets):
      sheets[i].update({"href": encode_path(s["href"])})

    scripts = self.script.copy()
    for i, s in enumerate(scripts):
      scripts[i].update({"src": encode_path(s["src"])})

    metas = [tags.meta(**m) for m in self.meta]
    links = [tags.link(**s) for s in sheets]
    scripts = [tags.script(**s) for s in scripts]
    head = html(self.head) if self.head else None
    return tag_list(*metas, *links, *scripts, head).as_html()

  def _src_path(self) -> str:
    dir = package_dir(self.package) if self.package else ""
    return os.path.join(dir, self.src)

  def _as_dicts(self, val: Any, attr: str) -> List[Dict[str, str]]:
    if val is None:
      return []
    if isinstance(val, str):
      return [{attr: val}]
    if isinstance(val, list):
      return [{attr: i} if isinstance(i, str) else i for i in val]
    raise Exception(f"Invalid type for {repr(val)} in HTML dependency {self.name}@{self.version}")

  def __repr__(self):
    return f'<html_dependency "{self.name}@{self.version}">'

  def __str__(self):
    return self.as_html()

def normalize_text(txt: Any):
  return txt if isinstance(txt, html) else html_escape(str(txt), attr = False)

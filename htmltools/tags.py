import json
import os
import shutil
import tempfile
from pathlib import Path
from copy import deepcopy
from urllib.parse import quote
import webbrowser
import types
from typing import Optional, Union, List, Dict, Callable, Any, TypedDict
from .util import *
from .versions import versions
from packaging import version
package_version = version.parse
Version = version.Version

__all__ = [
  "tag_list",
  "tag",
  "tags",
  "jsx_tag",
  "html_document",
  "html",
  "jsx",
  "html_dependency",
  "tagify"
]

AttrType = Union[str, None]

# Types of objects that can be a child of a tag.
TagChild = Union['tag_list', 'html_dependency', str, int, float, bool]

class RenderedHTMLDocument(TypedDict):
    dependencies: List['html_dependency']
    html: str


class tag_list:
  '''
  Create a list (i.e., fragment) of HTML content

  Methods:
  --------
    show: Render and preview as HTML.
    save_html: Save the HTML to a file.
    append: Add content _after_ any existing children.
    insert: Add content after a given child index.
    render: Render the tag tree as an HTML string and also retrieve any dependencies.

  Attributes:
  -----------
    children: A list of child tags.

  Examples:
  ---------
    >>> print(tag_list(h1('Hello htmltools'), tags.p('for python')))
  '''
  def __init__(self, *args: TagChild) -> None:
    self.children: List[TagChild] = []
    if args:
      self.append(*args)

  def append(self, *args: TagChild) -> None:
    self.children += flatten(args)

  def insert(self, index: int = 0, *args: TagChild) -> None:
    if args:
      self.children.insert(index, *flatten(args))

  def render(self, tagify: bool = True) -> RenderedHTMLDocument:
    return html_document(self).render(tagify=tagify)

  def save_html(self, file: str, libdir: str = "lib") -> str:
    return html_document(self).save_html(file, libdir)

  def _get_html_string(self, indent: int = 0, eol: str = '\n') -> 'html':
    children = [x for x in self.children if not isinstance(x, html_dependency)]
    n = len(children)
    indent_ = '  ' * indent
    html_ = indent_
    for i, x in enumerate(children):
      if isinstance(x, tag_list):
        html_ += x._get_html_string(indent, eol)
      else:
        html_ += normalize_text(str(x))
      html_ += (eol + indent_) if i < n - 1 else ''
    return html(html_)

  def _get_dependencies(self) -> List['html_dependency']:
    deps: List[html_dependency] = []
    for x in self.children:
      if isinstance(x, html_dependency):
        deps.append(x)
      elif isinstance(x, tag_list):
        deps += x._get_dependencies()
    unames = unique([d.name for d in deps])
    resolved: List[html_dependency] = []
    for nm in unames:
      latest = max([d.version for d in deps if d.name == nm])
      deps_ = [d for d in deps if d.name == nm]
      for d in deps_:
        if d.version == latest and not d in resolved:
          resolved.append(d)
    return resolved

  def show(self, renderer: str = "auto") -> Any:
    if renderer == "auto":
      try:
        import IPython
        ipy = IPython.get_ipython()
        renderer = "ipython" if ipy else "browser"
      except ImportError:
        renderer = "browser"

    # TODO: can we get htmlDependencies working in IPython?
    if renderer == "ipython":
      from IPython.core.display import display_html
      # https://github.com/ipython/ipython/pull/10962
      return display_html(str(self), raw=True, metadata={'text/html': {'isolated': True}})

    if renderer == "browser":
      tmpdir = tempfile.gettempdir()
      key_ = "viewhtml" + str(hash(str(self)))
      dir = os.path.join(tmpdir, key_)
      Path(dir).mkdir(parents=True, exist_ok=True)
      file = os.path.join(dir, "index.html")
      self.save_html(file)
      port = ensure_http_server(tmpdir)
      webbrowser.open(f"http://localhost:{port}/{key_}/index.html")
      return file

    raise Exception(f"Unknown renderer {renderer}")

  def __str__(self) -> str:
    return self._get_html_string()

  def __eq__(self, other: Any) -> bool:
    return equals_impl(self, other)

  def __bool__(self) -> bool:
    return len(self.children) > 0

  def __repr__(self) -> str:
    return tag_repr_impl("tag_list", {}, self.children)

class tag(tag_list):
  '''
  Create an HTML tag.

  Methods:
  --------
    show: Render and preview as HTML.
    save_html: Save the HTML to a file.
    append: Add children (or attributes) _after_ any existing children (or attributes).
    insert: Add children (or attributes) into a specific child (or attribute) index.
    get_attrs: Get a dictionary of attributes.
    get_attr: Get the value of an attribute.
    has_attr: Check if an attribute is present.
    has_class: Check if the class attribte contains a particular class.
    render: Render the tag as HTML.

  Attributes:
  -----------
    name: The name of the tag
    children: A list of children

   Examples:
  ---------
    >>> print(div(h1('Hello htmltools'), tags.p('for python'), _class_ = 'mydiv'))
    >>> print(tag("MyJSXComponent"))
  '''

  def __init__(self,
    _name: str,
    *args: TagChild,
    children: Optional[List[TagChild]] = None,
    **kwargs: AttrType
  ) -> None:
    if children is None:
      children = []
    super().__init__(*args, *children)

    self.name: str = _name
    self._attrs: Dict[str, str] = {}
    self.append(**kwargs)
    # http://dev.w3.org/html5/spec/single-page.html#void-elements
    self._is_void = _name in ["area", "base", "br", "col", "command", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"]

  def __call__(self, *args: Any, **kwargs: AttrType) -> 'tag':
    self.append(*args, **kwargs)
    return self

  def append(self, *args: Any, **kwargs: AttrType) -> None:
    if args:
      super().append(*args)
    for k, v in kwargs.items():
      if v is None:
        continue
      k_ = encode_attr(k)
      v_ = self._attrs.get(k_, "")
      self._attrs[k_] = (v_ + " " + str(v)) if v_ else str(v)

  def get_attrs(self) -> Dict[str, str]:
    return self._attrs

  def get_attr(self, key: str) -> Optional[str]:
    return self.get_attrs().get(key)

  def has_attr(self, key: str) -> bool:
    return key in self.get_attrs()

  def has_class(self, _class_: str) -> bool:
    class_attr = self.get_attr("class")
    if class_attr is None:
      return False
    return _class_ in class_attr.split(" ")

  def _get_html_string(self, indent: int = 0, eol: str = '\n') -> 'html':
    html_ = '<' + self.name

    # write attributes (boolean attributes should be empty strings)
    for key, val in self.get_attrs().items():
      val = val if isinstance(val, html) else html_escape(val, attr=True)
      html_ += f' {key}="{val}"'

    # Dependencies are ignored in the HTML output
    children = [x for x in self.children if not isinstance(x, html_dependency)]

    # Don't enclose JSX/void elements if there are no children
    if len(children) == 0 and self._is_void:
      return html(html_ + '/>')

    # Other empty tags are enclosed
    html_ += '>'
    close = '</' + self.name + '>'
    if len(children) == 0:
      return html(html_ + close)

    # Inline a single/empty child text node
    if len(children) == 1 and isinstance(children[0], str):
      return html(html_ + normalize_text(children[0]) + close)

    # Write children
    # TODO: inline elements should eat ws?
    html_ += eol
    html_ += tag_list._get_html_string(self, indent + 1, eol)
    return html(html_ + eol + ('  ' * indent) + close)

  def __bool__(self) -> bool:
    return True

  def __repr__(self) -> str:
    return tag_repr_impl(self.name, self.get_attrs(), self.children)

# --------------------------------------------------------
# HTML tag functions
# --------------------------------------------------------

def make_tag_fn(_name: str) -> Callable[..., tag]:
  def tag_fn(
    *args: TagChild,
    children: Optional[List[TagChild]] = None,
    **kwargs: AttrType
  ) -> tag:
    return tag(_name, *args, children = children, **kwargs)

  tag_fn.__name__ = _name
  return tag_fn

class HTMLTags:
  def __init__(self) -> None:
    dir = os.path.dirname(__file__)
    with open(os.path.join(dir, 'known_tags.json')) as f:
      known_tags = json.load(f)
      # We don't have any immediate need for tags.head() since you can achieve
      # the same effect with an 'anonymous' dependency (i.e.,
      # htmlDependency(head = ....))
      known_tags.remove("head")
      for tag_name in known_tags:
        setattr(self, tag_name, make_tag_fn(tag_name))

tags = HTMLTags()

# --------------------------------------------------------
# JSX tags
# --------------------------------------------------------

def jsx_tag(_name: str, allowedProps: List[str] = None) -> None:
  pieces = _name.split('.')
  if pieces[-1][:1] != pieces[-1][:1].upper():
    raise NotImplementedError("JSX tags must be lowercase")

  # TODO: disallow props that are not in allowedProps
  def as_tags(self, *args, **kwargs) -> tag_list:
    js = "\n".join([
      "(function() {",
      "  var container = new DocumentFragment();",
      f"  ReactDOM.render({self._get_html_string()}, container);",
      "  document.currentScript.after(container);",
      "})();"
    ])
    # TODO: avoid the inline script tag (for security)
    return tag_list(
        lib_dependency("react", script="react.production.min.js"),
        lib_dependency("react-dom", script="react-dom.production.min.js"),
        self._get_dependencies(),
        tag("script", type="text/javascript")(html("\n"+js+"\n"))
    )

  def _get_html_string(self) -> str:
    if isinstance(self, tag_list) and not isinstance(self, tag):
      self = jsx_tag("React.Fragment")(*self.children)

    name = getattr(self, "_is_jsx", False) and self.name or "'" + \
        self.name + "'"
    res_ = 'React.createElement(' + name + ', '

    # Unfortunately we can't use json.dumps() here because I don't know how to
    # avoid quoting jsx(), jsx_tag(), tag(), etc.
    def serialize_attr(x) -> str:
      if isinstance(x, (list, tuple)):
        return '[' + ', '.join([serialize_attr(y) for y in x]) + ']'
      if isinstance(x, dict):
        return '{' + ', '.join([y + ': ' + serialize_attr(x[y]) for y in x]) + '}'
      if isinstance(x, jsx):
        return str(x)
      if isinstance(x, str):
        return '"' + x + '"'
      x_ = str(x)
      if isinstance(x, bool):
        x_ = x_.lower()
      return x_

    attrs = deepcopy(self.get_attrs())
    if not attrs:
      res_ += 'null'
    else:
      res_ += '{'
      for key, vals in attrs.items():
        res_ += key + ': '
        # If this tag is jsx, then it should be a list (otherwise, it's a string)
        if isinstance(vals, list):
          for i, v in enumerate(vals):
            vals[i] = serialize_attr(v)
          res_ += vals[0] if len(vals) == 1 else '[' + ', '.join(vals) + ']'
        else:
          res_ += vals
        res_ += ', '
      res_ += '}'

    for x in self.children:
      if isinstance(x, html_dependency):
        continue
      res_ += ', '
      if isinstance(x, tag_list):
        res_ += x._get_html_string()
      elif isinstance(x, jsx):
        res_ += x
      else:
        res_ += '"' + str(x) + '"'

    return res_ + ')'

  # JSX attrs can be full-on JSON objects whereas html/svg attrs
  # always get encoded as string
  def append(self, *args, **kwargs) -> None:
    if args:
        self.children += flatten(args)
    for k, v in kwargs.items():
      if v is None:
        continue
      k_ = encode_attr(k)
      if not self._attrs.get(k_):
        self._attrs[k_] = []
      self._attrs[k_].append(v)

  # JSX tags are similar to HTML tags, but have the following key differences:
  # 1. _All_ JSX tags have _is_jsx set to True
  #    * This differentiates from normal tags in the tag writing logic.
  # 2. Only the _root_ JSX tag has an __as_tags__ method
  #    * This ensures that only the root JSX tag is wrapped in a <script> tag
  # 3. Any tags within a JSX tag (inside children or attributes):
  #     * Have a different get_html_string() method (returning the relevant JavaScript)
  #     * Have a different append method (attributes can be JSON instead of just a string)
  def __new__(cls, *args: Any, children: Optional[Any] = None, **kwargs: AttrType) -> None:
    if allowedProps:
      for k in kwargs.keys():
        if k not in allowedProps:
          raise NotImplementedError(f"{k} is not a valid prop for {_name}")
    self = type(_name, (tag,), {'append': append})(_name, *args, children = children, **kwargs)
    def set_jsx_attrs(x):
      if not isinstance(x, tag_list):
        return x
      setattr(x, "__as_tags__", None)
      x._get_html_string = types.MethodType(_get_html_string, x)
      x.append = types.MethodType(append, x)
      return x
    rewrite_tags(self, set_jsx_attrs, preorder=False)
    for k, v in self._attrs.items():
      self._attrs[k] = [rewrite_tags(x, set_jsx_attrs, preorder=False) for x in v]
    setattr(self, "__as_tags__", as_tags)
    setattr(self, "_is_jsx", True)
    return self

  return type(_name, (tag,), {'__new__': __new__, '__init__': lambda self: None})



# --------------------------------------------------------
# Document class
# --------------------------------------------------------
class html_document(tag):
  '''
  Create an HTML document.

  Examples:
  ---------
    >>> print(html_document(h1("Hello"), tags.meta(name="description", content="test"), lang = "en"))
  '''
  def __init__(self, body: tag_list, head: Optional[tag_list] = None, **kwargs: AttrType) -> None:
    super().__init__("html", **kwargs)

    if not (isinstance(head, tag) and head.name == "head"):
      head = tag("head", head)
    if not (isinstance(body, tag) and body.name == "body"):
      body = tag("body", body)

    self.append(head, body)

  def render(self,
    tagify: bool = True,
    process_dep: Optional[Callable[['html_dependency'], 'html_dependency']] = None
  ) -> RenderedHTMLDocument:
    if tagify:
      self2 = _tagify(self)
    else:
      self2 = self

    deps: List[html_dependency] = self2._get_dependencies()
    if callable(process_dep):
      deps = [process_dep(x) for x in deps]

    child0_children: List[TagChild] = []
    if isinstance(self2.children[0], tag_list):
      child0_children = self2.children[0].children

    head = tag(
      "head",
      tag("meta", charset="utf-8"),
      *[d.as_tags() for d in deps],
      *child0_children
    )
    body = self2.children[1]
    return {
      "dependencies": deps,
      "html": "<!DOCTYPE html>\n" + str(tag("html", head, body))
    }

  def save_html(self, file: str, libdir: str = "lib") -> str:
    # Copy dependencies to libdir (relative to the file)
    dir = str(Path(file).resolve().parent)
    libdir = os.path.join(dir, libdir)
    def copy_dep(d: html_dependency):
      d = d.copy_to(libdir, False)
      d = d.make_relative(dir, False)
      return d
    res = self.render(process_dep=copy_dep)
    with open(file, "w") as f:
      f.write(res['html'])
    return file

# --------------------------------------------------------
# html strings
# --------------------------------------------------------
class html(str):
  '''
  Mark a string as raw HTML.

  Example:
  -------
  >>> print(div("<p>Hello</p>"))
  >>> print(div(html("<p>Hello</p>")))
  '''
  def __new__(cls, *args: str) -> 'html':
    return super().__new__(cls, '\n'.join(args))

  def __str__(self) -> 'html':
    return html(self)

  # html() + html() should return html()
  def __add__(self, other: Union[str, 'html']) -> str:
    res = str.__add__(self, other)
    return html(res) if isinstance(other, html) else res

# --------------------------------------------------------
# jsx expressions
# --------------------------------------------------------
class jsx(str):
  '''
  Mark a string as a JSX expression.

  Example:
  -------
  >>> Foo = tag_factory("Foo")
  >>> print(Foo(myProp = "<p>Hello</p>"))
  >>> print(Foo(myProp = jsx("<p>Hello</p>")))
  '''
  def __new__(cls, *args: str) -> 'jsx':
    return super().__new__(cls, '\n'.join(args))

  # html() + html() should return html()
  def __add__(self, other: Union[str, 'jsx']) -> str:
    res = str.__add__(self, other)
    return jsx(res) if isinstance(other, jsx) else res

# --------------------------------------------------------
# html dependencies
# --------------------------------------------------------
class html_dependency:
  '''
  Create an HTML dependency.

  Example:
  -------
  >>> x = div("foo", html_dependency(name = "bar", version = "1.0", src = ".", script = "lib/bar.js"))
  >>> x.render()
  '''
  def __init__(self, name: str, version: Union[str, Version],
                     src: Union[str, Dict[str, str]],
                     script: Optional[Union[str, List[str], List[Dict[str, str]]]] = None,
                     stylesheet: Optional[Union[str, List[str], List[Dict[str, str]]]] = None,
                     package: Optional[str] = None, all_files: bool = False,
                     meta: Optional[List[Dict[str, str]]] = None,
                     head: Optional[str] = None):
    self.name: str = name
    self.version: Version = version if isinstance(version, Version) else package_version(version)
    self.src: Dict[str, str] = src if isinstance(src, dict) else {"file": src}
    self.script: List[Dict[str, str]] = self._as_dicts(script, "src")
    self.stylesheet: List[Dict[str, str]] = self._as_dicts(stylesheet, "href")
    # Ensures a rel='stylesheet' default
    for i, s in enumerate(self.stylesheet):
      if "rel" not in s: self.stylesheet[i].update({"rel": "stylesheet"})
    self.package = package
    self.all_files = all_files
    self.meta = meta if meta else []
    self.head = head

  # I don't think we need hrefFilter (seems rmarkdown was the only one that needed it)?
  # https://github.com/search?l=r&q=%22hrefFilter%22+user%3Acran+language%3AR&ref=searchresults&type=Code&utf8=%E2%9C%93
  def as_tags(self, src_type: Optional[str]=None, encode_path: Callable[[str], str] = quote) -> html:
    # Prefer the first listed src type if not specified
    if not src_type:
      src_type = list(self.src.keys())[0]

    src = self.src.get(src_type, None)
    if not src:
      raise Exception(f"HTML dependency {self.name}@{self.version} has no '{src_type}' definition")

    # Assume href is already URL encoded
    src = encode_path(src) if src_type == "file" else src

    sheets = deepcopy(self.stylesheet)
    for s in sheets:
      s.update({"href": os.path.join(src, encode_path(s["href"]))})

    scripts = deepcopy(self.script)
    for s in scripts:
      s.update({"src": os.path.join(src, encode_path(s["src"]))})

    metas: List[tag] = [tags.meta(**m) for m in self.meta]
    links: List[tag] = [tags.link(**s) for s in sheets]
    scripts: List[tag] = [tags.script(**s) for s in scripts]
    head = html(self.head) if self.head else None
    return tag_list(*metas, *links, *scripts, head)

  def copy_to(self, path: str, must_work: bool = True) -> 'html_dependency':
    src = self.src['file']
    version = str(self.version)
    if not src:
      if must_work:
        raise Exception(f"Failed to copy HTML dependency {self.name}@{version} to {path} because it's local source directory doesn't exist")
      else:
        return self
    if not path or path == "/":
      raise Exception(f"path cannot be empty or '/'")

    if self.package:
      src = os.path.join(package_dir(self.package), src)

    # Collect all the source files
    if self.all_files:
      src_files = list(Path(src).glob("*"))
    else:
      src_files = flatten([[s["src"] for s in self.script], [s["href"] for s in self.stylesheet]])

    # setup the target directory
    # TODO: add option to exclude version
    target = os.path.join(path, self.name + "@" + version)
    if os.path.exists(target):
      shutil.rmtree(target)
    Path(target).mkdir(parents=True, exist_ok=True)

    # copy all the files
    for f in src_files:
      src_f = os.path.join(src, f)
      if not os.path.isfile(src_f):
        raise Exception(f"Failed to copy HTML dependency {self.name}@{version} to {path} because {src_f} doesn't exist")
      tgt_f = os.path.join(target, f)
      os.makedirs(os.path.dirname(tgt_f), exist_ok=True)
      shutil.copy2(src_f, tgt_f)

    # return a new instance of this class with the new path
    kwargs = deepcopy(self.__dict__)
    kwargs['src']['file'] = str(Path(target).resolve())
    return html_dependency(**kwargs)

  def make_relative(self, path: str, must_work: bool = True) -> 'html_dependency':
    src = self.src['file']
    if not src:
      if must_work:
        raise Exception(f"Failed to make HTML dependency {self.name}@{self.version} files relative to {path} since a local source directory doesn't exist")
      else:
        return self

    src = Path(src)
    if not src.is_absolute():
      raise Exception("Failed to make HTML dependency {self.name}@{self.version} relative because it's local source directory is not already absolute (call .copy_to() before .make_relative())")

    kwargs = deepcopy(self.__dict__)
    kwargs['src']['file'] = str(src.relative_to(Path(path).resolve()))
    return html_dependency(**kwargs)

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
    return str(self.as_tags())

  def __eq__(self, other: Any) -> bool:
    return equals_impl(self, other)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

from typing_extensions import Protocol, runtime_checkable

# A duck type: objects with __as_tags__ methods are considered AsTagable.
@runtime_checkable
class AsTagable(Protocol):
    def __as_tags__(self) -> tag_list:
       ...

Tagifiable = Union[tag_list, List[tag_list], AsTagable]

def tagify(x: Tagifiable) -> tag_list:
  def tagify_impl(ui: Tagifiable) -> tag_list:
    if isinstance(ui, AsTagable):
      # TODO: This should be ui.__as_tags__(), but it currently doesn't work due
      # to the way that jsx_tag.__as_tags__ is implemented.
      return(tagify(ui.__as_tags__(ui)))
    elif isinstance(ui, list):
      return tag_list(*ui)
    else:
      return ui

  return rewrite_tags(x, func=tagify_impl, preorder=False)

# For internal use in this module; this is so that a function can take `tagify`
# as an argument but still be able to call the `_tagify` function.
_tagify = tagify

def rewrite_tags(
  ui: Tagifiable,
  func: Callable[[Tagifiable], tag_list],
  preorder: bool
) -> tag_list:
  if preorder:
    ui = func(ui)

  if isinstance(ui, tag_list):
    new_children: List[TagChild] = []
    for child in ui.children:
      if isinstance(child, (tag_list, AsTagable)):
        new_children.append(rewrite_tags(child, func, preorder))
      else:
        new_children.append(child)

    ui.children = new_children

  elif isinstance(ui, list):
    ui = [rewrite_tags(item, func, preorder) for item in ui]

  if not preorder:
    ui = func(ui)

  return ui


# e.g., _foo_bar_ -> foo-bar
def encode_attr(x: str) -> str:
  if x.startswith('_') and x.endswith('_'):
    x = x[1:-1]
  return x.replace("_", "-")


def tag_repr_impl(name: str, attrs: Dict[str, str], children: List[TagChild]) -> str:
  x = '<' + name
  n_attrs = len(attrs)
  if attrs.get('id'):
     x += '#' + attrs['id']
     n_attrs -= 1
  if attrs.get('class'):
    x += '.' + attrs['class'].replace(' ', '.')
    n_attrs -= 1
  x += ' with '
  if n_attrs > 0:
    x += f'{n_attrs} other attributes and '
  n = len(children)
  x += '1 child>' if n == 1 else f'{n} children>'
  return x


def normalize_text(txt: str) -> str:
  return txt if isinstance(txt, html) else html_escape(txt, attr=False)


def equals_impl(x: Any, y: Any) -> bool:
  if not isinstance(y, type(x)):
    return False
  for key in x.__dict__.keys():
    if getattr(x, key, None) != getattr(y, key, None):
      return False
  return True


def lib_dependency(pkg: str, **kwargs: object) -> html_dependency:
  return html_dependency(
      name=pkg, version=versions[pkg],
      package="htmltools", src="lib/"+pkg,
      **kwargs
  )

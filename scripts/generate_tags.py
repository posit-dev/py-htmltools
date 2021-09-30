import os
from typing import List
import urllib
import urllib.request
import json

# Change known-tags to master once this gets merged
# https://github.com/rstudio/htmltools/pull/286
url = "https://raw.githubusercontent.com/rstudio/htmltools/known-tags/scripts/known_tags.json"
with urllib.request.urlopen(url) as u:
    tags = json.loads(u.read().decode())

tags_code: List[str] = []
for nm in tags:
  # We don't have any immediate need for tags.head() since you can achieve
  # the same effect with an 'anonymous' dependency (i.e.,
  # htmlDependency(head = ....))
  if nm == "head":
    continue
  # TODO: still provide this, but with underscores?
  if nm == "del":
    continue
  # TODO: this probably should be removed from the R pkg??
  if nm == "color-profile":
    continue
  code = '\n'.join([
      f"def {nm}(*args: TagChild, children: Optional[List[TagChild]]=None, **kwargs: AttrType) -> 'tag':",
      f"    return tag('{nm}', *args, children=children, **kwargs)"
  ])
  tags_code.append(code)

header = [
    "# Do not edit by hand, this file is automatically generated by ./scripts/get_known_tags.py",
    "from typing import Optional, List",
    "from .tags import tag, TagChild, AttrType",
    "",
    "# Should match https://github.com/rstudio/htmltools/blob/bc226a3d/R/tags.R#L697-L763",
    "__all__ = [",
    "    'p',",
    "    'h1',",
    "    'h2',",
    "    'h3',",
    "    'h4',",
    "    'h5',",
    "    'h6',",
    "    'a',",
    "    'br',",
    "    'div',",
    "    'span',",
    "    'pre',",
    "    'code',",
    "    'img',",
    "    'strong',",
    "    'em',",
    "    'hr'",
    "]",
    "",
    ""
]

# TODO: change tags2 to tags once tags.py gets renamed
src_file = os.path.join(os.path.dirname(__file__), '../htmltools/tags2.py')
with open(src_file, 'w') as f:
  src = '\n'.join(header) + '\n\n'.join(tags_code)
  f.write(src)
# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_attr_vals attr_vals.txt'] = '''<div true="" str="a" int="1" float="1.2" date="1999-01-02"></div>
<div class="foo bar"></div>'''

snapshots['test_basic_tag_api basic_tag_api'] = '''<div class="foo" for="bar" id="baz" bool="">
  <h1>hello</h1>
  <h2>world</h2>
  text
  list
  here
</div>'''

snapshots['test_html_save html_save_dep'] = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <link href="lib/foo-1.0/css/my-styles.css" rel="stylesheet"/>
    <script src="lib/foo-1.0/js/my-js.js"></script>
  </head>
  <body>
    <div>foo</div>
  </body>
</html>'''

snapshots['test_html_save html_save_div'] = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
  </head>
  <body>
    <div></div>
  </body>
</html>'''

snapshots['test_html_save html_save_doc'] = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <link href="foo-1.0/css/my-styles.css" rel="stylesheet"/>
    <script src="foo-1.0/js/my-js.js"></script>
  </head>
  <body>
    <div>foo</div>
    <meta name="description" content="test"/>
  </body>
</html>'''

snapshots['test_tag_writing tag_writing'] = '''<b>
  one
  two
  <span>
    foo
    bar
    <span>baz</span>
  </span>
</b>'''

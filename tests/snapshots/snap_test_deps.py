# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_append_deps append_deps.txt'] = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.2/a2.js"></script>
    <script src="lib/b-1.0/b1.js"></script>
  </head>
  <body>
    <div></div>
  </body>
</html>

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.2/a2.js"></script>
    <script src="lib/b-1.0/b1.js"></script>
  </head>
  <body>
    <div></div>
  </body>
</html>

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.2/a2.js"></script>
    <script src="lib/b-1.0/b1.js"></script>
  </head>
  <body>
    <div></div>
  </body>
</html>'''

snapshots['test_inline_deps inline_deps.txt'] = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.1/a1.js"></script>
  </head>
  <body>
    <div>foo</div>
    bar
  </body>
</html>

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.2/a2.js"></script>
  </head>
  <body>
    <div>foo</div>
    bar
  </body>
</html>

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.1/a1.js"></script>
  </head>
  <body>
    <div>
      <div>foo</div>
      bar
    </div>
  </body>
</html>

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.1/a1.js"></script>
  </head>
  <body>
    <div>foo</div>
    bar
  </body>
</html>

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <script src="lib/a-1.1/a1.js"></script>
  </head>
  <body>
    <div>
      <div>foo</div>
      bar
    </div>
  </body>
</html>'''

# Change Log for htmltools (for Python)

All notable changes to htmltools for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] 2024-10-29

### Breaking changes

* `HTML` no longer inherits from `str`. It now inherits from `collections.UserString`. This was done to avoid confusion between `str` and `HTML` objects. (#86)

* `TagList` no longer inherits from `list`. It now inherits from `collections.UserList`. This was done to avoid confusion between `list` and `TagList` objects. (#97)

* `Tag` and `TagList`'s method `.get_html_string()` now both return `str` instead of `HTML`. (#86)

* Strings added to `HTML` objects, now return `HTML` objects. E.g. `HTML_value + str_value` and `str_value + HTML_value` both return `HTML` objects. To maintain a `str` result, call `str()` on your `HTML` objects before adding them to other strings values. (#86)

* Items added to `TagList` objects, now return `TagList` objects. E.g. `TagList_value + arr_value` and `arr_value + TagList_value` both return new `TagList` objects. To maintain a `list` result, call `list()` on your `TagList` objects before combining them to other list objects. (#97)

### New features

* Exported `ReprHtml` protocol class. If an object has a `_repr_html_` method, then it is of instance `ReprHtml`. (#86)

* Exported `is_tag_node()` and `is_tag_child()` functions that utilize `typing.TypeIs` to narrow `TagNode` and `TagChild` type variables, respectively. (#86)

* Exported `consolidate_attrs(*args, **kwargs)` function. This function will combine the `TagAttrs` (supplied in `*args`) with `TagAttrValues` (supplied in `**kwargs`) into a single `TagAttrs` object. In addition, it will also return all `*args` that are not dictionary as a list of unaltered `TagChild` objects. (#86)

* The `Tag` method `.add_style(style=)` added support for `HTML` objects in addition to `str` values. (#86)

### Bug fixes

* Fixed an issue with `HTMLTextDocument()` returning extracted `HTMLDependency()`s in a non-determistic order. (#95)

## [0.5.3] 2024-07-18

* HTML tags in docstrings are now escaped. (#90)

## [0.5.2] 2024-05-23

* The `HTMLDependency.copy()` method can now correctly copy folders in depenendencies that both include directories and have `all_files=True`. (#87)

## [0.5.1] 2023-12-18

* `Tag` objects can now be used as context managers, as in `with tags.div():`. When used this way, then inside the `with` block, `sys.displayhook` is replaced with a function which adds items as children to the `Tag`. This is meant to be used with Shiny Express, Quarto, or Jupyter. (#76)

* Added a function `wrap_displayhook_handler()`. This alliows displayhooks to delegate their logic for handling various kinds of objects (like `Tag` objects and objects with a `_repr_html()`) to this function. (#77)


## [0.5.0] 2023-12-07

* Objects with a `_repr_html_` method can now appear as children of `Tag`/`TagList` objects. (#74)

* Changed the type annotation of `_add_ws` from `bool` to `TagAttrValue`. This makes it easier to write functions which call `Tag` functions and pass along `**kwargs`. (#67)

* Changed the type annotation of `collapse_` from `str` to `str | float | None`. This makes it easier to write calls to `css()` pass along `**kwargs`. (#68)

* Enhanced the type definition of `TagAttrs` to include `TagAttrDict`, the type of a `Tag`'s `attrs` property. (#55)

* For `HTMLTextDocument` objects, deduplicate HTML dependencies. (#72)

* Switched from `setup.cfg` and `setup.py` to `pyproject.toml`. (#73)


## [0.4.1] 2023-10-30

* Fixed deserialization of JSON HTML dependencies when they contained newline characters. (#65)


## [0.4.0] 2023-10-30

* Added `HTMLTextDocument` class, which takes as input a string representation of an HTML document. (#61)

* Added `htmltools.html_dependency_render_mode`. If this is set to `"json"`, then `HTMLDependency` objects will be rendered as JSON inside of `<script>` tags. (#61)


## [0.3.0] 2023-08-01

### New features

* Added `Tag` methods `remove_class` and `add_style`. (#57)

* Added support for `Tag`'s `add_class(prepend=)`. (#57)

### Other changes

* Dropped support for Python 3.7 (#56)


## [0.2.1] - 2023-04-03

### Bug fixes

* Fixed the stype signature of the `TagFunction` protocol class.


## [0.2.0] - 2023-04-03

### New features

* Added support for URL based `HTMLDependency` objects. (#53)

* Tag functions now have a boolean parameter `_add_ws`, which determines if the tag should be surrounded by whitespace. Tags which are normally block elements (like `div`) have this default to `True`, and tags which are normally inline elements (like `span`) have this default to `False`. This makes it possible to create HTML where neighboring elements have no whitespace between them. For example, `span(span("a"), span("b"))` will now yield `<span><span>a</span><span>b</span></span>`. (#54)


## [0.1.5] - 2023-03-11

### New features

* Changed types hints for `Tag` functions. The new types are `TagChild`, `TagNode`, `TagAttrValue`, and `TagAttrs`. (#51)

* Add public-facing `html_escape` function.

### Bug fixes

* Removed default argument values which were mutable objects.

### Other changes

* Moved packages from requirements-dev.txt to setup.cfg.


## [0.1.4] - 2023-03-01

### Bug fixes

* Added alias for `htmltools._util._package_dir` function, which was used by shinywidgets 0.1.4.


## [0.1.3] - 2023-03-01

### Bug fixes

* Fixed path handling on Windows. (#47)

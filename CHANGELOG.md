# Change Log for htmltools (for Python)

All notable changes to htmltools for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [UNRELEASED]

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

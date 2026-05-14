# htmltools

Tools for creating, manipulating, and writing HTML from Python.

## Installation

```sh
pip install htmltools
```

To install the latest development version from this repository:

```sh
uv pip install https://github.com/posit-dev/py-htmltools/tarball/main
```

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for managing the Python dev environment. Install `uv`, then:

```sh
make setup        # creates .venv and installs all dev/test deps
make ai-setup     # like setup, but also installs the pre-commit hook
make help         # list available targets
make check        # format + type + test checks
make format       # auto-fix formatting
```

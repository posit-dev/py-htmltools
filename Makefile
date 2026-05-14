.PHONY: help setup pre-commit-setup ai-setup \
        check check-format check-types check-tests check-tox \
        format coverage coverage-report update-snaps build clean

.DEFAULT_GOAL := help

# ---- Setup ----------------------------------------------------------------

setup:  ## Install dev environment (uv sync --all-groups)
	uv sync --all-groups

pre-commit-setup:  ## Install pre-commit git hook (idempotent)
	uv run pre-commit install

ai-setup: setup pre-commit-setup  ## Bootstrap a fresh checkout for AI agents / IDEs

# ---- Checks ---------------------------------------------------------------

check: check-format check-types check-tests  ## Run format + type + test checks

check-format:  ## Check lint and formatting with ruff
	@echo "📐 ruff check"
	uv run ruff check .
	@echo "📐 ruff format --check"
	uv run ruff format --check .

check-types:  ## Run pyright type checks
	@echo "📝 pyright"
	uv run pyright

check-tests:  ## Run pytest against the dev Python
	@echo "🧪 pytest"
	uv run pytest

check-tox:  ## Run pytest + pyright across Python 3.10-3.14 in parallel
	@echo "🔄 tox run-parallel"
	uv run tox run-parallel

# ---- Fixing ---------------------------------------------------------------

format:  ## Auto-fix lint and format with ruff
	uv run ruff check --fix .
	uv run ruff format .

# ---- Coverage -------------------------------------------------------------

coverage:  ## Run tests under coverage and print the report
	uv run coverage run -m pytest
	uv run coverage report

coverage-report: coverage  ## Build the HTML coverage report at htmlcov/
	uv run coverage html
	@echo "📔 HTML report written to htmlcov/index.html"

# ---- Snapshots ------------------------------------------------------------

update-snaps:  ## Update syrupy test snapshots
	@echo "📸 pytest --snapshot-update"
	uv run pytest --snapshot-update

# ---- Build ----------------------------------------------------------------

build: clean  ## Build sdist + wheel into dist/ via uv build
	@echo "🧳 uv build"
	uv build

# ---- Housekeeping ---------------------------------------------------------

clean:  ## Remove build, test, and coverage artifacts
	rm -rf build/ dist/ .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov/ .coverage .tox/

# ---- Help -----------------------------------------------------------------

help:  ## Show help messages for make targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; { \
		printf "\033[32m%-18s\033[0m %s\n", $$1, $$2; \
	}'

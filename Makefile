.PHONY: setup dev test lint typecheck build check release

PYTHON ?= python3

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && $(PYTHON) -m pip install -U pip
	. .venv/bin/activate && pip install -e .[dev]

dev:
	. .venv/bin/activate && devex-agent --help

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check src tests

typecheck:
	. .venv/bin/activate && mypy src

build:
	. .venv/bin/activate && $(PYTHON) -m build

check:
	. .venv/bin/activate && ruff check src tests
	. .venv/bin/activate && mypy src
	. .venv/bin/activate && pytest
	. .venv/bin/activate && bandit -q -r src
	. .venv/bin/activate && $(PYTHON) -m build

release:
	@echo "Update docs/CHANGELOG.md, tag release, and publish GitHub Release."

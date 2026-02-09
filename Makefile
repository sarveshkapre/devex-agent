.PHONY: setup dev test lint typecheck build check release

PYTHON ?= python3
VENV ?= .venv

ifeq ($(wildcard $(VENV)/bin/python),)
PYTHON_BIN := $(PYTHON)
PIP_BIN := pip
RUFF_BIN := ruff
MYPY_BIN := mypy
PYTEST_BIN := pytest
BANDIT_BIN := bandit
else
PYTHON_BIN := $(VENV)/bin/python
PIP_BIN := $(VENV)/bin/pip
RUFF_BIN := $(VENV)/bin/ruff
MYPY_BIN := $(VENV)/bin/mypy
PYTEST_BIN := $(VENV)/bin/pytest
BANDIT_BIN := $(VENV)/bin/bandit
endif

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install -U pip
	$(VENV)/bin/pip install -e .[dev]

dev:
	$(PYTHON_BIN) -m devex_agent.cli --help

test:
	$(PYTEST_BIN)

lint:
	$(RUFF_BIN) check src tests

typecheck:
	$(MYPY_BIN) src

build:
	$(PYTHON_BIN) -m build

check:
	$(RUFF_BIN) check src tests
	$(MYPY_BIN) src
	$(PYTEST_BIN)
	$(BANDIT_BIN) -q -r src
	$(PYTHON_BIN) -m build

release:
	@echo "Update docs/CHANGELOG.md, tag release, and publish GitHub Release."

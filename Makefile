#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PYTHONPATH := `pwd`

#* Installation
.PHONY: install
install:
	pip install pip-tools
	pip-compile -o requirements.txt pyproject.toml
	pip install -r requirements.txt

.PHONY: pre-commit-install
pre-commit-install:
	pip install pre-commit
	pre-commit install

#* Formatters
.PHONY: codestyle
codestyle:
	hatch run lint:fmt

.PHONY: formatting
formatting: codestyle

#* Linting
.PHONY: test
test:
	PYTHONPATH=$(PYTHONPATH) pytest -c pyproject.toml --cov-report=html --cov=django_paddle_billing tests/
	# poetry run coverage-badge -o assets/images/coverage.svg -f

.PHONY: mypy
mypy:
	mypy --config-file pyproject.toml ./

# .PHONY: check-safety
# check-safety:
# 	poetry check
# 	poetry run safety check --full-report
# 	poetry run bandit -ll --recursive paddle_billing_client tests

.PHONY: lint
lint: test check-codestyle mypy

# .PHONY: update-dev-deps
# update-dev-deps:
# 	poetry add -D bandit@latest darglint@latest "isort[colors]@latest" mypy@latest pre-commit@latest pydocstyle@latest pylint@latest pytest@latest pyupgrade@latest safety@latest coverage@latest coverage-badge@latest pytest-html@latest pytest-cov@latest
# 	poetry add -D --allow-prereleases black@latest

#* Cleaning
.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: dsstore-remove
dsstore-remove:
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: mypycache-remove
mypycache-remove:
	find . | grep -E ".mypy_cache" | xargs rm -rf

.PHONY: ipynbcheckpoints-remove
ipynbcheckpoints-remove:
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf

.PHONY: pytestcache-remove
pytestcache-remove:
	find . | grep -E ".pytest_cache" | xargs rm -rf

.PHONY: build-remove
build-remove:
	rm -rf build/

.PHONY: cleanup
cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove

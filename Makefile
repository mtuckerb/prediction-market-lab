.PHONY: check test lint

PYTHON ?= python

check: lint test

lint:
	$(PYTHON) -m compileall src tests

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

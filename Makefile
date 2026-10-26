#
# vim:ft=make
# fred, 2026-05-28 21:43
#
#
## Makefile for adif_parser Python module

.PHONY: help  clean pre-commit mypy pylint build

help:
	@echo ""
	@echo "Use the following commands:"
	@echo "---------------------------"
	@echo "make clean"
	@echo "make pre-commit"
	@echo "make mypy"
	@echo "make pylint"
	@echo "make build"

# Clean: Remove build artifacts and cache
clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .mypy_cache/ .pylint.py

# Pre-commit: Run pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Mypy: Run static type checking
mypy:
	mypy src/qsogrid.py add_grid.py

# Pylint: Run code linting
pylint:
	-pylint src/qsogrid.py add_grid.py

# Build: Build the Python package
build: clean
	python -m build

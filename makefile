help:
	echo "Available Targets: help clean test install install-dev check"

clean:
	pipenv run python -B scripts/clean_project.py

test:
	pipenv run pytest tests

check: test
	pipenv run flake8 shall
	pipenv run mypy shall

docs:
	pipenv run sphinx-build -M html docs/source docs/build

install:
	pipenv install

install-dev:
	pipenv install --dev
	pipenv run pip install -e .

.PHONY: help clean test install install-dev docs check

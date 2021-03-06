ifeq ($(OS),Windows_NT)
	SCRIPT_DIR = Scripts
	EXE_EXT = .exe
else
	SCRIPT_DIR = bin
	EXE_EXT =
endif

# Force forward slashes in $WORKON_HOME
WORKON_HOME := $(subst \,/,$(WORKON_HOME))

PROJECT_NAME = clac
VENV_ROOT = $(WORKON_HOME)/$(PROJECT_NAME)
VENV_SCRIPTS = $(VENV_ROOT)/$(SCRIPT_DIR)
VENV_PYTHON = $(VENV_SCRIPTS)/python$(EXE_EXT)
VENV_LINTER = $(VENV_SCRIPTS)/pylint$(EXE_EXT)
VENV_TYPECHKR = $(VENV_SCRIPTS)/mypy$(EXE_EXT)
VENV_PYTEST = $(VENV_SCRIPTS)/pytest$(EXE_EXT)
VENV_SPHINX = $(VENV_SCRIPTS)/sphinx-build$(EXE_EXT)
VENV_WHEEL = $(VENV_SCRIPTS)/wheel$(EXE_EXT)
VENV_TWINE = $(VENV_SCRIPTS)/twine$(EXE_EXT)
VENV_PIP = $(VENV_PYTHON) -m pip
CLEAN_ARGS = -dxe "*.egg-info" -e ".idea" -e ".vscode" -e "*.komodoproject" -e ".venv"
PYTEST_ARGS = -W ignore --cov $(PROJECT_NAME) --junitxml result.junit.xml

install: .venv
	$(VENV_PIP) install -e .

install-dev: install
	$(VENV_PIP) install -e .[fulldev]

unvenv:
	-deactivate
	rm -rf ./$(PROJECT_NAME).egg-info
	rm -rf $(VENV_ROOT)
	rm -f .venv

$(VENV_PYTHON):
	python -m venv $(VENV_ROOT)
	$(VENV_PIP) install --upgrade pip setuptools

$(VENV_LINTER): .venv
	$(VENV_PIP) install -e .[lint]

$(VENV_PYTEST): .venv
	$(VENV_PIP) install -e .[test,cov]

$(VENV_SPHINX): .venv
	$(VENV_PIP) install -e .[docs]

$(VENV_WHEEL): .venv
	$(VENV_PIP) install -e .[pkg]

.venv: $(VENV_PYTHON)
	echo $(VENV_PYTHON) > .venv

clean:
	git clean -f $(CLEAN_ARGS)

dry-clean:
	git clean -n $(CLEAN_ARGS)

lint: $(VENV_LINTER)
	$(VENV_LINTER) $(PROJECT_NAME)
	$(VENV_TYPECHKR) $(PROJECT_NAME)

test: $(VENV_PYTEST)
	$(VENV_PYTEST) $(PYTEST_ARGS) tests
	$(VENV_PYTHON) -m coverage html

docs: $(VENV_SPHINX)
	$(VENV_SPHINX) -M html docs/source docs/build

dist: $(VENV_WHEEL)
	$(VENV_PYTHON) setup.py sdist bdist_wheel

upload: dist
	$(VENV_TWINE) upload dist/*

.PHONY: install unvenv docs test lint clean install-dev upload

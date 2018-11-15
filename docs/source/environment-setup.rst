Setting up a Development Environment
====================================

This document explains how to set up a devlopment environment for the CLAC
project.

A note about Makefiles
----------------------

CLAC includes a Makefile to simplify the devlopment process.  This allows
commands to be run in a virtual environment without having to actually activate
the environment in your own shell.  To support this on Windows (which is the
real outlier) and other systems at the same time, the WORKON_HOME environment
variable must be set, and must NOT contain backslashes.  This means that on my
windows platforms, the virtualenv home directory must be set to ``D:/dev/venv``
instead of ``D:\dev\venv``.

Cloning the project
-------------------

To clone the project, please follow the steps below (after reading the whole
section to understand exactly what impact it will have):

- Ensure you are cloning the correct project (i.e. cloning your fork instead of
  the project itself)
- ``git clone https://github.com/<yourusername>/clac``
- ``make test``

The ``make test`` command will create a new virtual environment using the
current python interpreter as a base.  The environment will be stored in
``$WORKON_HOME/clac``, and the full path to the executable will be written to a
file named ``.venv`` at the root of the project.

Confirming your changes
-----------------------

In order to prevent destabilization of the project, all changes must pass CI
checks without fail.  Changes will not be accepted until this occurs.  There
are four checks which occur as of writing this:

- Unit testing through pytest_
  - ``make test``
- Code style/linting with pylint_
  - ``make lint``
- Static type analysis using mypy_
  - ``make lint`` *must pass the pylint check first for
  make to work.*
- Building documentation powered by sphinx_
  - ``make docs``

If any one of these fails, your pull request will be rejected.  If rejected,
you must submit a patch to the pull request which resolves the issue.

Additionally, if your change is an enhancement or bugfix to the codebase, it
must be accompanied by passing, coverage-proven unit tests.  Changes without
unit tests will not be accepted, but if you are unsure of how to unit test your
changes, submit anyway and the project owner will help you to write effective
unit tests for your change.

Working without make
--------------------

If you cannot use make, or wish to setup your own environment in a different
way, please follow the guide as-is, but referencing this section for
alternative executions to mimic make's functionality.

This section will be written with the assumption that you understand how to
configure your desired environment and use it properly, and is being provided
as a convenience.  Additionally, all of these commands should be executed from
the project root.

``pip install`` sections only need to be run once per environment.

**make install**
    ``pip install -e .``
**make install-dev**
    ``pip install -e .[fulldev]``
**make test**
    ``pip install -e .[test,cov] && pytest --cov clac tests && python -m coverage html``
**make docs**
    ``pip install -e .[docs] && sphinx-build -M html docs/source docs/build``
**make lint**
    ``pip install -e .[lint] && pylint clac && mypy clac``

.. _pytest: https://docs.pytest.org/en/stable/
.. _pylint: https://www.pylint.org/
.. _mypy: http://mypy-lang.org/
.. _sphinx: http://www.sphinx-doc.org/en/master/
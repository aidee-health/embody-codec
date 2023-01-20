# Contributor Guide

Thank you for your interest in improving this project. This page is
for developers wishing to contribute to this project.

Here is a list of important resources for contributors:

- [Source Code]
- [Issue Tracker]

[source code]: https://github.com/aidee-health/embody-protocol-codec
[issue tracker]: https://github.com/aidee-health/embody-protocol-codec/issues

## How to report a bug

Report bugs in the [Issue Tracker].

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.

## How to request a feature

Request features on the [Issue Tracker].

## How to set up your development environment

You need Python 3.9+ and the following tools:

- [Poetry]
- [Nox]
- [nox-poetry]

Install the package with development requirements:

```console
# install package with development requirements
$ poetry install
# setup pre-commit hooks
$ nox --session=pre-commit -- install
```

Note that most python IDEs has support for poetry as the intepreter.

[poetry]: https://python-poetry.org/
[nox]: https://nox.thea.codes/
[nox-poetry]: https://nox-poetry.readthedocs.io/

## How to setup pre-commit-hooks

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

```console
$ nox --session=pre-commit -- install
```

## How to test the project

Run the full test suite:

```console
$ pytest
```

Unit tests are located in the _tests_ directory,
and are written using the [pytest] testing framework.

[pytest]: https://pytest.readthedocs.io/

## How to submit changes

Open a [pull request] to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The tests must pass without errors and warnings.
- Include unit tests.
- If your changes add functionality, update the documentation accordingly.

[pull request]: https://github.com/aidee-health/embody-codec/pulls

## How to add a new library

To add a new library, run:

```
poetry add <library>
poetry update
```

Changes are made to the _pyproject.toml_ file.

## How to perform a release

To do a release:

- Create a new branch, ie `release-v-1-0-6`
- Run `poetry version <version>` (replacing `<version>` with the actual new version)
- Push change and create pull request
- Merge pull request - release and pypi deployment will be performed automatically

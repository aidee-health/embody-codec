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

Install the package with development requirements:

```console
$ poetry install
```

Note that most python IDEs has support for poetry as the intepreter. 

[poetry]: https://python-poetry.org/

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

[pull request]: https://github.com/aidee-health/embody-protocol-codec/pulls

## How to add a new library

To add a new library, run:

```
poetry add <library>
poetry update
```

Changes are made to the _pyproject.toml_ file and the _poetry.lock_ file 

## How to perform a release

To do a release:

- Create a new branch (or use an existing one if appropriate)
- Run `poetry version <new version number>`
- Push and create a pull request
- Merge pull request after approval

On merge, a release will be generated automatically, with all pull requests as
changes in the release note. 
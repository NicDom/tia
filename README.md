# tia

<div align="center">

[![Build status](https://github.com/NicDom/tia/workflows/build/badge.svg?branch=master&event=push)](https://github.com/NicDom/tia/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/tia.svg)](https://pypi.org/project/tia/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/NicDom/tia/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)
[![Codecov](https://codecov.io/gh/NicDom/tia/branch/main/graph/badge.svg)](https://codecov.io/gh/NicDom/tia)
[![Read The Docs](https://img.shields.io/readthedocs/tia/latest.svg?label=Read%20the%20Docs)](https://tia.readthedocs.io/)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/NicDom/tia/blob/master/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/NicDom/tia/releases)
[![License](https://img.shields.io/github/license/NicDom/tia)](https://github.com/NicDom/tia/blob/master/LICENSE)

A Tax and Invoice Assistant (TIA)

</div>

## Features

**TODO**

## Requirements

**TODO**

## Installation

```bash
pip install -U tia
```

or install with `Poetry`

```bash
poetry add tia
```

Then you can run

```bash
tia --help
```

or with `Poetry`:

```bash
poetry run tia --help
```

<details>
<summary>Installing Poetry</summary>
<p>

To download and install Poetry run (with curl):

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
```

or on windows (without curl):

```bash
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py -UseBasicParsing).Content | python -
```

</p>
</details>

### Uninstall:

If you wan to uninstall the package, simply run

```bash
pip uninstall tia
```

or with `Poetry`:

```bash
poetry remove tia
```

## Usage

**TODO**

## Contributing

Contributions are very welcome.
To learn more, see the `Contributor Guide`.

### Set up bots

- Set up [Dependabot](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates) to ensure you have the latest dependencies.
- Set up [Stale bot](https://github.com/apps/stale) for automatic issue closing.

### Poetry

Want to know more about Poetry? Check [its documentation](https://python-poetry.org/docs/).

<details>
<summary>Details about Poetry</summary>
<p>

Poetry's [commands](https://python-poetry.org/docs/cli/#commands) are very intuitive and easy to learn, like:

- `poetry add numpy@latest`
- `poetry run pytest`
- `poetry publish --build`

etc

</p>
</details>

### Building and releasing your package

Building a new version of the application contains steps:

- Switch to a branch
- Bump the version of your package `poetry version <version>`. You can pass the new version explicitly, or a rule such as `major`, `minor`, or `patch`. For more details, refer to the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub` and push it.
- Open a pull request.
- Merge the pull request 🙂

### Development features

- Supports for `Python 3.7` and higher.
- [`Poetry`](https://python-poetry.org/) as the dependencies manager. See configuration in [`pyproject.toml`](https://github.com/NicDom/tia/blob/master/pyproject.toml) and [`setup.cfg`](https://github.com/NicDom/tia/blob/master/setup.cfg).
- Automatic codestyle with [`black`](https://github.com/psf/black), [`isort`](https://github.com/timothycrosley/isort) and [`pyupgrade`](https://github.com/asottile/pyupgrade).
- Ready-to-use [`pre-commit`](https://pre-commit.com/) hooks with code-formatting.
- Type checks with [`mypy`](https://mypy.readthedocs.io); docstring checks with [`darglint`](https://github.com/terrencepreilly/darglint); security checks with [`safety`](https://github.com/pyupio/safety) and [`bandit`](https://github.com/PyCQA/bandit)
- Testing with [`pytest`](https://docs.pytest.org/en/latest/).
- Automating testing in multiple Python environments, linting, pre-commit, typechecks, doctests and safety checks using [`nox`]()
- Ready-to-use [`.editorconfig`](https://github.com/NicDom/tia/blob/master/.editorconfig) and [`.gitignore`](https://github.com/NicDom/tia/blob/master/.gitignore). You don't have to worry about those things.

### Table of Nox sessions

The following table gives an overview of the available Nox sessions:

| Session                          | Description                                      | Python                   | Default |
| -------------------------------- | ------------------------------------------------ | ------------------------ | ------- |
| [coverage][coverage session]     | Report coverage with [Coverage.py][coverage.py_] | `3.9`                    | (✓)     |
| [docs][docs session]             | Build and serve [Sphinx][sphinx_] documentation  | `3.9`                    |
| [docs][docs session]             | Build [Sphinx][sphinx_] documentation            | `3.9`                    | ✓       |
| [mypy][mypy session]             | Type-check with [mypy][mypy_]                    | `3.6` … `3.9`            | ✓       |
| [pre-commit][pre-commit session] | Lint with [pre-commit][pre-commit_]              | `3.9`                    | ✓       |
| [safety][safety session]         | Scan dependencies with [Safety][safety_]         | `3.9`                    | ✓       |
| [tests][tests session]           | Run tests with [pytest][pytest_]                 | `3.[6, 7, 8, 9]` … `3.9` | ✓       |
| [typeguard][typeguard session]   | Type-check with [Typeguard][typeguard_]          | `3.[6, 7, 8, 9]` … `3.9` | ✓       |
| [xdoctest][xdoctest session]     | Run examples with [xdoctest][xdoctest_]          | `3.[6, 7, 8, 9]` … `3.9` | ✓       |

### Deployment features

- `GitHub` integration: issue and pr templates.
- `Github Actions` with predefined [build workflow](https://github.com/NicDom/tia/blob/master/.github/workflows/build.yml) as the default CI/CD.
- Everything is already set up for security checks, codestyle checks, code formatting, testing, linting, docker builds, etc with [`nox`](https://github.com/NicDom/tia/blob/master/Makefile#L89). More details in [makefile-usage](#makefile-usage).
- [Dockerfile](https://github.com/NicDom/tia/blob/master/docker/Dockerfile) for your package.
- Always up-to-date dependencies with [`@dependabot`](https://dependabot.com/). You will only [enable it](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates).
- Automatic drafts of new releases with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). You may see the list of labels in [`release-drafter.yml`](https://github.com/NicDom/tia/blob/master/.github/release-drafter.yml). Works perfectly with [Semantic Versions](https://semver.org/) specification.

### Open source community features

- Ready-to-use [Pull Requests templates](https://github.com/NicDom/tia/blob/master/.github/PULL_REQUEST_TEMPLATE.md) and several [Issue templates](https://github.com/NicDom/tia/tree/master/.github/ISSUE_TEMPLATE).
- Files such as: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` are generated automatically.
- [`Stale bot`](https://github.com/apps/stale) that closes abandoned issues after a period of inactivity. (You will only [need to setup free plan](https://github.com/marketplace/stale)). Configuration is [here](https://github.com/NicDom/tia/blob/master/.github/.stale.yml).
- [Semantic Versions](https://semver.org/) specification with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter).

## 📈 Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/NicDom/tia/releases) page.

We follow [Semantic Versions](https://semver.org/) specification.

We use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

| **Pull Request Label** | **Section in Release Notes** |
| ---------------------- | ---------------------------- |
| `breaking`             | 💥 Breaking Changes          |
| `enhancement`          | 🚀 Features                  |
| `removal`              | 🔥 Removals and Deprecations |
| `bug`                  | 🐞 Fixes                     |
| `performance`          | 🐎 Performance               |
| `testing`              | 🚨 Testing                   |
| `ci`                   | 👷 Continuous Integration    |
| `documentation`        | 📚 Documentation             |
| `refactoring`          | 🔨 Refactoring               |
| `style`                | 💄 Style                     |
| `dependencies`         | 📦 Dependencies              |

You can update it in [`release-drafter.yml`](https://github.com/NicDom/tia/blob/master/.github/release-drafter.yml).

GitHub creates the `bug`, `enhancement`, and `documentation` labels for you.
Dependabot creates the `dependencies` label.
Create the remaining labels when you need them,
on the _Issues_ tab of your GitHub repository,

## 🛡 License

[![License](https://img.shields.io/github/license/NicDom/tia)](https://github.com/NicDom/tia/blob/master/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/NicDom/tia/blob/master/LICENSE) for more details.

## Issues

If you encounter any problems,
please [file an issue]("https://github.com/NicDom/overloadlib/issues") along with a detailed description.

## 📃 Citation

```bibtex
@misc{tia,
  author = {Niclas D. Gesing},
  title = {TIA: A Tax and Invoice Assistant (TIA)},
  year = {2021},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/NicDom/tia}}
}
```

## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This project was generated with a template inspired by ['Hypermodern Cookiecutter Template'](https://github.com/audreyr/cookiecutter) and [`python-package-template`](https://github.com/TezRomacH/python-package-template).

[bandit_]: https://github.com/PyCQA/bandit
[black_]: https://github.com/psf/black
[click_]: https://click.palletsprojects.com/
[codecov_]: https://codecov.io/
[cookiecutter_]: https://github.com/audreyr/cookiecutter
[coverage.py_]: https://coverage.readthedocs.io/
[dependabot_]: https://dependabot.com/
[flake8_]: http://flake8.pycqa.org
[github_]: https://github.com/
[github actions_]: https://github.com/features/actions
[hypermodern python_]: https://medium.com/@cjolowicz/hypermodern-python-d44485d9d769
[nox_]: https://nox.thea.codes/
[poetry_]: https://python-poetry.org/
[prettier_]: https://prettier.io/
[pypi_]: https://pypi.org/
[read the docs_]: https://readthedocs.org/
[release drafter_]: https://github.com/release-drafter/release-drafter
[safety_]: https://github.com/pyupio/safety
[sphinx_]: http://www.sphinx-doc.org/
[testpypi_]: https://test.pypi.org/
[typeguard_]: https://github.com/agronholm/typeguard
[autodoc_]: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
[mypy_]: http://mypy-lang.org/
[napoleon_]: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
[nox-poetry_]: https://nox-poetry.readthedocs.io/
[pipx_]: https://pipxproject.github.io/pipx/
[pre-commit_]: https://pre-commit.com/
[pyenv_]: https://github.com/pyenv/pyenv
[pytest_]: https://docs.pytest.org/en/latest/
[sphinx-click_]: https://sphinx-click.readthedocs.io/
[xdoctest_]: https://github.com/Erotemic/xdoctest
[coverage session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-coverage-session
[docs session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-docs-session
[docs session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-docs-session
[mypy session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-mypy-session
[pre-commit session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-pre-commit-session
[safety session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-safety-session
[tests session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-tests-session
[typeguard session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-typeguard-session
[xdoctest session]: https://cookiecutter-hypermodern-python.readthedocs.io/en/2020.10.15.1/guide.html#the-xdoctest-session

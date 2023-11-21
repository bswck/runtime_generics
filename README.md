# runtime_generics [![Package version](https://img.shields.io/pypi/v/runtime-generics?label=PyPI)](https://pypi.org/project/runtime-generics) [![Supported Python versions](https://img.shields.io/pypi/pyversions/runtime-generics.svg?logo=python&label=Python)](https://pypi.org/project/runtime-generics)
[![Tests](https://github.com/bswck/runtime_generics/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/runtime_generics/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/runtime_generics.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/runtime_generics)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg?label=Code%20style)](https://github.com/psf/black)
[![License](https://img.shields.io/github/license/bswck/runtime_generics.svg?label=License)](https://github.com/bswck/runtime_generics/blob/master/LICENSE)


# Installation


## For the users 💻
```bash
pip install runtime-generics
```


## For the contributors ❤️
> [!Note]
> If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).

First, [install Poetry](https://python-poetry.org/docs/#installation).<br/>
Poetry is an amazing tool for managing dependencies & virtual environments, building packages and publishing them.

```bash
pipx install poetry
```
<sub>If you encounter any problems, refer to [the official documentation](https://python-poetry.org/docs/#installation) for the most up-to-date installation instructions.</sub>

Be sure to have Python 3.8 installed—if you use [pyenv](https://github.com/pyenv/pyenv#readme), simply run:
```bash
pyenv install 3.8
```

Then, run:
```bash
git clone https://github.com/bswck/runtime_generics
cd runtime_generics
poetry install
pre-commit install --hook-type pre-commit --hook-type pre-push
poetry env use $(cat .python-version)
poetry shell
```

# Legal info
© Copyright by Bartosz Sławecki ([@bswck](https://github.com/bswck)).<br />This software is licensed under the [MIT License](https://github.com/bswck/runtime_generics/blob/main/LICENSE).


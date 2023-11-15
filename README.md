# runtime_generics `1.0.3` [![Supported Python versions](https://img.shields.io/pypi/pyversions/runtime_generics.svg?logo=python&label=Python)](https://pypi.org/project/runtime_generics)
[![Tests](https://github.com/bswck/runtime_generics/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/runtime_generics/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/runtime_generics.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/runtime_generics)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg?label=Code%20style)](https://github.com/psf/black)
[![Package version](https://img.shields.io/pypi/v/runtime_generics?label=PyPI)](https://pypi.org/project/runtime_generics)
[![License](https://img.shields.io/github/license/bswck/runtime_generics.svg?label=License)](https://github.com/bswck/runtime_generics/blob/main/LICENSE)

Highly into type-safe Python code?

_runtime_generics_ is a niche Python library that allows you to reuse type arguments explicitly passed at runtime
to generic classes before instantiation.
The library does two things:
- makes it possible to retrieve the type argument passed to the generic class at runtime
  before the class was instantiated;
- given a parametrized generic class (generic alias),
  it makes every class method use generic alias `cls` instead of the origin class.

# Simple example
3.12+ ([PEP 695](https://peps.python.org/pep-0695) syntax):
```python
from runtime_generics import runtime_generic, select

@runtime_generic
class MyGeneric[T]:
    type_argument: type[T]

    def __init__(self) -> None:
        self.type_argument = select[T](self)

    @classmethod
    def whoami(cls):
        print(f"I am {cls}")

my_generic = MyGeneric[int]()
assert my_generic.type_argument is int
my_generic.whoami()  # I am MyGeneric[int]

```

3.8+:

```python
from __future__ import annotations

from typing import Generic, TypeVar
from runtime_generics import runtime_generic, select

T = TypeVar("T")

@runtime_generic
class MyGeneric(Generic[T]):
    type_argument: type[T]

    def __init__(self) -> None:
        self.type_argument = select[T](self)

    @classmethod
    def whoami(cls):
        print(f"I am {cls}")

my_generic = MyGeneric[int]()
assert my_generic.type_argument is int
my_generic.whoami()  # I am MyGeneric[int]
```

# Installation

## For users 💻
```bash
pip install runtime-generics
```

## For developers ❤️
_Note: If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)._

First, [install Poetry](https://python-poetry.org/docs/#installation).<br/>
Poetry is an amazing tool for managing dependencies & virtual environments, building packages and publishing them.

```bash
curl -sSL https://install.python-poetry.org | python3 -
```
<sub>This way of installing Poetry on Linux is valid as of 2023-10-27.<br/> If you encounter any problems, refer to [the official documentation](https://python-poetry.org/docs/#installation) for the most up-to-date installation instructions.</sub>

Be sure to have Python 3.8 installed—if you use [pyenv](https://github.com/pyenv/pyenv#readme), simply run:
```bash
pyenv install 3.8
```

Then, run:
```bash
git clone https://github.com/bswck/runtime_generics && cd runtime_generics && ./install && poetry shell
```

# Legal info
© Copyright by [bswck](https://github.com/bswck).
This software is licensed under the [MIT License](https://opensource.org/licenses/MIT).

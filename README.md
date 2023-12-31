
# runtime_generics [![skeleton](https://img.shields.io/badge/fe6ed23-skeleton?label=%F0%9F%92%80%20bswck/skeleton&labelColor=black&color=grey&link=https%3A//github.com/bswck/skeleton)](https://github.com/bswck/skeleton/tree/fe6ed23)
[![Package version](https://img.shields.io/pypi/v/runtime-generics?label=PyPI)](https://pypi.org/project/runtime-generics/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/runtime-generics.svg?logo=python&label=Python)](https://pypi.org/project/runtime-generics/)

[![Tests](https://github.com/bswck/runtime_generics/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/runtime_generics/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/runtime_generics.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/runtime_generics)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/github/license/bswck/runtime_generics.svg?label=License)](https://github.com/bswck/runtime_generics/blob/HEAD/LICENSE)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Highly into type-safe Python code?

_runtime_generics_ is a niche Python library that allows you to reuse type arguments explicitly passed at runtime
to generic classes before instantiation.

The library does three things:
- makes it possible to retrieve the type arguments passed to the generic class at runtime
  before the class was instantiated;
- supports basic instance/subclass checking of runtime generic classes;
- given a parametrized generic class (generic alias),
  it makes every class method use generic alias `cls` instead of the origin class.

# A simple example
3.12+ ([PEP 695](https://peps.python.org/pep-0695) syntax):
```python
from runtime_generics import get_type_arguments, runtime_generic

@runtime_generic
class MyGeneric[T]:
    type_argument: type[T]

    def __init__(self) -> None:
        (self.type_argument,) = get_type_arguments(self)

    @classmethod
    def whoami(cls) -> None:
        print(f"I am {cls}")

my_generic = MyGeneric[int]()
assert my_generic.type_argument is int
my_generic.whoami()  # I am MyGeneric[int]

```

3.8+:

```python
from __future__ import annotations

from typing import Generic, TypeVar
from runtime_generics import get_type_arguments, runtime_generic

T = TypeVar("T")

@runtime_generic
class MyGeneric(Generic[T]):
    type_argument: type[T]

    def __init__(self) -> None:
        (self.type_argument,) = get_type_arguments(self)

    @classmethod
    def whoami(cls) -> None:
        print(f"I am {cls}")

my_generic = MyGeneric[int]()
assert my_generic.type_argument is int
my_generic.whoami()  # I am MyGeneric[int]
```

# TDD section
> [!Note]
> Before you read this, you might want to get to know
> the [type theory take on generic types](https://www.python.org/dev/peps/pep-0483/#generic-types).

Test-driven development of runtime generics with inheritance and variance.


```py
# Considering the following hierarchy:
class A[T]:
    pass


class B[T](A[T]):
    pass


class C[X](B[int]):
    pass


class D[Z, Y](C[Y]):
    pass


class E[A, Y](D[A, int]):
    # TypeVar instances are not cached,
    # so Y in this scope is not the same object as Y in D
    pass


class F[T, *Ts](D[T, *Ts]):  # What then???
    pass


# We want the following results:
generic_issubclass(B[int], A[int])  # True
generic_issubclass(B, A[int])  # False
generic_issubclass(B[int], A[str])  # False
generic_issubclass(C[str], B[int])  # True
generic_issubclass(C, B[int])  # True
generic_issubclass(D[float, str], C[str])  # True
generic_issubclass(E[float, str], C[int])  # True
generic_issubclass(E[bytearray, str], D[bytearray, int])  # True
```


# Installation



You might simply install it with pip:

```shell
pip install runtime-generics
```

If you use [Poetry](https://python-poetry.org/), then run:

```shell
poetry add runtime-generics
```

## For contributors

<!--
This section was generated from bswck/skeleton@fe6ed23.
Instead of changing this particular file, you might want to alter the template:
https://github.com/bswck/skeleton/tree/fe6ed23/project/README.md.jinja
-->

> [!Note]
> If you use Windows, it is highly recommended to complete the installation in the way presented below through [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).



1.  Fork the [runtime_generics repository](https://github.com/bswck/runtime_generics) on GitHub.

1.  [Install Poetry](https://python-poetry.org/docs/#installation).<br/>
    Poetry is an amazing tool for managing dependencies & virtual environments, building packages and publishing them.
    You might use [pipx](https://github.com/pypa/pipx#readme) to install it globally (recommended):

    ```shell
    pipx install poetry
    ```

    <sub>If you encounter any problems, refer to [the official documentation](https://python-poetry.org/docs/#installation) for the most up-to-date installation instructions.</sub>

    Be sure to have Python 3.8 installed—if you use [pyenv](https://github.com/pyenv/pyenv#readme), simply run:

    ```shell
    pyenv install 3.8
    ```

1.  Clone your fork locally and install dependencies.

    ```shell
    git clone https://github.com/your-username/runtime_generics path/to/runtime_generics
    cd path/to/runtime_generics
    poetry env use $(cat .python-version)
    poetry install
    ```

    Next up, simply activate the virtual environment and install pre-commit hooks:

    ```shell
    poetry shell
    pre-commit install --hook-type pre-commit --hook-type pre-push
    ```

For more information on how to contribute, check out [CONTRIBUTING.md](https://github.com/bswck/runtime_generics/blob/HEAD/CONTRIBUTING.md).<br/>
Always happy to accept contributions! ❤️


# Legal info
© Copyright by Bartosz Sławecki ([@bswck](https://github.com/bswck)).
<br />This software is licensed under the terms of [MIT License](https://github.com/bswck/runtime_generics/blob/HEAD/LICENSE).

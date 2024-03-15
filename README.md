# runtime_generics [![skeleton](https://img.shields.io/badge/0.0.2rc–166–gf236e83-skeleton?label=%F0%9F%92%80%20bswck/skeleton&labelColor=black&color=grey&link=https%3A//github.com/bswck/skeleton)](https://github.com/bswck/skeleton/tree/0.0.2rc-166-gf236e83) [![Supported Python versions](https://img.shields.io/pypi/pyversions/runtime-generics.svg?logo=python&label=Python)](https://pypi.org/project/runtime-generics/) [![Package version](https://img.shields.io/pypi/v/runtime-generics?label=PyPI)](https://pypi.org/project/runtime-generics/)

[![Tests](https://github.com/bswck/runtime_generics/actions/workflows/test.yml/badge.svg)](https://github.com/bswck/runtime_generics/actions/workflows/test.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/bswck/runtime_generics.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/bswck/runtime_generics)
[![Documentation Status](https://readthedocs.org/projects/runtime-generics/badge/?version=latest)](https://runtime-generics.readthedocs.io/en/latest/?badge=latest)
[![Lifted?](https://tidelift.com/badges/package/pypi/runtime-generics)](https://tidelift.com/subscription/pkg/pypi-runtime-generics?utm_source=pypi-runtime-generics&utm_medium=readme)

Highly into type-safe Python code?

_runtime_generics_ is a niche Python library that allows you to reuse type arguments explicitly passed at runtime
to generic classes before instantiation.

The library does four things:
- makes it possible to retrieve the type arguments passed to the generic class at runtime
  before the class was instantiated: `get_type_arguments()`, `get_alias()`;
- given a parametrized generic class (generic alias),
  makes every class method use generic alias `cls` instead of the origin class
  (unless decorated with `@no_alias`);
- offers facilities to find how parent classes are parametrized (
  e.g. if `Foo[T]` inherits from `Dict[str, T]`,
  finds that `Dict[str, int]` is a parent for `Foo[int]`
  ): `get_parents()`;
- exposes utilities that allow to inspect C3-linearized MROs of runtime generics
  and type-check them with variance support: `get_mro()`, `type_check()`.

# A simple example
3.12+ ([PEP 695](https://peps.python.org/pep-0695) syntax):
```python
from __future__ import annotations

import io
from typing import TYPE_CHECKING

from runtime_generics import get_alias, get_type_arguments, runtime_generic, type_check

if TYPE_CHECKING:
    from typing import IO, Literal, overload


@runtime_generic
class IOWrapper[T: str | bytes]:
    data_type: type[T]

    def __init__(self, stream: IO[T]) -> None:
        (self.data_type,) = get_type_arguments(self)
        self.stream = stream

    if TYPE_CHECKING:
        @overload
        def is_binary(self: IOWrapper[bytes]) -> Literal[True]: ...

        @overload
        def is_binary(self: IOWrapper[str]) -> Literal[False]: ...

    def is_binary(self) -> bool:
        # alternatively here: `self.data_type == bytes`
        return type_check(self, IOWrapper[bytes])

    def __repr__(self) -> str:
        return f"<{get_alias(self)} object at ...>"


my_binary_data = IOWrapper[bytes](io.BytesIO(b"foo"))
assert my_binary_data.data_type is bytes
assert my_binary_data.is_binary()
assert repr(IOWrapper[str](io.StringIO())) == "<__main__.IOWrapper[str] object at ...>"
```

3.8+:

```python
from __future__ import annotations

import io
from typing import TYPE_CHECKING, Generic, TypeVar

from runtime_generics import get_alias, get_type_arguments, runtime_generic, type_check

if TYPE_CHECKING:
    from typing import IO, Literal, overload

T = TypeVar("T", str, bytes)


@runtime_generic
class IOWrapper(Generic[T]):
    data_type: type[T]

    def __init__(self, stream: IO[T]) -> None:
        (self.data_type,) = get_type_arguments(self)
        self.stream = stream

    if TYPE_CHECKING:
        @overload
        def is_binary(self: IOWrapper[bytes]) -> Literal[True]: ...

        @overload
        def is_binary(self: IOWrapper[str]) -> Literal[False]: ...

    def is_binary(self) -> bool:
        # alternatively here: `self.data_type == bytes`
        return type_check(self, IOWrapper[bytes])

    def __repr__(self) -> str:
        return f"<{get_alias(self)} object at ...>"


my_binary_data = IOWrapper[bytes](io.BytesIO(b"foo"))
assert my_binary_data.data_type is bytes
assert my_binary_data.is_binary()
assert repr(IOWrapper[str](io.StringIO())) == "<__main__.IOWrapper[str] object at ...>"
```

# For enterprise
Available as part of the Tidelift Subscription.

This project and the maintainers of thousands of other packages are working with Tidelift to deliver one enterprise subscription that covers all of the open source you use.

[Learn more here](https://tidelift.com/subscription/pkg/pypi-runtime-generics?utm_source=pypi-runtime-generics&utm_medium=referral&utm_campaign=github).

## Security contact information
To report a security vulnerability, please use the
[Tidelift security contact](https://tidelift.com/security).<br>
Tidelift will coordinate the fix and disclosure.

# Installation
You might simply install it with pip:

```shell
pip install runtime-generics
```

If you use [Poetry](https://python-poetry.org/), then you might want to run:

```shell
poetry add runtime-generics
```

## For contributors
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!--
This section was generated from bswck/skeleton@0.0.2rc-166-gf236e83.
Instead of changing this particular file, you might want to alter the template:
https://github.com/bswck/skeleton/tree/0.0.2rc-166-gf236e83/project/README.md.jinja
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
    pre-commit install
    ```

For more information on how to contribute, check out [CONTRIBUTING.md](https://github.com/bswck/runtime_generics/blob/HEAD/CONTRIBUTING.md).<br/>
Always happy to accept contributions! ❤️

# Legal info
© Copyright by Bartosz Sławecki ([@bswck](https://github.com/bswck)).
<br />This software is licensed under the terms of [MIT License](https://github.com/bswck/runtime_generics/blob/HEAD/LICENSE).

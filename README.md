# runtime_generics `1.0.2`
[![Supported Python versions](https://img.shields.io/pypi/pyversions/runtime_generics.svg?label=Python)](https://pypi.org/project/runtime_generics)
[![Package version](https://img.shields.io/pypi/v/runtime_generics?color=%2334D058&label=PyPI%20Package)](https://pypi.org/project/runtime_generics)
[![License](https://img.shields.io/github/license/bswck/runtime_generics.svg?label=License)](https://github.com/pydantic/pydantic/blob/main/LICENSE)

Highly into type-safe Python code?

_runtime_generics_ is a niche Python library that allows you to reuse type arguments explicitly passed at runtime
to generic classes before instantiation.

# Simple example
3.12+ ([PEP 695](https://peps.python.org/pep-0695) syntax):
```python
from runtime_generics import runtime_generic, get_arg

@runtime_generic
class MyGeneric[T]:
    type_argument: type[T]

    def __init__(self) -> None:
        self.type_argument = get_arg(self)

my_generic = MyGeneric[int]()
assert my_generic.type_argument is int
```

3.8+:

```python
from __future__ import annotations

from typing import Generic, TypeVar
from runtime_generics import runtime_generic, get_arg

T = TypeVar("T")

@runtime_generic
class MyGeneric(Generic[T]):
    type_argument: type[T]

    def __init__(self) -> None:
        self.type_argument = get_arg(self)

my_generic = MyGeneric[int]()
assert my_generic.type_argument is int
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

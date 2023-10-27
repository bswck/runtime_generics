# `runtime_generics` 0.1.2
Highly into typing your Python code? Ever wanted to reuse type arguments of your generic classes at runtime, in their instances?

If so, then this is for you!

_runtime_generics_ is a Python library that allows you to access type arguments of your generic classes through their instances at runtime.

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
pip install runtime_generics
```

## For developers ❤️
First, [install Poetry](https://python-poetry.org/docs/#installation).
Poetry is an amazing tool for managing dependencies & virtual environments, building packages and publishing them.
Be sure to have Python 3.8 installed. If you use pyenv, simply run:
```bash
pyenv install 3.8
```

Then, run:
```bash
git clone https://github.com/bswck/runtime_generics && cd runtime_generics && ./install && poetry shell
```

Since you are a developer, I assume that you use Linux.
Good luck!

# Legal info
© Copyright by [bswck](https://github.com/bswck).

[All rights explained in the LICENSE file](/LICENSE).
This software is licensed under the [MIT License](https://opensource.org/licenses/MIT).

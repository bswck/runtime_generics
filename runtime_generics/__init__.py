"""
runtime_generics — A library for working with runtime generics in Python.

This library provides a decorator that allows you to mark a class as
a 'runtime generic': after instantiation, the class will have a `__args__` attribute
that contains the type arguments of the instance.

You can conveniently access the type arguments using the
`get_args` function, or the `get_arg` function if the class has exactly one type.

Examples
--------
Python 3.8+
>>> from typing import Generic, TypeVar
>>> from runtime_generics import get_arg, runtime_generic
>>> T = TypeVar("T")
...
>>> @runtime_generic
... class Foo(Generic[T]):
...     def __init__(self) -> None:
...         print(f"Hello! I am Foo[{get_arg(self).__name__}] :)")
...
>>> Foo[int]()
Hello! I am Foo[int] :)

Python 3.12+
>>> from runtime_generics import get_arg, runtime_generic
...
>>> @runtime_generic
... class Foo[T]:
...     def __init__(self) -> None:
...         print(f"Hello! I am Foo[{get_arg(self).__name__}] :)")
...
>>> Foo[int]()
Hello! I am Foo[int] :)

"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Protocol, TypeVar
from typing import _GenericAlias as _typing_GenericAlias  # type: ignore[attr-defined]
from typing import get_args as _typing_get_args

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = (
    "runtime_generic",
    "get_args",
    "get_arg",
    "get_argument",
)


class GenericProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for runtime generics."""

    def __class_getitem__(
        cls,
        item: tuple[type[Any], ...],
    ) -> Callable[..., Any]:  # pragma: no cover
        ...


T = TypeVar("T", bound=GenericProtocol)


class _RuntimeGenericArgs(tuple):  # type: ignore[type-arg]
    """Marker class for type arguments of runtime generics."""

    __slots__ = ()


def _note_args(cls: type[Any], alias: Any, /, *args: object, **kwargs: object) -> Any:
    __tracebackhide__ = True  # pylint: disable=unused-variable
    instance: Any = cls.__new__(cls, *args, **kwargs)
    instance.__args__ = _RuntimeGenericArgs(_typing_get_args(alias))
    instance.__init__(*args, **kwargs)  # pylint: disable=unnecessary-dunder-call
    return instance


class _GenericFactoryProxy(
    _typing_GenericAlias,  # type: ignore[misc,call-arg]
    _root=True,
):
    def __call__(self, *args: object, **kwargs: object) -> Any:
        return partial(_note_args, self.__origin__, self)(*args, **kwargs)


class _RuntimeGenericDescriptor:  # pylint: disable=too-few-public-methods
    def __init__(self, factory: Callable[..., Any]) -> None:
        self.factory = factory

    def __get__(
        self,
        instance: object,
        owner: type[Any] | None = None,
    ) -> Callable[..., Any]:
        __tracebackhide__ = True  # pylint: disable=unused-variable
        cls = owner
        if cls is None:  # pragma: no cover
            # Probably redundant, but we support this case anyway
            # https://docs.python.org/3/reference/datamodel.html#object.__get__
            cls = type(instance)
        return lambda args: _GenericFactoryProxy(cls, args)


def runtime_generic(cls: type[T]) -> type[T]:
    """
    Mark a class as a runtime generic.

    This is a class decorator that dynamically adds a `__class_getitem__` descriptor
    to the class. This method returns a callable that takes type arguments and returns
    a new instance of the class with the `__args__` attribute set to the type arguments.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo:
    ...     pass
    >>> Foo[int]().__args__
    (int,)
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable
    descriptor = _RuntimeGenericDescriptor(cls.__class_getitem__)
    cls.__class_getitem__ = descriptor  # type: ignore[assignment,method-assign]
    return cls


def get_args(instance: object) -> tuple[Any, ...]:
    """
    Get the type arguments of a runtime generic instance.

    Parameters
    ----------
    instance
        An instance of a class that was decorated with `@runtime_generic`.

    Returns
    -------
    args
        The type arguments of the instance.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo[T]:
    ...     pass
    >>> args: tuple[type[int]] = get_args(Foo[int]())
    >>> args
    (<class 'int'>,)
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable
    args = getattr(instance, "__args__", ())
    return tuple(args) if isinstance(args, _RuntimeGenericArgs) else ()


def get_arg(instance: object) -> Any:
    """
    Get the single type argument of a runtime generic instance.

    Parameters
    ----------
    instance
        An instance of a class that was decorated with `@runtime_generic`.

    Returns
    -------
    arg
        The single type argument of the instance.

    Raises
    ------
    ValueError
        If the instance has more than one type argument.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo[T]:
    ...     pass
    >>> arg: type[int] = get_arg(Foo[int]())
    >>> arg
    <class 'int'>
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable
    args = get_args(instance)
    if len(args) != 1:
        msg = (
            f"Expected instance of runtime generic with exactly one type argument, "
            f"got {instance!r} with {len(args)} type arguments."
        )
        raise ValueError(msg)
    return args[0]


get_argument = get_arg

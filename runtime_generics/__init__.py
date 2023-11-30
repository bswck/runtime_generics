"""
runtime_generics — A library for working with runtime generics in Python.

This library provides a decorator that allows you to mark a class as
a 'runtime generic': after instantiation, the class will have a `__args__` attribute
that contains the type arguments of the instance.

Examples
--------
```python

>>> # Python 3.8+
... from __future__ import annotations
... from typing import Generic, TypeVar
... from runtime_generics import get_type_arguments, runtime_generic
...
... T = TypeVar("T")
...
... @runtime_generic
... class MyGeneric(Generic[T]):
...     type_argument: type[T]
...
...     def __init__(self) -> None:
...         (self.type_argument,) = get_type_arguments(self)
...
...     @classmethod
...     def whoami(cls) -> None:
...        print(f"I am {cls}")
...
>>> # Python 3.12+
... from runtime_generics import get_type_arguments, runtime_generic
...
... @runtime_generic
... class MyGeneric[T]:
...     type_argument: type[T]
...
...     def __init__(self) -> None:
...         (self.type_argument,) = get_type_arguments(self)
...
...     @classmethod
...     def whoami(cls) -> None:
...         print(f"I am {cls}")
...
>>> my_generic = MyGeneric[int]()
>>> my_generic.type_argument
<class 'int'>
>>> my_generic.whoami()
I am MyGeneric[int]
```

"""

from __future__ import annotations

from types import MethodType
from typing import TYPE_CHECKING, Any, TypeVar, overload
from typing import _GenericAlias as _typing_GenericAlias  # type: ignore[attr-defined]
from typing import get_args as _typing_get_args

from typing_extensions import TypeVarTuple

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import ParamSpec, Self, TypeGuard

    P = ParamSpec("P")
    R = TypeVar("R")

try:
    from typing import _TypingEmpty  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    _TypingEmpty = ()

try:
    # Not removed in Python 3.13, but not documented either.
    from typing import _TypingEllipsis  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    _TypingEllipsis = ...


__all__ = (
    "get_type_arguments",
    "generic_isinstance",
    "no_alias",
    "runtime_generic",
)


GenericClass = TypeVar("GenericClass", bound=Any)
GenericArguments = TypeVarTuple("GenericArguments")


class GenericArgs(tuple):  # type: ignore[type-arg]
    """Marker class for type arguments of runtime generics."""

    __slots__ = ()


class _ClassMethodProxy:
    def __init__(
        self,
        alias_proxy: _AliasProxy,
        cls_method: classmethod[Any, Any, Any],
    ) -> None:
        self.alias_proxy = alias_proxy
        self.cls_method = cls_method

    def __get__(
        self,
        instance: object,
        owner: type[object] | None = None,
    ) -> MethodType:
        return MethodType(
            self.cls_method.__func__,
            self.alias_proxy.copy_with(owner=owner),
        )


ALIAS_PROXY_INTERNS: dict[tuple[type[Any], GenericArgs], _AliasProxy] = {}


def _normalize_generic_args(
    args: type[Any] | tuple[Any, ...],
) -> GenericArgs:
    """Normalize type arguments to a canonical form."""
    if not isinstance(args, tuple):
        args = (args,)
    return GenericArgs(
        () if arg is _TypingEmpty else ... if arg is _TypingEllipsis else arg
        for arg in args
    )


class _AliasProxy(
    _typing_GenericAlias,  # type: ignore[misc,call-arg]
    _root=True,
):
    __args__: tuple[type[Any], ...]

    def __new__(
        cls,
        origin: type[GenericClass],
        params: tuple[Any, ...],
        **_kwds: Any,
    ) -> Self:
        # A factory constructor--returns an existing instance if possible.
        args = _normalize_generic_args(params)
        self = ALIAS_PROXY_INTERNS.get((origin, args))
        if self is None:
            self = super().__new__(cls)
        return self

    def __init__(
        self,
        origin: type[GenericClass],
        params: tuple[Any, ...],
        *,
        cascade: bool = True,
        **kwds: Any,
    ) -> None:
        super().__init__(origin, params, **kwds)
        self.__cascade__ = cascade
        self.__args__ = args = GenericArgs(self.__args__)

        ALIAS_PROXY_INTERNS[(origin, args)] = self
        cls_dict = vars(origin)
        for cls_method_name, cls_method in cls_dict.items():
            if isinstance(cls_method, classmethod) and not getattr(
                cls_method,
                "__no_alias__",
                False,
            ):
                setattr(
                    origin,
                    cls_method_name,
                    _ClassMethodProxy(self, cls_method),
                )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        origin = self.__origin__
        instance: Any = origin.__new__(origin, *args, **kwargs)
        instance.__args__ = self.__args__
        instance.__init__(*args, **kwargs)
        return instance

    def copy_with(
        self,
        params: tuple[type[object], ...] | None = None,
        owner: type[object] | None = None,
    ) -> _AliasProxy:
        """Create a copy of the alias proxy with a new owner or new type arguments."""
        return _AliasProxy(
            owner or self.__origin__,
            params or self.__args__,
            cascade=self.__cascade__,
        )


class _RuntimeGenericDescriptor:
    def __init__(self, *, cascade: bool) -> None:
        self.cascade = cascade

    def __get__(
        self,
        instance: object,
        owner: type[Any],
    ) -> Callable[..., _AliasProxy]:
        # X.__class__ instead of type(X) to honor .__class__ descriptor behavior
        return lambda args: _AliasProxy(owner, args, cascade=self.cascade)


@overload
def runtime_generic(
    cls: None = None,
    *,
    cascade: bool = ...,
) -> Callable[[type[GenericClass]], type[GenericClass]]:
    ...


@overload
def runtime_generic(
    cls: type[GenericClass],
    *,
    cascade: bool = ...,
) -> type[GenericClass]:
    ...


def runtime_generic(
    cls: type[GenericClass] | None = None,
    *,
    cascade: bool = True,
) -> type[GenericClass] | Callable[[type[GenericClass]], type[GenericClass]]:
    """
    Mark a class as a runtime generic.

    This is a class decorator that dynamically adds a `__class_getitem__` descriptor
    to the class. This method returns a callable that takes type arguments and returns
    a new instance of the class with the `__args__` attribute set to the type arguments.

    If `cascade` is `True`, the `__class_getitem__` descriptor will be added to all
    subclasses of the decorated class as they are created.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo:
    ...     pass
    >>> Foo[int]().__args__
    (int,)
    """
    if cls is None:
        return lambda cls: runtime_generic(cls, cascade=cascade)
    descriptor = _RuntimeGenericDescriptor(cascade=cascade)
    cls.__class_getitem__ = descriptor
    return cls


def get_type_arguments(instance: object) -> tuple[type[Any], ...]:
    """
    Get all type arguments of a runtime generic instance.

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
    >>> args: tuple[type[int]] = get_type_arguments(Foo[int]())
    >>> args
    (<class 'int'>,)
    """
    args = getattr(instance, "__args__", ())
    return tuple(args) if isinstance(args, GenericArgs) else _typing_get_args(args)


def no_alias(cls_method: Callable[P, R]) -> Callable[P, R]:
    """Mark a classmethod as not being passed a generic alias in place of cls."""
    cls_method.__no_alias__ = True  # type: ignore[attr-defined]
    return cls_method


def generic_isinstance(obj: object, cls: type[GenericClass]) -> TypeGuard[GenericClass]:
    """
    Perform an `isinstance()` check on a runtime generic.

    Currently only invariant type arguments are supported, without argument inheritance.
    """
    # Not defining __instancecheck__() is intentional.
    # Using isinstance() with a parametrized runtime generic
    # would result in a type error, even when the custom subclass of GenericAlias
    # implements __instancecheck__() correctly.
    if get_type_arguments(obj) == get_type_arguments(cls):
        return issubclass(obj.__class__, cls.__origin__)
    return generic_issubclass(obj.__class__, cls)


def generic_issubclass(
    cls_obj: Any,
    cls: type[GenericClass],
) -> TypeGuard[GenericClass]:
    """
    Perform an `issubclass()` check on a runtime generic.

    Currently only invariant type arguments are supported, without argument inheritance.
    """
    # Not defining __subclasscheck__() is intentional.
    # Using issubclass() with a parametrized runtime generic
    # would result in a type error, even when the custom subclass of GenericAlias
    # implements __subclasscheck__() correctly.
    if isinstance(cls, _typing_GenericAlias):
        if isinstance(cls_obj, _typing_GenericAlias) and not issubclass(
            cls_obj.__origin__,
            cls.__origin__,
        ):
            return False
        return get_type_arguments(cls_obj) == get_type_arguments(cls)
    if isinstance(cls_obj, _typing_GenericAlias):
        return get_type_arguments(cls_obj) in (cls.__parameters__, (Any,))
    return issubclass(cls_obj, cls)

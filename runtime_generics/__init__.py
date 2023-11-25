"""
runtime_generics — A library for working with runtime generics in Python.

This library provides a decorator that allows you to mark a class as
a 'runtime generic': after instantiation, the class will have a `__args__` attribute
that contains the type arguments of the instance.

You can conveniently access all type arguments of a generic class instance
using the `get_all_arguments` function, or retrieve a specific part of arguments
with the `get_arguments` using a selector class (see below).

Examples
--------
```python

>>> # Python 3.8+
... from __future__ import annotations
... from typing import Generic, TypeVar
... from runtime_generics import runtime_generic, select
...
... T = TypeVar("T")
...
... @runtime_generic
... class MyGeneric(Generic[T]):
...     type_argument: type[T]
...
...     def __init__(self) -> None:
...         self.type_argument = select[T](self)
...
...     @classmethod
...     def whoami(cls):
...        print(f"I am {cls}")
...
>>> # Python 3.12+
... from runtime_generics import runtime_generic, select
...
... @runtime_generic
... class MyGeneric[T]:
...     type_argument: type[T]
...
...     def __init__(self) -> None:
...         self.type_argument = select[T](self)
...
...     @classmethod
...     def whoami(cls):
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

from itertools import chain
from types import MethodType
from typing import TYPE_CHECKING, Any, ForwardRef, Generic, Protocol, TypeVar
from typing import _GenericAlias as _typing_GenericAlias  # type: ignore[attr-defined]
from typing import get_args as _typing_get_args

from typing_extensions import TypeVarTuple, Unpack, deprecated

if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = (
    "runtime_generic",
    "get_arg",
    "get_args",
    "get_argument",
    "get_arguments",
    "get_all_args",
    "get_all_arguments",
    "FunctionalSelectorMixin",
    "Select",
    "Index",
    "select",
    "index",
)


class _GenericMetaclassProtocol(type(Protocol)):  # type: ignore[misc]
    __parameters__: tuple[type[Any], ...]


class _GenericProtocol(
    Protocol,
    metaclass=_GenericMetaclassProtocol,
):  # pylint: disable=too-few-public-methods
    """Protocol for runtime generics."""

    def __class_getitem__(
        cls,
        item: tuple[type[Any], ...],
    ) -> Callable[..., Any]:  # pragma: no cover
        ...


GenericClass = TypeVar("GenericClass", bound=_GenericProtocol)
GenericArguments = TypeVarTuple("GenericArguments")


class _RuntimeGenericArgs(tuple):  # type: ignore[type-arg]
    """Marker class for type arguments of runtime generics."""

    __slots__ = ()


def _try_forward_ref(obj: str) -> str | ForwardRef:
    try:
        return ForwardRef(obj)
    except SyntaxError:
        return obj


class _ClassMethodProxy:
    def __init__(
        self,
        alias_proxy: _AliasProxy,
        cls_method: classmethod[Any, Any, Any],
    ) -> None:
        self.alias_proxy = alias_proxy
        self.cls_method = cls_method
        self.__func__ = self.cls_method.__func__

    def __get__(self, instance: object, owner: type[Any] | None = None) -> MethodType:
        return MethodType(self.cls_method.__func__, self.alias_proxy)


class _AliasProxy(
    _typing_GenericAlias,  # type: ignore[misc,call-arg]
    _root=True,
):
    def __init__(
        self,
        origin: type[GenericClass],
        params: tuple[Any, ...],
        **kwds: Any,
    ) -> None:
        patched_params = tuple(
            _try_forward_ref(param) if isinstance(param, str) else param
            for param in (params if isinstance(params, tuple) else (params,))
        )
        super().__init__(origin, patched_params, **kwds)
        cls_dict = vars(origin)
        for cls_method_name, cls_method in cls_dict.items():
            if isinstance(cls_method, classmethod):
                setattr(
                    origin,
                    cls_method_name,
                    _ClassMethodProxy(self, cls_method),
                )

    def __get_arguments__(
        self,
        instance: GenericClass,
        *,
        _origin: type[Any] | None = None,
    ) -> Any:
        method = object.__getattribute__(
            _origin or self.__origin__,
            "__get_arguments__",
        )
        return method.__func__(self, instance)

    # @override?
    def copy_with(self, params: tuple[Any, ...] = ()) -> _AliasProxy:
        return _AliasProxy(self.__origin__, params, name=self._name, inst=self._inst)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        origin = self.__origin__
        if issubclass(origin, FunctionalSelectorMixin):
            # Functional selector API
            arguments = self.__get_arguments__(*args, **kwargs, _origin=origin.__base__)
            if any(isinstance(arg, slice) for arg in self.__args__):
                return arguments
            if len(arguments) == 1:
                return arguments[0]
            return arguments
        instance: Any = origin.__new__(origin, *args, **kwargs)
        instance.__args__ = _RuntimeGenericArgs(_typing_get_args(self))
        instance.__init__(*args, **kwargs)  # pylint: disable=unnecessary-dunder-call
        return instance


class _RuntimeGenericDescriptor:  # pylint: disable=too-few-public-methods
    def __get__(
        self,
        instance: object,
        owner: type[Any] | None = None,
    ) -> Callable[..., Any]:
        cls = owner
        if cls is None:  # pragma: no cover
            # Probably redundant, but we support this case anyway
            # https://docs.python.org/3/reference/datamodel.html#object.__get__
            # X.__class__ instead of type(X) to honor .__class__ descriptor behavior
            cls = instance.__class__
        return lambda args: _AliasProxy(cls, args)


def runtime_generic(cls: type[GenericClass]) -> type[GenericClass]:
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
    descriptor = _RuntimeGenericDescriptor()
    cls.__class_getitem__ = descriptor  # type: ignore[assignment,method-assign]
    return cls


def get_all_arguments(instance: object) -> tuple[Any, ...]:
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
    >>> args: tuple[type[int]] = get_all(Foo[int]())
    >>> args
    (<class 'int'>,)
    """
    args = getattr(instance, "__args__", ())
    return (
        tuple(args) if isinstance(args, _RuntimeGenericArgs) else _typing_get_args(args)
    )


get_all_args = get_all_arguments


class FunctionalSelectorMixin:
    """
    Mixin for functional selectors.

    TODO(bswck): documentation.
    """


@runtime_generic
class Select(Generic[Unpack[GenericArguments]]):
    """Select[] selector. Selects provided type variables."""

    @classmethod
    def __get_arguments__(
        cls,
        instance: GenericClass,
    ) -> tuple[Any, ...]:
        """Return the selected type arguments."""
        arguments = get_all_arguments(instance)
        tvars = _typing_get_args(cls)
        all_tvars = instance.__class__.__parameters__

        tvars_to_arguments = {}
        argument_iter = iter(arguments)
        for tvar in all_tvars:
            if isinstance(tvar, TypeVarTuple):
                tvars_to_arguments[Unpack[tvar]] = tuple(argument_iter)
                break
            tvars_to_arguments[tvar] = (next(argument_iter),)
        return tuple(chain.from_iterable(tvars_to_arguments[tvar] for tvar in tvars))


class _FunctionalSelect(
    Select[Unpack[GenericArguments]],
    Generic[Unpack[GenericArguments]],
    FunctionalSelectorMixin,
):
    """
    Functional version of `Select`.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo[T1, T2]:
    ...     pass
    ...
    >>> select["T1"](Foo[int, str]())
    <class 'int'>
    """


select: Any = _FunctionalSelect


def _map_index_argument(obj: object, /, all_tvars: tuple[type[Any], ...]) -> int | None:
    return obj if isinstance(obj, int) or obj is None else all_tvars.index(obj)


@runtime_generic
class _Index(Generic[Unpack[GenericArguments]]):
    """Note: right-inclusive."""

    @classmethod
    def __get_arguments__(cls, instance: GenericClass) -> tuple[Any, ...]:
        arguments = get_all_arguments(instance)
        all_tvars = instance.__class__.__parameters__
        result: list[Any] = []

        for index_object in _typing_get_args(cls):
            if isinstance(index_object, slice):
                start, stop, step = (
                    _map_index_argument(obj, all_tvars)
                    for obj in (
                        index_object.start,
                        index_object.stop,
                        index_object.step,
                    )
                )
                result.extend(
                    arguments[start : stop if stop is None else stop + 1 : step],
                )
            else:
                err = f"Expected an integer or a type variable, got {index_object!r}"
                try:
                    argument = _map_index_argument(index_object, all_tvars)
                except ValueError:
                    raise TypeError(err) from None
                else:
                    if argument is None:
                        raise TypeError(err) from None
                result.append(arguments[argument])
        return tuple(result)


# A nuclear workaround for any dubious problems with indexing/slicing,
# such as in cases like Index[5] or Index[1:3, 2:5].
Index: Any = _Index


class _FunctionalIndex(
    _Index[Unpack[GenericArguments]],
    Generic[Unpack[GenericArguments]],
    FunctionalSelectorMixin,
):
    """
    Functional version of `Index`.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo[T1, T2]:
    ...     pass
    ...
    >>> index[1](Foo[int, str]())
    <class 'str'>
    """


index: Any = _FunctionalIndex


def get_arguments(
    instance: object,
    argument_type: type[
        Select[Unpack[GenericArguments]] | Index[Unpack[GenericArguments]]
    ]
    | None = None,
) -> tuple[Any, ...]:
    """
    Get the single type argument of a runtime generic instance.

    Parameters
    ----------
    instance
        An instance of a class that was decorated with `@runtime_generic`.

    argument_type
        A selector of the type argument. If None (default), the instance
        of a generic class is assumed to have only one type argument
        and if that is untrue, a ValueError is raised.

    local_ns
        Local namespace to resolve deferred type arguments from.

    global_ns
        Global namespace to resolve deferred type arguments from.

    stack_offset
        Stack offset: index of the underlying frame to the caller in the stack
        (`inspect.stack()`).

    Returns
    -------
    args
        The type arguments of the instance.

    Raises
    ------
    ValueError
        If the instance has more than one type argument.

    Examples
    --------
    >>> @runtime_generic
    ... class Foo[T]:
    ...     pass
    >>> args: tuple[type[int]] = get_arguments(Foo[int]())
    >>> args
    (<class 'int'>,)
    """
    arguments = get_all_arguments(instance)

    if argument_type is None:
        return arguments

    return argument_type.__get_arguments__(instance)


get_args = get_arguments
get_arg = get_argument = deprecated(
    f"{__name__}.get_arg()/.get_argument() is deprecated"
    f"use {__name__}.get_arguments() instead",
    category=DeprecationWarning,
    stacklevel=2,
)(get_arguments)

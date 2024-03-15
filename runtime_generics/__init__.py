# SPDX-License-Identifier: MIT
# (C) 2024-present Bartosz Sławecki (bswck)
"""
`runtime_generics`.

This library provides a decorator that allows you to mark a class as
a 'runtime generic': after instantiation, the class will have a `__args__` attribute
that contains the type arguments of the instance.

Examples
--------
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

"""

from __future__ import annotations

import inspect
import typing
from collections import defaultdict
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from functools import partial
from itertools import islice, takewhile
from types import MethodType
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast
from typing import _GenericAlias as _typing_GenericAlias  # type: ignore[attr-defined]
from typing import get_args as _typing_get_args

from backframe import map_args_to_identifiers
from typing_extensions import TypeVarTuple, Unpack

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from typing_extensions import ParamSpec, Self

    _P = ParamSpec("_P")
    _R = TypeVar("_R")

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
    "get_alias",
    "get_type_arguments",
    "get_parametrization",
    "get_parents",
    "no_alias",
    "runtime_generic_patch",
    "runtime_generic",
    "runtime_generic_proxy",
    "type_check",
)

_NO_ALIAS_FLAG = "__no_alias__"
_MRO_ENTRY_SLUG = "_runtime_generic_mro_entry_"

unique_mro_entries: dict[type[Any], Any] = {}
parent_aliases_registry: defaultdict[Any, list[Any]] = defaultdict(list)
_typevar_cache: dict[str, Any] = {}


def _get_cached_typevar(typevar_name: str) -> Any:
    try:
        typevar = _typevar_cache[typevar_name]
    except KeyError:
        typevar = _typevar_cache[typevar_name] = cast("Callable[[str], Any]", TypeVar)(
            typevar_name,  # pyright hack
        )
    return typevar


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


ALIAS_PROXY_CACHE_MAXSIZE: int = 128
ALIAS_PROXY_CACHE: dict[tuple[type[Any], GenericArgs], _AliasProxy] = {}


def _normalize_generic_args(
    # I remember `typing.Type[CT_co]`; should be fine to annotate as `type[object]`.
    # `tuple[...]` params are also covariant.
    args: type[object] | tuple[object, ...],
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
        origin: Any,
        params: tuple[Any, ...],
        _result_type: Any = None,
        **_kwds: Any,
    ) -> Self:
        # A factory constructor--returns an existing instance if possible.
        args = _normalize_generic_args(params)
        self = ALIAS_PROXY_CACHE.get((origin, args))
        if self is None:
            self = super().__new__(cls)
        return self

    def __init__(
        self,
        origin: Any,
        params: tuple[Any, ...],
        result_type: Any = None,
        **kwds: Any,
    ) -> None:
        super().__init__(origin, params, **kwds)
        self.__args__ = args = GenericArgs(self.__args__)
        result_type = result_type or self.__origin__

        default_factory = partial(_typing_GenericAlias, result_type)

        if isinstance(result_type, type):
            result_factory = getattr(
                result_type,
                "__class_getitem__",
                None,
            )
        else:
            result_factory = getattr(
                result_type,
                "__getitem__",
                None,
            )

        if result_factory is None or isinstance(result_factory, _AliasFactory):
            result_factory = default_factory

        self.__result__ = result_factory(args)

        while len(ALIAS_PROXY_CACHE) > ALIAS_PROXY_CACHE_MAXSIZE:  # pragma: no cover
            ALIAS_PROXY_CACHE.popitem()
        ALIAS_PROXY_CACHE[(origin, args)] = self

        for name, obj in vars(origin).items():
            if isinstance(obj, classmethod) and not getattr(obj, _NO_ALIAS_FLAG, False):
                setattr(origin, name, _ClassMethodProxy(self, obj))

    def __mro_entries__(self, bases: tuple[type[Any], ...]) -> Any:
        mro_entries_iter = iter(super().__mro_entries__(bases))
        mro_entries = (
            *takewhile(
                lambda mro_entry: not mro_entry.__name__.startswith(_MRO_ENTRY_SLUG),
                mro_entries_iter,
            ),
        )
        unique_mro_entry = type(
            _MRO_ENTRY_SLUG + f"{id(self):x}",
            (*mro_entries_iter,),
            {},
        )
        unique_mro_entries[unique_mro_entry] = self
        return *mro_entries, unique_mro_entry

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        origin = self.__origin__
        instance: Any = origin.__new__(origin, *args, **kwargs)
        runtime_generic_init(instance, args=self.__args__, origin=self.__origin__)
        instance.__init__(*args, **kwargs)
        return instance

    def copy_with(
        self,
        params: tuple[type[object], ...] | None = None,
        owner: type[object] | None = None,
    ) -> _AliasProxy:
        """Create a copy of the alias proxy with a new owner or new type arguments."""
        return _AliasProxy(owner or self.__origin__, params or self.__args__)


@dataclass
class _AliasFactory:
    owner: type[Any]
    result_type: Any = None

    def __call__(self, args: tuple[Any, ...]) -> Any:
        return _AliasProxy(self.owner, args, self.result_type)


@dataclass
class _RuntimeGenericDescriptor:
    result_type: Any = None

    def __get__(
        self,
        instance: object,
        owner: type[Any],
    ) -> Callable[..., _AliasProxy]:
        # X.__class__ instead of type(X) to honor .__class__ descriptor behavior
        return _AliasFactory(owner, self.result_type)


def _has_origin(cls: object) -> bool:
    # If you're thinking about making a typing.Protocol
    # for typing this as a TypeGuard, I assure you I thought
    # about that too and it's not worth it.
    return hasattr(cls, "__origin__")


def _replace_type_arguments_impl(
    replacements: dict[object, Any],
    args: tuple[Any, ...],
) -> Iterator[Any]:
    for arg in args:
        if isinstance(arg, TypeVarTuple):
            yield from _normalize_generic_args(
                replacements.get(arg, ()),
            )
        elif _has_origin(arg):
            if arg.__origin__ is Unpack:
                yield from _replace_type_arguments(replacements, arg.__args__)
            else:
                yield _typing_GenericAlias(
                    arg.__origin__,
                    _replace_type_arguments(replacements, arg.__args__),
                )
        else:
            replaced = replacements.get(arg, arg)
            if isinstance(replaced, TypeVar):
                replaced = Any
            yield replaced


def _replace_type_arguments(
    replacements: dict[Any, Any],
    args: tuple[Any, ...],
) -> tuple[Any, ...]:
    return tuple(_replace_type_arguments_impl(replacements, args))


def _get_parametrization_impl(
    params: tuple[object, ...],
    args: tuple[object, ...],
) -> Iterator[tuple[Any, Any]]:
    if not args:
        return (yield from ())
    arg_iter = iter(args)
    for i, param in enumerate(params):
        if isinstance(param, TypeVarTuple):
            # The remaining params are not TypeVarTuples.
            # Determine how many args to take until the next regular param.
            take = len(args) - i - len(params[i + 1 :])
            yield param, tuple(islice(arg_iter, take))
        else:
            yield param, next(arg_iter)


def _get_parametrization(
    params: tuple[Any, ...],
    args: tuple[Any, ...],
) -> dict[Any, Any]:
    return dict(_get_parametrization_impl(params, args))


def get_parametrization(runtime_generic: Any) -> dict[Any, Any]:
    """Map type parameters to type arguments in a generic alias."""
    return _get_parametrization(
        _get_generic_signature(runtime_generic).__args__,
        get_type_arguments(runtime_generic),
    )


def _get_parents(cls: Any) -> Iterator[Any]:
    """Get all parametrized parents of a runtime generic class or instance."""
    if not _has_origin(cls):
        return (
            yield from map(
                get_alias,
                parent_aliases_registry[
                    cls if isinstance(cls, type) else cls.__class__
                ],
            )
        )

    sig = _get_generic_signature(cls)
    origin, args = cls.__origin__, cls.__args__
    if not args:
        return (yield from map(get_alias, parent_aliases_registry[origin]))

    # Map child type arguments to parent type arguments.
    params = sig.__args__
    parametrization = _get_parametrization(params, args)
    parent_aliases: list[_AliasProxy] = parent_aliases_registry[origin]

    for parent in parent_aliases:
        yield parent.copy_with(
            _replace_type_arguments(parametrization, parent.__args__),
        )


def get_parents(cls: Any) -> tuple[Any, ...]:
    """Get all parametrized parents of a runtime generic class or instance."""
    return tuple(_get_parents(cls))


def _c3_merge(sequences: list[list[Any]]) -> list[Any]:
    # Adopted from functools.
    result: list[Any] = []
    while True:
        # Purge empty sequences.
        sequences = [seq for seq in sequences if seq]
        if not sequences:
            return result
        for seq_1 in sequences:  # Find merge candidates among sequence heads.
            candidate = seq_1[0]
            for seq_2 in sequences:
                if candidate in seq_2[1:]:
                    candidate = None
                    break  # Reject the current head, it appears in a tail!
            else:
                break
        if candidate is None:
            msg = "Inconsistent hierarchy"
            raise RuntimeError(msg)
        result.append(candidate)
        # Remove the chosen candidate.
        for seq in sequences:
            if seq[0] == candidate:
                del seq[0]


def _get_mro(cls: Any) -> list[Any]:
    return _c3_merge(
        [
            [get_alias(cls)],
            *map(_get_mro, parents := get_parents(cls)),
            [*parents],
        ],
    )


def get_mro(cls: Any) -> tuple[Any, ...]:
    """Get all parametrized parents of a runtime generic using the C3 algorithm."""
    return tuple(_get_mro(cls))


def _get_generic_signature(cls: Any) -> Any:
    if cls.__module__ == "typing":
        origin = cls
        if isinstance(cls, _AliasProxy):
            origin = cls.__origin__
        try:
            parameters = origin.__parameters__
        except AttributeError:
            # Smells like Python 3.9+ ;)
            conjured_typevars = map(
                "T".__add__,
                map(str, range(1, origin._nparams + 1)),  # noqa: SLF001
            )
            parameters = tuple(map(_get_cached_typevar, conjured_typevars))
        return _AliasProxy(origin, parameters)
    if _has_origin(cls):
        origin = cls.__origin__
        return _AliasProxy(origin, origin.__parameters__)
    return _AliasProxy(cls if isinstance(cls, type) else type(cls), cls.__parameters__)


def _get_default_alias(cls: Any) -> Any:
    sig = _get_generic_signature(cls)
    orig = sig.__origin__
    params = sig.__parameters__
    anys = (Any,) * (
        len(params) - any(isinstance(param, TypeVarTuple) for param in params)
    )
    return _AliasProxy(orig, anys)


def get_alias(rg: Any) -> Any:
    """
    For any runtime generic (class, instance), find the most relevant generic alias.

    Parameters
    ----------
    rg
        Any form of a runtime generic.

    Examples
    --------
    ```py
    >>> from typing import Generic, TypeVar
    >>> T = TypeVar("T")
    ...
    >>> @runtime_generic
    ... class Foo(Generic[T]):
    ...     pass
    ...
    >>> get_alias(Foo)
    runtime_generics.Foo[typing.Any]
    >>> get_alias(Foo())
    runtime_generics.Foo[typing.Any]
    >>> get_alias(Foo[int])
    runtime_generics.Foo[int]
    >>> get_alias(Foo[int]())
    runtime_generics.Foo[int]

    ```

    """
    try:
        args = rg.__args__
    except AttributeError:
        return _get_default_alias(rg)
    else:
        if any(
            _has_origin(arg) and arg.__origin__ is Unpack or isinstance(arg, TypeVar)
            for arg in args
        ):
            return _get_default_alias(rg)
    if rg.__module__ == "typing" and rg._name:  # noqa: SLF001
        return _AliasProxy(getattr(typing, rg._name), rg.__args__)  # noqa: SLF001
    return _AliasProxy(rg.__origin__, rg.__args__)


@contextmanager
def runtime_generic_patch(*objects: object, stack_offset: int = 2) -> Iterator[None]:
    """Patch `objects` to support runtime generics."""
    variables = {}

    with suppress(ValueError, TypeError, RuntimeError):
        variables = map_args_to_identifiers(
            *objects,
            stack_offset=stack_offset + 1,
            function=runtime_generic_patch,
        )

    if objects and not variables:
        msg = (
            "Failed to resolve objects to patch.\n"
            "This might have occured on incorrect call to `runtime_generic_patch()`.\n"
            "Call `runtime_generic_patch()` only with explicit identifiers, "
            "like `runtime_generic_patch(List, Tuple)`."
        )
        raise ValueError(msg)

    backframe_globals = inspect.stack()[stack_offset].frame.f_globals
    previous_state = backframe_globals.copy()

    # fmt: off
    backframe_globals.update({
        identifier: runtime_generic_proxy(obj)
        for identifier, obj in variables.items()
    })
    # fmt: on

    try:
        yield
    finally:
        backframe_globals.update(previous_state)


def _setup_runtime_generic(cls: Any, result_type: Any = None) -> None:
    cls.__class_getitem__ = _RuntimeGenericDescriptor(result_type)
    for unique_mro_entry, parent_cls in unique_mro_entries.copy().items():
        if unique_mro_entry in cls.__bases__:
            parametrized_parent = parent_cls.__result__
            parent_aliases_registry[cls].append(parametrized_parent)
            del unique_mro_entries[unique_mro_entry]


def no_alias(cls_method: Callable[_P, _R]) -> Callable[_P, _R]:
    """Mark a classmethod as not being passed a generic alias in place of cls."""
    cls_method.__no_alias__ = True  # type: ignore[attr-defined]
    return cls_method


def get_type_arguments(rg: object) -> tuple[type[Any], ...]:
    """
    Get all type arguments of a runtime generic.

    Parameters
    ----------
    rg
        An class that was decorated with `@runtime_generic` or its instance.

    Returns
    -------
    args
        The type arguments of the examined runtime generic.

    Examples
    --------
    ```python
    >>> from typing import Generic, TypeVar
    >>> T = TypeVar("T")
    ...
    >>> @runtime_generic
    ... class Foo(Generic[T]):
    ...     pass
    >>> args: tuple[type[int]] = get_type_arguments(Foo[int]())
    >>> args
    (<class 'int'>,)

    ```

    """
    args = getattr(rg, "__args__", ())
    return tuple(args) if isinstance(args, GenericArgs) else _typing_get_args(args)


def runtime_generic_proxy(result_type: Any) -> Any:
    """Create a runtime generic descriptor with a result type."""
    parameters = _get_generic_signature(result_type).__args__

    @partial(runtime_generic, result_type=result_type)
    class _Proxy(Generic[parameters]):  # type: ignore[misc]
        pass

    return cast(Any, _Proxy)


def runtime_generic_init(
    self: object,
    args: tuple[object, ...],
    origin: object,
) -> None:
    """Initialize a runtime generic instance."""
    vars(self).setdefault("__args__", args)
    vars(self).setdefault("__origin__", origin)


def runtime_generic(
    cls: _R,
    result_type: Any = None,
) -> _R:
    """
    Mark a class as a runtime generic.

    This is a class decorator that dynamically adds a `__class_getitem__` descriptor
    to the class. This method returns a callable that takes type arguments and returns
    a new instance of the class with the `__args__` attribute set to the type arguments.

    Examples
    --------
    ```python
    >>> from typing import Generic, TypeVar
    >>> T = TypeVar("T")
    ...
    >>> @runtime_generic
    ... class Foo(Generic[T]):
    ...     pass
    ...
    >>> Foo[int]().__args__
    (<class 'int'>,)

    ```

    """
    _setup_runtime_generic(cls, result_type=result_type)
    return cls


def _inner_type_check(  # noqa: PLR0911
    subtype: Any,
    cls: Any,
    param: Any,
) -> bool:
    if Any in (subtype, cls):
        return True
    invariant_passes = cast(bool, subtype == cls)
    if isinstance(param, TypeVarTuple):
        return invariant_passes
    if isinstance(subtype, _typing_GenericAlias) or isinstance(
        cls,
        _typing_GenericAlias,
    ):
        if param.__covariant__:
            return type_check(subtype, cls)
        if param.__contravariant__:
            return type_check(cls, subtype)
        return invariant_passes
    if param.__covariant__:
        return issubclass(subtype, cls)
    if param.__contravariant__:
        return issubclass(cls, subtype)
    return invariant_passes


def type_check(subtype: Any, cls: Any) -> bool:
    """
    Examine whether a runtime generic is a of another runtime generic.

    Variance is supported. TypeVar bounds are not yet supported.

    Parameters
    ----------
    subtype
        The runtime generic to examine.
    cls
        The supertype runtime generic.

    Examples
    --------
    ```python
    >>> from typing import Any, Dict, Generic, TypeVar
    ...
    >>> T = TypeVar("T")
    >>> T_co = TypeVar("T_co", covariant=True)
    >>> T_contra = TypeVar("T_contra", contravariant=True)
    ...
    >>> type_check(Dict[str, int], Dict[str, bool])  # KT, VT - invariant
    False
    >>> @runtime_generic
    ... class Foo(Generic[T, T_co, T_contra]):
    ...     pass
    ...
    >>> @runtime_generic
    ... class Bar(Generic[T_contra, T_co, T], Foo[T, T_co, T_contra]):
    ...     pass
    ...
    >>> type_check(Foo[int, int, int], Foo[int, int, int])
    True
    >>> type_check(Foo[int, bool, int], Foo[int, int, int])
    True
    >>> type_check(Foo[int, int, int], Foo[int, int, bool])
    True
    >>> type_check(Foo[int, int, int], Foo[int, bool, int])
    False
    >>> type_check(Foo[int, int, bool], Foo[int, int, int])
    False
    >>> type_check(Bar[int, int, int], Foo[int, int, bool])
    True
    >>> type_check(Bar[bool, int, int], Foo[int, int, int])
    False
    >>> type_check(Bar[int, bool, int], Foo[int, int, int])
    True

    ```

    Returns
    -------
    bool
        Whether `subtype` is a valid subtype of `cls`.

    """
    subtype = get_alias(subtype)
    cls = get_alias(cls)

    for mro_entry in get_mro(subtype):
        if mro_entry.__origin__ is cls.__origin__:
            mro_entry_parametrization = get_parametrization(mro_entry)
            cls_parametrization = get_parametrization(cls)
            sig = _get_generic_signature(cls)

            for orig_param in sig.__args__:
                param = orig_param
                if _has_origin(param) and param.__origin__ is Unpack:
                    (param,) = param.__args__

                mro_entry_args = mro_entry_parametrization[param]
                if not isinstance(mro_entry_args, tuple):
                    mro_entry_args = (mro_entry_args,)

                cls_args = cls_parametrization[param]
                if not isinstance(cls_args, tuple):
                    cls_args = (cls_args,)

                if not all(
                    map(
                        partial(_inner_type_check, param=param),
                        mro_entry_args,
                        cls_args,
                    ),
                ):
                    break
            else:
                return True
    return False

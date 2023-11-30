from __future__ import annotations

from typing import Any, Generic, TypeVar
from typing import get_args as _typing_get_args

from pytest import raises, warns
from typing_extensions import TypeVarTuple, Unpack

from runtime_generics import (
    generic_isinstance,
    generic_issubclass,
    get_type_arguments,
    no_alias,
    runtime_generic,
)

T = TypeVar("T")
T2 = TypeVar("T2")
Ts = TypeVarTuple("Ts")


@runtime_generic
class SingleArgGeneric(Generic[T]):
    __args__: tuple[type[T]]


@runtime_generic
class TwoArgGeneric(Generic[T, T2]):
    __args__: tuple[type[T], type[T2]]


@runtime_generic(cascade=False)
class VariadicGeneric(Generic[T, Unpack[Ts]]):
    __args__: tuple[type[Any], ...]


def test_dunder_args_single() -> None:
    assert SingleArgGeneric[int]().__args__ == (int,)
    assert SingleArgGeneric[int].__args__ == (int,)  # type: ignore[misc]
    assert _typing_get_args(SingleArgGeneric[int]) == (int,)


def test_get_all_arguments_single() -> None:
    assert get_type_arguments(SingleArgGeneric[int]()) == (int,)


def test_get_arguments() -> None:
    assert get_type_arguments(SingleArgGeneric[complex]()) == (complex,)
    assert get_type_arguments(TwoArgGeneric[int, str]()) == (int, str)


def test_dunder_args_two() -> None:
    assert TwoArgGeneric[int, str]().__args__ == (int, str)


def test_get_all_arguments_two() -> None:
    assert get_type_arguments(TwoArgGeneric[int, object]()) == (int, object)


def test_args_variadic() -> None:
    assert VariadicGeneric[int, str, float]().__args__ == (int, str, float)


def test_get_all_arguments_variadic() -> None:
    assert get_type_arguments(VariadicGeneric[str, int, float]()) == (str, int, float)


def test_classmethod_alias() -> None:
    @runtime_generic
    class TestedClass(Generic[T]):
        @classmethod
        def classmethod_with_alias(cls) -> type[TestedClass[T]]:
            return cls

        @no_alias
        @classmethod
        def classmethod_without_alias(cls) -> type[TestedClass[Any]]:
            return cls

    assert TestedClass[int].classmethod_with_alias() is TestedClass[int]
    assert TestedClass[int].classmethod_without_alias() is TestedClass



def test_generic_isinstance() -> None:
    @runtime_generic
    class TestedClass(Generic[T]):
        pass

    assert generic_isinstance(TestedClass[int](), TestedClass[int])
    assert not generic_isinstance(TestedClass[int](), TestedClass[str])
    assert generic_isinstance(TestedClass[int](), TestedClass)


def test_generic_issubclass() -> None:
    @runtime_generic
    class TestedClass(Generic[T]):
        pass

    assert generic_issubclass(TestedClass[int], TestedClass[int])
    assert generic_issubclass(TestedClass[Any], TestedClass)
    assert not generic_issubclass(int, TestedClass[int])
    assert not generic_issubclass(TestedClass[int], TestedClass[str])
    assert not generic_issubclass(TestedClass[int], TestedClass)
    assert not generic_issubclass(SingleArgGeneric[int], TestedClass)
    assert not generic_issubclass(SingleArgGeneric[int], TestedClass[int])


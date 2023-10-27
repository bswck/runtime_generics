from __future__ import annotations

from typing import Any, Generic, TypeVar
from typing import get_args as _typing_get_args

from pytest import raises
from typing_extensions import TypeVarTuple

from runtime_generics import get_arg, get_args, get_argument, runtime_generic

T = TypeVar("T")
T2 = TypeVar("T2")
Ts = TypeVarTuple("Ts")


@runtime_generic
class SingleArgGeneric(Generic[T]):
    __args__: tuple[type[T]]


@runtime_generic
class TwoArgGeneric(Generic[T, T2]):
    __args__: tuple[type[T], type[T2]]


VariadicGenericBase = Generic.__class_getitem__((T, *Ts))  # type: ignore[attr-defined]


@runtime_generic
class VariadicGeneric(VariadicGenericBase):  # type: ignore[valid-type,misc]
    __args__: tuple[type[Any], ...]


def test_args_single() -> None:
    assert SingleArgGeneric[int]().__args__ == (int,)
    assert SingleArgGeneric[int].__args__ == (int,)  # type: ignore[attr-defined,misc]
    assert _typing_get_args(SingleArgGeneric[int]) == (int,)


def test_get_args_single() -> None:
    assert get_args(SingleArgGeneric[int]()) == (int,)


def test_get_arg() -> None:
    assert get_arg(SingleArgGeneric[complex]()) == complex
    assert get_arg(SingleArgGeneric[float]()) != int
    assert get_argument is get_arg

    with raises(ValueError):
        get_arg(TwoArgGeneric[int, str]())


def test_args_two() -> None:
    assert TwoArgGeneric[int, str]().__args__ == (int, str)


def test_get_args_two() -> None:
    assert get_args(TwoArgGeneric[int, object]()) == (int, object)


def test_args_variadic() -> None:
    assert VariadicGeneric[int, str, float]().__args__ == (int, str, float)  # type: ignore[misc]


def test_get_args_variadic() -> None:
    assert get_args(VariadicGeneric[str, int, float]()) == (str, int, float)  # type: ignore[misc]

from __future__ import annotations

from typing import Any, Generic, TypeVar
from typing import get_args as _typing_get_args

from pytest import raises, warns
from typing_extensions import TypeVarTuple, Unpack

from runtime_generics import (
    Index,
    Select,
    get_all_args,
    get_all_arguments,
    get_arg,
    get_args,
    get_argument,
    get_arguments,
    index,
    runtime_generic,
    select,
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


@runtime_generic
class VariadicGeneric(Generic[T, Unpack[Ts]]):
    __args__: tuple[type[Any], ...]


def test_api_aliases() -> None:
    with warns(DeprecationWarning):
        assert get_argument(SingleArgGeneric[int]()) == (int,)
        assert get_argument is get_arg
    assert get_args is get_arguments
    assert get_all_args is get_all_arguments


def test_dunder_args_single() -> None:
    assert SingleArgGeneric[int]().__args__ == (int,)
    assert SingleArgGeneric[int].__args__ == (int,)  # type: ignore[misc]
    assert _typing_get_args(SingleArgGeneric[int]) == (int,)


def test_get_all_arguments_single() -> None:
    assert get_all_arguments(SingleArgGeneric[int]()) == (int,)


def test_get_arguments() -> None:
    assert get_arguments(SingleArgGeneric[complex]()) == (complex,)
    assert get_arguments(TwoArgGeneric[int, str]()) == (int, str)
    assert get_arguments(TwoArgGeneric[int, bytearray](), Select[T2]) == (bytearray,)  # type: ignore[valid-type]
    assert get_arguments(
        VariadicGeneric[str, float, bytearray, bytes](), Index[1:3]
    ) == (
        float,
        bytearray,
        bytes,
    )  # right inclusive


def test_dunder_args_two() -> None:
    assert TwoArgGeneric[int, str]().__args__ == (int, str)


def test_get_all_arguments_two() -> None:
    assert get_all_arguments(TwoArgGeneric[int, object]()) == (int, object)


def test_args_variadic() -> None:
    assert VariadicGeneric[int, str, float]().__args__ == (int, str, float)


def test_get_all_arguments_variadic() -> None:
    assert get_all_arguments(VariadicGeneric[str, int, float]()) == (str, int, float)


def test_select() -> None:
    assert select[T2, T](TwoArgGeneric[int, str]()) == (str, int)
    assert select[T](TwoArgGeneric[int, str]()) is int
    assert select[T2](TwoArgGeneric[int, str]()) is str
    assert select[Unpack[Ts]](VariadicGeneric[str, float, int]()) == (float, int)


def test_index() -> None:
    assert index[0](TwoArgGeneric[int, str]()) is int
    assert index[:5](TwoArgGeneric[int, str]()) == (int, str)
    assert index[::-1](TwoArgGeneric[int, str]()) == (str, int)
    with raises(TypeError):
        index["?"](TwoArgGeneric[int, str]())
    with raises(TypeError):
        index[None](TwoArgGeneric[int, str]())

def test_classmethod_transform() -> None:
    @runtime_generic
    class C(Generic[T]):
        @classmethod
        def foo(cls) -> type[C[T]]:
            return cls

    assert C[int].foo() == C[int]

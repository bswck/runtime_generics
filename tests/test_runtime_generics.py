from __future__ import annotations

from typing import Any, Generic, Dict, TypeVar
from typing import get_args as _typing_get_args

from typing_extensions import TypeVarTuple, Unpack

from runtime_generics import (
    get_parents,
    get_type_arguments,
    get_parametrization,
    no_alias,
    runtime_generic_patch,
    runtime_generic,
    runtime_generic_proxy,
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


@runtime_generic
class Foo(Generic[T]):
    pass

@runtime_generic
class Bar(Generic[T], Foo[T]):
    pass

@runtime_generic
class Biz(Generic[T], Bar[T]):
    pass

@runtime_generic
class Baz(Generic[T2], Bar[T2]):
    pass

@runtime_generic
class Qux(Generic[T], Biz[T], Baz[T]):
    pass

@runtime_generic
class Fred(Generic[T], Bar[int]):
    pass

@runtime_generic
class SpamVariadic(Generic[Unpack[Ts]]):
    pass

@runtime_generic
class HamVariadic(Generic[Unpack[Ts], T], SpamVariadic[Unpack[Ts]], Qux[T]):
    pass


with runtime_generic_patch(Dict):
    @runtime_generic
    class EggsVariadic(Generic[T, T2], Dict[HamVariadic[T, T2], str]):
        pass


def test_get_parametrization() -> None:
    gp = get_parametrization
    assert gp(Foo[int]) == gp(Foo[int]()) == {T: int}
    assert gp(Bar[float]) == gp(Bar[float]()) == {T: float}
    assert gp(Biz[bytes]) == gp(Biz[bytes]()) == {T: bytes}
    assert gp(Baz[complex]) == gp(Baz[complex]()) == {T2: complex}
    assert gp(Qux[int]) == gp(Qux[int]()) == {T: int}
    assert gp(Fred[bool]) == gp(Fred[bool]()) == {T: bool}
    assert gp(Fred[str]) == gp(Fred[str]()) == {T: str}
    assert (
        gp(SpamVariadic[str, int])
        == gp(SpamVariadic[str, int]())
        == {Ts: (str, int)}
    )
    assert (
        gp(HamVariadic[float, str, bytes])
        == gp(HamVariadic[float, str, bytes]())
        == {Ts: (float, str), T: bytes}
    )
    assert (
        gp(EggsVariadic[complex, bool])
        == gp(EggsVariadic[complex, bool]())
        == {T: complex, T2: bool}
    )


def test_get_parents() -> None:
    gps = get_parents  # I think I would travel to Tibet. How about you?
    assert gps(Foo) == gps(Foo()) == ()
    assert gps(Bar) == gps(Bar()) == (Foo[T],)  # type: ignore[valid-type]
    assert gps(Biz) == gps(Biz()) == (Bar[T],)  # type: ignore[valid-type]
    assert gps(Baz) == gps(Baz()) == (Bar[T2],)  # type: ignore[valid-type]
    assert gps(Qux) == gps(Qux()) == (Biz[T], Baz[T])  # type: ignore[valid-type]
    assert gps(Qux[int]) == gps(Qux[int]()) == (Biz[int], Baz[int])
    assert gps(Fred) == gps(Fred()) == (Bar[int],)
    assert gps(Fred[str]) == gps(Fred[str]()) == (Bar[int],)
    assert gps(SpamVariadic[str, int]) == gps(SpamVariadic[str, int]()) == ()
    assert (
        gps(HamVariadic)
        == gps(HamVariadic())
        == (SpamVariadic[Unpack[Ts]], Qux[T])  # type: ignore[valid-type]
    )
    assert (
        gps(HamVariadic[float, str, bytes])
        == gps(HamVariadic[float, str, bytes]())
        == (SpamVariadic[float, str], Qux[bytes])
    )
    assert (
        gps(EggsVariadic[complex, bool])
        == gps(EggsVariadic[complex, bool]())
        == (Dict[HamVariadic[complex, bool], str],)
    )

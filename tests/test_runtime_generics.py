from __future__ import annotations

import pytest
from typing import Any, Generic, Dict, TypeVar
from typing import get_args as _typing_get_args

from typing_extensions import TypeVarTuple, Unpack

from runtime_generics import (
    get_mro,
    get_parents,
    get_type_arguments,
    get_parametrization,
    no_alias,
    runtime_generic_patch,
    runtime_generic,
    type_check,
)

T = TypeVar("T")
T2_co = TypeVar("T2_co", covariant=True)
T2_contra = TypeVar("T2_contra", contravariant=True)
Ts = TypeVarTuple("Ts")


@runtime_generic
class SingleArgGeneric(Generic[T]):
    __args__: tuple[type[T]]


@runtime_generic
class TwoArgGeneric(Generic[T, T2_co], SingleArgGeneric[T]):
    __args__: tuple[type[T], type[T2_co]]  # type: ignore[assignment]


@runtime_generic
class TwoArgGenericContra(Generic[T, T2_contra], SingleArgGeneric[T]):
    __args__: tuple[type[T], type[T2_contra]]  # type: ignore[assignment]


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
class Baz(Generic[T2_co], Bar[int]):
    pass


@runtime_generic
class Qux(Generic[T], Biz[str], Baz[T]):
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
    class EggsVariadic(Generic[T, T2_co], Dict[HamVariadic[T, T2_co], str]):
        pass


def test_get_parametrization() -> None:
    gp = get_parametrization
    assert gp(Foo[int]) == gp(Foo[int]()) == {T: int}
    assert gp(Bar[float]) == gp(Bar[float]()) == {T: float}
    assert gp(Biz[bytes]) == gp(Biz[bytes]()) == {T: bytes}
    assert gp(Baz[complex]) == gp(Baz[complex]()) == {T2_co: complex}
    assert gp(Qux[int]) == gp(Qux[int]()) == {T: int}
    assert gp(Fred[bool]) == gp(Fred[bool]()) == {T: bool}
    assert gp(Fred[str]) == gp(Fred[str]()) == {T: str}
    assert (
        gp(SpamVariadic[str, int]) == gp(SpamVariadic[str, int]()) == {Ts: (str, int)}
    )
    assert (
        gp(HamVariadic[float, str, bytes])
        == gp(HamVariadic[float, str, bytes]())
        == {Ts: (float, str), T: bytes}
    )
    assert (
        gp(EggsVariadic[complex, bool])
        == gp(EggsVariadic[complex, bool]())
        == {T: complex, T2_co: bool}
    )


def test_get_parents() -> None:
    gps = get_parents
    assert gps(Foo) == gps(Foo()) == ()
    assert gps(Bar) == gps(Bar()) == (Foo[Any],)
    assert gps(Biz) == gps(Biz()) == (Bar[Any],)
    assert gps(Baz) == gps(Baz()) == (Bar[int],)
    assert gps(Qux) == gps(Qux()) == (Biz[str], Baz[Any])
    assert gps(Qux[int]) == gps(Qux[int]()) == (Biz[str], Baz[int])
    assert gps(Fred) == gps(Fred()) == (Bar[int],)
    assert gps(Fred[str]) == gps(Fred[str]()) == (Bar[int],)
    assert gps(SpamVariadic[str, int]) == gps(SpamVariadic[str, int]()) == ()
    assert (
        gps(HamVariadic) == gps(HamVariadic()) == (SpamVariadic[()], Qux[Any])
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


def test_get_mro() -> None:
    hvp = HamVariadic[float, str, bytes]
    assert get_mro(hvp) == get_mro(hvp()) == (
        HamVariadic[float, str, bytes],
        SpamVariadic[float, str],
        Qux[bytes],
        Biz[str],
        Bar[str],
        Foo[str],
        Baz[bytes],
        Bar[int],
        Foo[int],
    )
    assert get_mro(HamVariadic()) == (
        HamVariadic[Any],
        SpamVariadic[()],
        Qux[Any],
        Biz[str],
        Bar[str],
        Foo[str],
        Baz[Any],
        Bar[int],
        Foo[int],
    )


@pytest.mark.parametrize(
    "subtype,cls,passes",
    (
        (TwoArgGeneric[str, int], SingleArgGeneric[str], True),
        (TwoArgGeneric[str, int], SingleArgGeneric[Any], True),
        (TwoArgGeneric[str, Any], SingleArgGeneric[Any], True),
        (TwoArgGeneric[Any, int], SingleArgGeneric[Any], True),
        (TwoArgGeneric[int, bool], TwoArgGeneric[int, int], True),
        (TwoArgGeneric[int, Any], TwoArgGeneric[int, int], True),
        (TwoArgGeneric[int, int], TwoArgGeneric[int, bool], False),
        (TwoArgGeneric[int, Any], TwoArgGeneric[int, bool], True),
        (TwoArgGenericContra[int, int], TwoArgGenericContra[int, bool], True),
        (TwoArgGenericContra[int, bool], TwoArgGenericContra[int, int], False),
        (TwoArgGeneric[int, int], TwoArgGeneric[bool, int], False),
        (TwoArgGeneric[Any, int], TwoArgGeneric[bool, int], True),
    )
)
def test_type_check(subtype: Any, cls: Any, passes: bool) -> None:
    assert type_check(subtype, cls) is passes
    assert type_check(subtype(), cls) is passes
    assert type_check(subtype, cls()) is passes
    assert type_check(subtype(), cls()) is passes
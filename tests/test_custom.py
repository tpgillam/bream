from __future__ import annotations

import typing
from dataclasses import dataclass

import pytest

import bream
from bream.core import InvalidPayloadDataError


@typing.final
class ComplexCoder(bream.Coder[complex]):
    """An demonstration coder for Python's `complex` type."""

    @property
    def version(self) -> int:
        return 1

    def encode(self, value: complex, fmt: bream.SerialisationFormat) -> bream.JsonType:
        del fmt
        return {"real": value.real, "imag": value.imag}

    def decode(
        self,
        data: bream.JsonType,
        fmt: bream.SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> complex:
        del bream_spec, fmt
        if coder_version != 1:
            raise bream.core.UnsupportedCoderVersionError(
                coder=self, version_provided=coder_version
            )
        if not isinstance(data, dict) or data.keys() != {"real", "imag"}:
            raise bream.core.InvalidPayloadDataError(
                coder=self, data=data, msg="Invalid keys"
            )
        if not isinstance(data["real"], float):
            raise bream.core.InvalidPayloadDataError(
                coder=self, data=data, msg="Invalid 'real'"
            )
        if not isinstance(data["imag"], float):
            raise bream.core.InvalidPayloadDataError(
                coder=self, data=data, msg="Invalid 'imag'"
            )
        return complex(data["real"], data["imag"])


class Moo:
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Moo)  # trivial objects currently so always equal


@typing.final
class MooCoder(bream.Coder[Moo]):
    @property
    def version(self) -> int:
        return 1

    def encode(self, value: Moo, fmt: bream.SerialisationFormat) -> bream.JsonType:
        del value, fmt
        return {}

    def decode(
        self,
        data: bream.JsonType,
        fmt: bream.SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> Moo:
        del data, fmt, coder_version, bream_spec
        return Moo()


@dataclass
class Cow:
    moo1: Moo
    moo2: Moo


@typing.final
class CowCoder(bream.Coder[Cow]):
    @property
    def version(self) -> int:
        return 1

    def encode(self, value: Cow, fmt: bream.SerialisationFormat) -> bream.JsonType:
        return {
            "moo1": bream.encode(value.moo1, fmt),
            "moo2": bream.encode(value.moo2, fmt),
        }

    def decode(
        self,
        data: bream.JsonType,
        fmt: bream.SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> Cow:
        if coder_version != 1:
            raise bream.core.UnsupportedCoderVersionError(
                coder=self, version_provided=coder_version
            )

        match data:
            case {"moo1": moo1, "moo2": moo2}:
                moo1 = bream.decode(moo1, fmt, bream_spec)
                moo2 = bream.decode(moo2, fmt, bream_spec)

                match (moo1, moo2):
                    case (Moo(), Moo()):
                        return Cow(moo1=moo1, moo2=moo2)
                    case _:
                        raise InvalidPayloadDataError(coder=self, data=data, msg=None)
            case _:
                raise InvalidPayloadDataError(coder=self, data=data, msg="Invalid keys")


def test_custom_complex() -> None:
    fmt = bream.SerialisationFormat(
        codecs=[
            bream.Codec(
                bream.TypeLabel("complex"),
                bream.TypeSpec.from_type(complex),
                ComplexCoder(),
            )
        ]
    )
    x = 1 + 2j
    assert isinstance(x, complex)
    encoded_x = bream.encode(x, fmt)
    assert encoded_x == {
        "_type": "complex",
        "_version": 1,
        "_payload": {"real": 1.0, "imag": 2.0},
    }
    new_x = bream.decode(encoded_x, fmt, bream_spec=0)
    assert new_x == x


def _some[T](x: T | None) -> T:
    assert x is not None
    return x


def test_serialization_format_find_coder() -> None:
    coder_complex = ComplexCoder()
    coder_moo = MooCoder()
    fmt = bream.SerialisationFormat(
        codecs=[
            bream.Codec(
                bream.TypeLabel("complex"),
                bream.TypeSpec.from_type(complex),
                coder_complex,
            ),
            bream.Codec(
                bream.TypeLabel("Moo"), bream.TypeSpec.from_type(Moo), coder_moo
            ),
        ]
    )
    assert _some(fmt.find_codec_for_value(0j)).coder is coder_complex
    assert _some(fmt.find_codec_for_value(Moo())).coder is coder_moo


def test_serialization_format_with_nesting() -> None:
    c = Cow(moo1=Moo(), moo2=Moo())
    fmt = bream.SerialisationFormat(
        codecs=[
            bream.Codec(
                bream.TypeLabel("cow"), bream.TypeSpec.from_type(Cow), CowCoder()
            ),
            bream.Codec(
                bream.TypeLabel("moo"), bream.TypeSpec.from_type(Moo), MooCoder()
            ),
        ]
    )
    c_serialized = bream.encode(c, fmt)
    c_deserialized = bream.decode(c_serialized, fmt, bream_spec=0)
    assert c == c_deserialized


def test_serialization_format_raises_for_json_codec() -> None:
    for json_type in (bool, int, float, type(None), list):
        with pytest.raises(ValueError, match="cannot add codec for native type"):
            bream.SerialisationFormat(
                codecs=[
                    bream.Codec(
                        bream.TypeLabel("moo"),
                        bream.TypeSpec.from_type(json_type),
                        MooCoder(),
                    )
                ]
            )


def test_serialization_format_raises_on_clashes() -> None:
    # We must catch two codecs targeting the same type spec.
    with pytest.raises(ValueError, match="multiple codecs for type spec"):
        bream.SerialisationFormat(
            codecs=[
                bream.Codec(
                    bream.TypeLabel("complex 1"),
                    bream.TypeSpec.from_type(complex),
                    ComplexCoder(),
                ),
                bream.Codec(
                    bream.TypeLabel("complex 2"),
                    bream.TypeSpec.from_type(complex),
                    ComplexCoder(),
                ),
            ]
        )

    # We must catch two codecs with the same type label.
    with pytest.raises(ValueError, match="multiple codecs for type label"):
        bream.SerialisationFormat(
            codecs=[
                bream.Codec(
                    bream.TypeLabel("dino"),
                    bream.TypeSpec.from_type(complex),
                    ComplexCoder(),
                ),
                bream.Codec(
                    bream.TypeLabel("dino"), bream.TypeSpec.from_type(Moo), MooCoder()
                ),
            ]
        )

    # We must catch repeated identical coders.
    coder = ComplexCoder()
    with pytest.raises(ValueError, match="multiple codecs"):
        bream.SerialisationFormat(
            codecs=[
                bream.Codec(
                    bream.TypeLabel("complex"), bream.TypeSpec.from_type(complex), coder
                ),
                bream.Codec(
                    bream.TypeLabel("complex"), bream.TypeSpec.from_type(complex), coder
                ),
            ]
        )

from __future__ import annotations

import typing

import pytest

import bream


@typing.final
class ComplexCoder(bream.Coder[complex]):
    """An demonstration coder for Python's `complex` type."""

    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: complex, fmt: bream.SerialisationFormat
    ) -> bream.EncodeError | bream.JsonType:
        del fmt
        return {"real": value.real, "imag": value.imag}

    def decode(
        self,
        data: bream.JsonType,
        fmt: bream.SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> bream.DecodeError | complex:
        del bream_spec, fmt
        if coder_version != 1:
            return bream.core.UnsupportedCoderVersion(self, coder_version)
        if not isinstance(data, dict) or data.keys() != {"real", "imag"}:
            return bream.core.InvalidPayloadData(self, data, "Invalid keys")
        if not isinstance(data["real"], float):
            return bream.core.InvalidPayloadData(self, data, "Invalid 'real'")
        if not isinstance(data["imag"], float):
            return bream.core.InvalidPayloadData(self, data, "Invalid 'imag'")
        return complex(data["real"], data["imag"])


class Moo:
    pass


@typing.final
class MooCoder(bream.Coder[Moo]):
    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: Moo, fmt: bream.SerialisationFormat
    ) -> bream.EncodeError | bream.JsonType:
        del value, fmt
        return {}

    def decode(
        self,
        data: bream.JsonType,
        fmt: bream.SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> bream.DecodeError | Moo:
        del data, fmt, coder_version, bream_spec
        return Moo()


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
    assert not isinstance(encoded_x, bream.EncodeError)
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

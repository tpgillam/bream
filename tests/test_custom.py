from __future__ import annotations

import typing

import pytest

import amber


@typing.final
class ComplexCoder(amber.Coder[complex]):
    """An demonstration coder for Python's `complex` type."""

    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: complex, fmt: amber.SerialisationFormat
    ) -> amber.EncodeError | amber.JsonType:
        del fmt
        return {"real": value.real, "imag": value.imag}

    def decode(
        self,
        data: amber.JsonType,
        fmt: amber.SerialisationFormat,
        coder_version: int,
        amber_spec: int,
    ) -> amber.DecodeError | complex:
        del amber_spec, fmt
        if coder_version != 1:
            return amber.UnsupportedCoderVersion(self, coder_version)
        if not isinstance(data, dict) or data.keys() != {"real", "imag"}:
            return amber.InvalidPayloadData(self, data, "Invalid keys")
        if not isinstance(data["real"], float):
            return amber.InvalidPayloadData(self, data, "Invalid 'real'")
        if not isinstance(data["imag"], float):
            return amber.InvalidPayloadData(self, data, "Invalid 'imag'")
        return complex(data["real"], data["imag"])


class Moo:
    pass


@typing.final
class MooCoder(amber.Coder[Moo]):
    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: Moo, fmt: amber.SerialisationFormat
    ) -> amber.EncodeError | amber.JsonType:
        del value, fmt
        return {}

    def decode(
        self,
        data: amber.JsonType,
        fmt: amber.SerialisationFormat,
        coder_version: int,
        amber_spec: int,
    ) -> amber.DecodeError | Moo:
        del data, fmt, coder_version, amber_spec
        return Moo()


def test_custom_complex() -> None:
    fmt = amber.SerialisationFormat(
        codecs=[
            amber.Codec(
                amber.TypeLabel("complex"),
                amber.TypeSpec.from_type(complex),
                ComplexCoder(),
            )
        ]
    )
    x = 1 + 2j
    assert isinstance(x, complex)
    encoded_x = amber.encode(x, fmt)
    assert not isinstance(encoded_x, amber.EncodeError)
    assert encoded_x == {
        "_type": "complex",
        "_version": 1,
        "_payload": {"real": 1.0, "imag": 2.0},
    }
    new_x = amber.decode(encoded_x, fmt, amber_spec=0)
    assert new_x == x


def _some[T](x: T | None) -> T:
    assert x is not None
    return x


def test_serialization_format_find_coder() -> None:
    coder_complex = ComplexCoder()
    coder_moo = MooCoder()
    fmt = amber.SerialisationFormat(
        codecs=[
            amber.Codec(
                amber.TypeLabel("complex"),
                amber.TypeSpec.from_type(complex),
                coder_complex,
            ),
            amber.Codec(
                amber.TypeLabel("Moo"), amber.TypeSpec.from_type(Moo), coder_moo
            ),
        ]
    )
    assert _some(fmt.find_codec_for_value(0j)).coder is coder_complex
    assert _some(fmt.find_codec_for_value(Moo())).coder is coder_moo


def test_serialization_format_raises_on_clashes() -> None:
    # We must catch two coders targeting the same type spec.
    with pytest.raises(ValueError, match="multiple coders"):
        amber.SerialisationFormat(
            codecs=[
                amber.Codec(
                    amber.TypeLabel("complex"),
                    amber.TypeSpec.from_type(complex),
                    ComplexCoder(),
                ),
                amber.Codec(
                    amber.TypeLabel("complex"),
                    amber.TypeSpec.from_type(complex),
                    ComplexCoder(),
                ),
            ]
        )
    # We must catch repeated identical coders.
    coder = ComplexCoder()
    with pytest.raises(ValueError, match="multiple coders"):
        amber.SerialisationFormat(
            codecs=[
                amber.Codec(
                    amber.TypeLabel("complex"), amber.TypeSpec.from_type(complex), coder
                ),
                amber.Codec(
                    amber.TypeLabel("complex"), amber.TypeSpec.from_type(complex), coder
                ),
            ]
        )

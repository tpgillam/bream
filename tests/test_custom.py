from __future__ import annotations

import typing

import amber


@typing.final
class ComplexCoder(amber.Coder[complex]):
    """An demonstration coder for Python's `complex` type."""

    @property
    def type_label(self) -> amber.TypeLabel:
        return amber.TypeLabel("complex")

    @property
    def type_spec(self) -> amber.TypeSpec:
        return amber.TypeSpec(module="builtins", name="complex")

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
        amber_version: int,
    ) -> amber.DecodeError | complex:
        del amber_version, fmt
        if coder_version != 1:
            return amber.UnsupportedCoderVersion(self.type_label, coder_version)
        if not isinstance(data, dict) or data.keys() != {"real", "imag"}:
            return amber.InvalidPayloadData(self.type_label, data, "Invalid keys")
        if not isinstance(data["real"], float):
            return amber.InvalidPayloadData(self.type_label, data, "Invalid 'real'")
        if not isinstance(data["imag"], float):
            return amber.InvalidPayloadData(self.type_label, data, "Invalid 'imag'")
        return complex(data["real"], data["imag"])


def test_custom_complex() -> None:
    fmt = amber.SerialisationFormat(coders=[ComplexCoder()])
    x = 1 + 2j
    assert isinstance(x, complex)
    encoded_x = amber.encode(x, fmt)
    assert not isinstance(encoded_x, amber.EncodeError)
    assert encoded_x == {
        "_type": "complex",
        "_version": 1,
        "_payload": {"real": 1.0, "imag": 2.0},
    }
    new_x = amber.decode(encoded_x, fmt, amber_version=0)
    assert new_x == x

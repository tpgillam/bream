# Following are some thoughts on how coders might look given the API above.
from __future__ import annotations

import dataclasses
import typing

import amber


@dataclasses.dataclass(frozen=True)
class Moo:
    x: int
    y: str
    z: list[float]
    w: complex


# TODO: not the most compact approach; might want to use a two-element list instead.
@typing.final
class ComplexCoder(amber.Coder[complex]):
    """A coder for Python's `complex` type."""

    @property
    def type_label(self) -> amber.TypeLabel:
        return amber.TypeLabel("complex")

    @property
    def version(self) -> int:
        return 1

    def encode(self, value: complex) -> amber.EncodeError | amber.JsonType:
        return {"real": value.real, "imag": value.imag}

    def decode(self, data: amber.JsonType, version: int) -> amber.DecodeError | complex:
        if version != 1:
            return amber.UnsupportedVersion(self.type_label, version)
        if not isinstance(data, dict) or data.keys() != {"real", "imag"}:
            return amber.InvalidData(self.type_label, data, "Invalid keys")
        if not isinstance(data["real"], float):
            return amber.InvalidData(self.type_label, data, "Invalid 'real'")
        if not isinstance(data["imag"], float):
            return amber.InvalidData(self.type_label, data, "Invalid 'imag'")
        return complex(data["real"], data["imag"])

from typing import NewType, Protocol

_JsonElement = bool | float | int | str | None
type JsonType = _JsonElement | list["JsonType"] | dict[str, "JsonType"]


class Coder(Protocol):
    """Encapsulate encoding & decoding for a specific type."""

    def decode(self, data: JsonType) -> object: ...
    def encode(self, value: object) -> JsonType: ...


class Decoder(Protocol):
    def decode(self, data: JsonType) -> object: ...


TypeLabel = NewType("TypeLabel", str)


# TODO: frozen
class SerialisationFormat:
    version: int
    """The current version of the serialisation format."""

    # TODO: frozen
    type_label_to_coder: dict[TypeLabel, Coder]
    """A map from an object's class label to a `Coder`."""

    breaking_version_type_label_to_compatibility_decoder: dict[
        tuple[int, TypeLabel], Decoder
    ]


_TYPE_LABEL_KEY = "__type"
_AMBER_VERSION_KEY = "__amber_version"
_FORMAT_VERSION_KEY = "__format_version"
_PAYLOAD_KEY = "__payload"

AMBER_VERSION = 1
"""This tracks the techniques used to serialise objects with amber.

The version will be incremeneted whenever breaking changes are made to amber.
"""


def encode(obj: object, format: SerialisationFormat) -> dict[str, JsonType]:
    return {_FORMAT_VERSION_KEY: format.version, _PAYLOAD_KEY: _encode(obj, format)}


def _assert_valid_key(x: object) -> str:
    if not isinstance(x, str):
        msg = f"keys must be strings; got {x!r}"
        raise TypeError(msg)
    if x in (_TYPE_LABEL_KEY, _AMBER_VERSION_KEY, _FORMAT_VERSION_KEY, _PAYLOAD_KEY):
        msg = f"{x!r} is a reserved keyword that can't appear as a dictionary key."
        raise ValueError(msg)
    return x


def _encode(obj: object, format: SerialisationFormat) -> JsonType:
    if isinstance(obj, _JsonElement):
        return obj

    if isinstance(obj, list):
        return [encode(x, format) for x in obj]

    if isinstance(obj, dict):
        # TODO: Support non-string keys
        return {_assert_valid_key(k): encode(v, format) for k, v in obj.items()}

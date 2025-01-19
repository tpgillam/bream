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


# XXX: more details in here
class EncodeError:
    pass


def encode(
    obj: object, format: SerialisationFormat
) -> EncodeError | dict[str, JsonType]:
    payload = _encode(obj, format)
    if isinstance(payload, EncodeError):
        return payload

    return {
        _AMBER_VERSION_KEY: AMBER_VERSION,
        _FORMAT_VERSION_KEY: format.version,
        _PAYLOAD_KEY: payload,
    }


def _assert_valid_key(x: object) -> None:
    if not isinstance(x, str):
        msg = f"keys must be strings; got {x!r}"
        raise TypeError(msg)
    if x in (_TYPE_LABEL_KEY, _AMBER_VERSION_KEY, _FORMAT_VERSION_KEY, _PAYLOAD_KEY):
        msg = f"{x!r} is a reserved keyword that can't appear as a dictionary key."
        raise ValueError(msg)


def _encode(obj: object, format: SerialisationFormat) -> EncodeError | JsonType:
    if isinstance(obj, _JsonElement):
        return obj

    # TODO: should this be hardcoded, or added as something registerable?
    if isinstance(obj, list):
        result = []
        for x in obj:
            x_encoded = _encode(x, format)
            if isinstance(x_encoded, EncodeError):
                return x_encoded
            result.append(x_encoded)
        return result

    # TODO: should this be hardcoded, or added as something registerable?
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # TODO: Support non-string keys
            _assert_valid_key(k)
            v_encoded = _encode(v, format)
            if isinstance(v_encoded, EncodeError):
                return v_encoded
            result[k] = v_encoded
        return result

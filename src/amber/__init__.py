from __future__ import annotations

import abc
import dataclasses
import typing
from typing import NewType

_JsonElement = bool | float | int | str | None
type JsonType = _JsonElement | list[JsonType] | dict[str, JsonType]

TypeLabel = NewType("TypeLabel", str)

# TODO: these error types, or exceptions?


@dataclasses.dataclass(frozen=True, slots=True)
class UnencodableObject:
    value: object


@dataclasses.dataclass(frozen=True, slots=True)
class UnencodableDictKey:
    value: object


EncodeError = UnencodableObject | UnencodableDictKey


@dataclasses.dataclass(frozen=True, slots=True)
class UnsupportedVersion:
    """The version requested for deserialisation is not supported."""

    type_label: TypeLabel
    version_provided: int


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidData:
    type_label: TypeLabel
    data: JsonType
    msg: str | None = None


type DecodeError = UnsupportedVersion | InvalidData


class Coder[T](abc.ABC):
    """Encapsulate encoding & decoding for a specific type."""

    @property
    @abc.abstractmethod
    def type_label(self) -> TypeLabel:
        """A label for the type this encoder handles.

        This should be an identifier that is unique within the format.
        """

    @property
    @abc.abstractmethod
    def version(self) -> int:
        """The current version of this coder.

        This is an integer, and it should be incremented whenever a breaking change is
        made.
        """

    @abc.abstractmethod
    def encode(self, value: T) -> EncodeError | JsonType:
        """Encode `value` using this coder's current version.

        Will return an `EncodeError` if encoding isn't possible.
        """

    @abc.abstractmethod
    def decode(self, data: JsonType, version: int) -> DecodeError | T:
        """Decode `data`, assuming it was encoded with `version` of this coder.

        Will return a `DecodeError` if decoding isn't possible.
        """


# TODO: frozen
@dataclasses.dataclass
class SerialisationFormat:
    version: int
    """The current version of the serialisation format."""

    coders: tuple[Coder[typing.Any]]
    """All `Coder` instances registered with this format."""


_AMBER_VERSION_KEY = "__amber_version"
_PAYLOAD_KEY = "__payload"
_TYPE_LABEL_KEY = "__type"
_VERSION_KEY = "__version"

AMBER_VERSION = 1
"""This tracks the techniques used to serialise objects with amber.

The version will be incremented whenever breaking changes are made to amber.
"""


def encode(obj: object, fmt: SerialisationFormat) -> EncodeError | dict[str, JsonType]:
    payload = _encode(obj, fmt)
    if isinstance(payload, EncodeError):
        return payload

    return {_AMBER_VERSION_KEY: AMBER_VERSION, _PAYLOAD_KEY: payload}


def _is_valid_key(x: object) -> typing.TypeGuard[str]:
    if not isinstance(x, str):
        return False
        msg = f"keys must be strings; got {x!r}"
        raise TypeError(msg)
    if x in (_TYPE_LABEL_KEY, _AMBER_VERSION_KEY, _VERSION_KEY, _PAYLOAD_KEY):
        return False
        msg = f"{x!r} is a reserved keyword that can't appear as a dictionary key."
        raise ValueError(msg)
    return True


def _encode(obj: object, fmt: SerialisationFormat) -> EncodeError | JsonType:
    if isinstance(obj, _JsonElement):
        return obj

    if isinstance(obj, list):
        return _encode_list(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

    if isinstance(obj, dict):
        return _encode_dict(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

    return UnencodableObject(obj)


def _encode_list(
    obj: list[typing.Any], fmt: SerialisationFormat
) -> EncodeError | list[JsonType]:
    result: list[JsonType] = []
    for x in obj:
        x_encoded = _encode(x, fmt)
        if isinstance(x_encoded, EncodeError):
            return x_encoded
        result.append(x_encoded)
    return result


def _encode_dict(
    obj: dict[typing.Any, typing.Any], fmt: SerialisationFormat
) -> EncodeError | dict[str, JsonType]:
    result: dict[str, JsonType] = {}
    for k, v in obj.items():
        # TODO: Support non-string keys
        if not _is_valid_key(k):
            return UnencodableDictKey(k)
        v_encoded = _encode(v, fmt)
        if isinstance(v_encoded, EncodeError):
            return v_encoded
        result[k] = v_encoded
    return result


def decode(obj: dict[str, JsonType]) -> object:
    pass


def _decode(obj: JsonType, *, amber_version: int, format_version: int):
    raise NotImplementedError

from __future__ import annotations

import abc
import dataclasses
import typing
from typing import NewType

_JsonElement = bool | float | int | str | None
type JsonType = _JsonElement | list[JsonType] | dict[str, JsonType]

TypeLabel = NewType("TypeLabel", str)
"""Represent a label for a type."""

# TODO: these error types, or exceptions?


@dataclasses.dataclass(frozen=True, slots=True)
class NoEncoderAvailable:
    value: object


@dataclasses.dataclass(frozen=True, slots=True)
class UnencodableDictKey:
    value: object


EncodeError = NoEncoderAvailable | UnencodableDictKey


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
        made. For example:

            - The type `T` might be altered to change its representation. The
              corresponding `Coder` version should be bumped, and (if possible) a
              fallback pathway provided in `encode` to decode older version to the
              current runtime representation.

            - `T` may be unaltered, but an optimisation is made to the encoded
              representation. The version should also be increased, and a compatibility
              pathway be provided.
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
@typing.final
@dataclasses.dataclass
class SerialisationFormat:
    version: int
    """The current version of the serialisation format."""

    # FIXME: freeze
    type_spec_to_coder: dict[TypeSpec, Coder[typing.Any]]
    """All `Coder` instances registered with this format."""

    def find_coder[T](self, obj: T) -> Coder[T] | None:
        """Find a suitable coder for `obj`, or `None` if there isn't one."""
        # PERF: we don't want this to be an O(N) lookup! Build some maps on construction
        #   to ensure that we don't do anything silly.



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


def _is_valid_dict_key(x: object) -> typing.TypeGuard[str]:
    if not isinstance(x, str):
        return False
    return x not in (_TYPE_LABEL_KEY, _AMBER_VERSION_KEY, _VERSION_KEY, _PAYLOAD_KEY)


def _encode(obj: object, fmt: SerialisationFormat) -> EncodeError | JsonType:
    if isinstance(obj, _JsonElement):
        return obj

    if isinstance(obj, list):
        return _encode_list(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

    if isinstance(obj, dict):
        return _encode_dict(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

    # We have handled all native types; now we delegate to the custom coders.
    coder = fmt.find_coder(obj)
    if coder is None:
        return NoEncoderAvailable(obj)

    return coder.encode(obj)


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
        # TODO: Support non-string keys -- this will require a different representation
        #   for a dict.
        if not _is_valid_dict_key(k):
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

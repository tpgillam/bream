from __future__ import annotations

import abc
import dataclasses
import enum
import typing
from typing import Any, NewType

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

# FIXME: warning -- version 0 is for pre-alpha development and WILL be broken on a
#   regular basis
# FIXME: rename this (and key) to something like 'amber format version'? This should
#   _not_ be confused with the version of the amber library itself.
AMBER_VERSION = 0
"""This tracks the techniques used to serialise objects with amber.

The version will be incremented whenever breaking changes are made to amber.
"""


class Keys(enum.Enum):
    """Special reserved keys for use in amber."""

    amber_version = "_amber_version"
    payload = "_payload"
    type_label = "_type"
    version = "_version"


# FIXME: should the document also contain some kind of identifier for the format? This
#    would mirror some property added to `SerialisationFormat`.
class Document(typing.TypedDict):
    """The structure of an amber document."""

    _amber_version: int
    _payload: JsonType


class CoderEncoded(typing.TypedDict):
    """The structure of a subtree encoded with a Coder."""

    _type: TypeLabel
    _version: int
    _payload: JsonType


def _is_coder_encoded(obj: dict[str, JsonType]) -> typing.TypeGuard[CoderEncoded]:
    if obj.keys() != CoderEncoded.__annotations__.keys():
        return False

    if not isinstance(obj[Keys.type_label.value], str):
        return False

    if not isinstance(obj[Keys.version.value], int):
        return False

    return False


_JsonElement = bool | float | int | str | None
type JsonType = _JsonElement | list[JsonType] | dict[str, JsonType]

TypeLabel = NewType("TypeLabel", str)
"""Represent a label for a type."""


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class TypeSpec:
    """Represent a type that can be imported from a module."""

    module: str
    name: str

    @staticmethod
    def from_type(type_: type) -> TypeSpec:
        return TypeSpec(module=type_.__module__, name=type_.__name__)


# TODO: these error types, or exceptions?


@dataclasses.dataclass(frozen=True, slots=True)
class NoEncoderAvailable:
    value: object


@dataclasses.dataclass(frozen=True, slots=True)
class UnencodableDictKey:
    value: object


EncodeError = NoEncoderAvailable | UnencodableDictKey


@dataclasses.dataclass(frozen=True, slots=True)
class UnsupportedAmberVersion:
    """The version of amber specified for deserialisation is unsupported."""

    amber_version: int


@dataclasses.dataclass(frozen=True, slots=True)
class NoDecoderAvailable:
    """No decoder is available for the given type_label."""

    type_label: TypeLabel


@dataclasses.dataclass(frozen=True, slots=True)
class UnsupportedCoderVersion:
    """The version requested for deserialisation is not supported."""

    type_label: TypeLabel
    version_provided: int


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidCoderEncoded:
    """Got an invalid structure that is similar to but not a `amber.CoderEncoded`."""

    obj: dict[str, JsonType]


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidPayloadData:
    type_label: TypeLabel
    data: JsonType
    msg: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidJson:
    data: object


DecodeError = (
    UnsupportedAmberVersion
    | NoDecoderAvailable
    | UnsupportedCoderVersion
    | InvalidCoderEncoded
    | InvalidPayloadData
    | InvalidJson
)


class Coder[T](abc.ABC):
    """Encapsulate encoding & decoding for a specific type."""

    @property
    @abc.abstractmethod
    def type_label(self) -> TypeLabel:
        """A label for the type this encoder handles.

        This should be an identifier that is unique within the format. It can NEVER be
        changed once specified if wanting to maintain backwards compatibility.
        """

    # FIXME: I suspect neither the type_spec nor type_label should not actually live
    #   on the coder. That's because two things are both decoupled from `version`.
    #   If we move a type then we should change where we build the format, but hopefully
    #   the coder itself doesn't have to be changed.
    @property
    @abc.abstractmethod
    def type_spec(self) -> TypeSpec:
        """The `TypeSpec` for the type that this coder can handle.

        Note that changing the `TypeSpec` need not trigger a bump in the `version`. For
        example, an `ImportableType` might be renamed, or moved to another module. This
        means that the type spec changes.
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

    # FIXME: open issue about avoiding cycles.
    @abc.abstractmethod
    def encode(self, value: T, fmt: SerialisationFormat) -> EncodeError | JsonType:
        """Encode `value` using this coder's current version.

        Note that this must encode recursively. Implementers should use `fmt` with
        `amber.encode` to encode any child entities.

        Will return an `EncodeError` if encoding isn't possible.
        """

    @abc.abstractmethod
    def decode(
        self,
        data: JsonType,
        fmt: SerialisationFormat,
        coder_version: int,
        amber_version: int,
    ) -> DecodeError | T:
        """Decode `data`, assuming it was encoded with `coder_version` of this coder.

        Note that `data` may contain other encoded types. Implementers should use `fmt`
        and `amber_version` with `amber.decode` to decode any child entities.

        Will return a `DecodeError` if decoding isn't possible.
        """


@typing.final
class SerialisationFormat:
    """A serialisation format is conceptually a collection of coders.

    No two coders should have the same label, and no two coders should operate on the
    same type.
    """

    def __init__(self, *, coders: Iterable[Coder[Any]]) -> None:
        # FIXME: reject coders for primitive json types
        spec_to_coder: dict[TypeSpec, Coder[Any]] = {}
        label_to_coder: dict[TypeLabel, Coder[Any]] = {}
        for coder in coders:
            spec = coder.type_spec
            label = coder.type_label
            if spec in spec_to_coder:
                msg = f"multiple coders for type spec: {spec}"
                raise ValueError(msg)
            if label in label_to_coder:
                msg = f"multiple coders for type label: {label}"
                raise ValueError(msg)
            spec_to_coder[spec] = coder
            label_to_coder[label] = coder
        self._spec_to_coder = spec_to_coder
        self._label_to_coder = label_to_coder
        self._coders = tuple(spec_to_coder.values())

    @property
    def coders(self) -> tuple[Coder[Any], ...]:
        """All `Coder` instances registered with this format."""
        return self._coders

    def find_coder_for_value[T](self, obj: T) -> Coder[T] | None:
        """Find a suitable coder for `obj`, or `None` if there isn't one."""
        # FIXME: reject coders for primitive json types
        spec = TypeSpec.from_type(type(obj))
        return self._spec_to_coder.get(spec)

    def find_coder_for_type_label(self, type_label: TypeLabel) -> Coder[Any] | None:
        """Find a suitable coder for `type_label`, or `None` if there isn't one."""
        return self._label_to_coder.get(type_label)


def encode_to_document(obj: object, fmt: SerialisationFormat) -> EncodeError | Document:
    """Encode `obj`, and place inside an amber document."""
    payload = encode(obj, fmt)
    if isinstance(payload, EncodeError):
        return payload

    return {Keys.amber_version.value: AMBER_VERSION, Keys.payload.value: payload}


def _is_valid_dict_key(x: object) -> typing.TypeGuard[str]:
    if not isinstance(x, str):
        return False
    return x not in Keys


def encode(obj: object, fmt: SerialisationFormat) -> EncodeError | JsonType:
    if isinstance(obj, _JsonElement):
        return obj

    if isinstance(obj, list):
        return _encode_list(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

    if isinstance(obj, dict):
        return _encode_dict(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

    # We have handled all native types; now we delegate to the custom coders.
    # NOTE: suppressing pyright's inability to reason that a `CoderEncoded` is a special
    #   case of `JsonType`.
    return _encode_custom(obj, fmt)  # pyright: ignore [reportReturnType]


# TODO: should these be Coders for builtins?
def _encode_list(
    obj: list[Any], fmt: SerialisationFormat
) -> EncodeError | list[JsonType]:
    result: list[JsonType] = []
    for x in obj:
        x_encoded = encode(x, fmt)
        if isinstance(x_encoded, EncodeError):
            return x_encoded
        result.append(x_encoded)
    return result


def _encode_dict(
    obj: dict[Any, typing.Any], fmt: SerialisationFormat
) -> EncodeError | dict[str, JsonType]:
    result: dict[str, JsonType] = {}
    for k, v in obj.items():
        # TODO: Support non-string keys -- this will require a different representation
        #   for a dict.
        if not _is_valid_dict_key(k):
            return UnencodableDictKey(k)
        v_encoded = encode(v, fmt)
        if isinstance(v_encoded, EncodeError):
            return v_encoded
        result[k] = v_encoded
    return result


def _encode_custom(obj: object, fmt: SerialisationFormat) -> EncodeError | CoderEncoded:
    coder = fmt.find_coder_for_value(obj)
    if coder is None:
        return NoEncoderAvailable(obj)

    payload = coder.encode(obj, fmt)
    if isinstance(payload, EncodeError):
        return payload
    return {
        Keys.type_label.value: coder.type_label,
        Keys.version.value: coder.version,
        Keys.payload.value: payload,
    }


def decode_document(
    document: Document, fmt: SerialisationFormat
) -> DecodeError | object:
    """Decode an amber document."""
    return decode(
        obj=document["_payload"], fmt=fmt, amber_version=document["_amber_version"]
    )


def decode(
    obj: JsonType, fmt: SerialisationFormat, amber_version: int
) -> DecodeError | object:
    # FIXME: version 0 should get a special error once we go stable.
    if amber_version != 0:
        return UnsupportedAmberVersion(amber_version=amber_version)

    if isinstance(obj, _JsonElement):
        return obj

    if isinstance(obj, list):
        return _decode_list(obj, fmt, amber_version)

    if isinstance(obj, dict):  # pyright: ignore [reportUnnecessaryIsInstance]
        if Keys.type_label.value in obj:
            if not _is_coder_encoded(obj):
                return InvalidCoderEncoded(obj)
            return _decode_custom(obj, fmt, amber_version)
        return _decode_dict(obj, fmt, amber_version)

    # NOTE: strictly unreachable, but we're catching the case where the function has
    # been called in a manner that doesn't obey the static types.
    typing.assert_never(obj)
    return InvalidJson(obj)


def _decode_list(
    obj: list[JsonType], fmt: SerialisationFormat, amber_version: int
) -> DecodeError | list[object]:
    res: list[object] = []
    for x in obj:
        tmp = decode(x, fmt, amber_version)
        # FIXME: that we're not getting a linter error since the success path might just
        # be an 'object'. We should probably use some kind of 'Result' type if avoiding
        # exceptions.
        if isinstance(tmp, DecodeError):
            return tmp
        res.append(x)
    return res


def _decode_dict(
    obj: dict[str, JsonType], fmt: SerialisationFormat, amber_version: int
) -> DecodeError | dict[str, object]:
    res: dict[str, object] = {}
    for k, v in obj.items():
        tmp = decode(v, fmt, amber_version)
        # FIXME: that we're not getting a linter error since the success path might just
        # be an 'object'. We should probably use some kind of 'Result' type if avoiding
        # exceptions.
        if isinstance(tmp, DecodeError):
            return tmp
        res[k] = v
    return res


def _decode_custom(
    obj: CoderEncoded, fmt: SerialisationFormat, amber_version: int
) -> DecodeError | object:
    type_label = obj[Keys.type_label.value]
    coder = fmt.find_coder_for_type_label(type_label)
    if coder is None:
        return NoDecoderAvailable(type_label)

    version = obj[Keys.version.value]
    payload = obj[Keys.payload.value]

    return coder.decode(payload, fmt, version, amber_version)

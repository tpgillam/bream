from __future__ import annotations

import abc
import dataclasses
import enum
import typing
from typing import Any, NewType

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

# FIXME: warning -- spec 0 is for pre-alpha development and WILL be broken on a
#   regular basis
BREAM_SPEC = 0
"""This integer will be incremented when the serialisation structure is changed.

Note that this is largely decoupled from the version of the `bream` package. We only
guarantee that `BREAM_SPEC` will never decrease as the package version increases.

This is useful because the Python API for using bream can change whilst the encoded
representation stays the same.
"""


class Keys(enum.Enum):
    """Special reserved keys for use in bream."""

    bream_spec = "_bream_spec"
    payload = "_payload"
    type_label = "_type"
    version = "_version"


# FIXME: should the document also contain some kind of identifier for the format? This
#    would mirror some property added to `SerialisationFormat`.
class Document(typing.TypedDict):
    """The structure of an bream document."""

    _bream_spec: int
    _payload: JsonType


class CoderEncoded(typing.TypedDict):
    """The structure of a subtree encoded with a Coder."""

    _type: TypeLabel
    _version: int
    _payload: JsonType


def _is_coder_encoded(obj: dict[str, JsonType]) -> typing.TypeGuard[CoderEncoded]:
    return (
        obj.keys() == CoderEncoded.__annotations__.keys()
        and isinstance(obj[Keys.type_label.value], str)
        and isinstance(obj[Keys.version.value], int)
    )


type _JsonElement = bool | float | int | str | None
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


_ELEMENT_TYPES = frozenset((bool, float, int, str, type(None)))


def _is_native_element(obj: object) -> typing.TypeGuard[_JsonElement]:
    # We do not use `isinstance` because we do not want to allow subtypes of known
    # element types to be accepted.
    return type(obj) in _ELEMENT_TYPES


_NATIVE_TYPE_NAMES = frozenset(x.__name__ for x in (*_ELEMENT_TYPES, list))


def _is_native_type(spec: TypeSpec) -> bool:
    return spec.module == "builtins" and spec.name in _NATIVE_TYPE_NAMES


@dataclasses.dataclass(frozen=True, slots=True)
class NoEncoderAvailable:
    value: object


@dataclasses.dataclass(frozen=True, slots=True)
class UnencodableDictKey:
    value: object


EncodeError = NoEncoderAvailable | UnencodableDictKey


@dataclasses.dataclass(frozen=True, slots=True)
class UnsupportedBreamSpec:
    """The bream spec specified for deserialisation is unsupported."""

    bream_spec: int


@dataclasses.dataclass(frozen=True, slots=True)
class NoDecoderAvailable:
    """No decoder is available for the given type_label."""

    type_label: TypeLabel


@dataclasses.dataclass(frozen=True, slots=True)
class UnsupportedCoderVersion:
    """The version requested for deserialisation is not supported."""

    coder: Coder[Any]
    version_provided: int


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidCoderEncoded:
    """Got an invalid structure that is similar to but not a `bream.CoderEncoded`."""

    obj: dict[str, JsonType]


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidPayloadData:
    coder: Coder[Any]
    data: JsonType
    msg: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class InvalidJson:
    data: object


DecodeError = (
    UnsupportedBreamSpec
    | NoDecoderAvailable
    | UnsupportedCoderVersion
    | InvalidCoderEncoded
    | InvalidPayloadData
    | InvalidJson
)


class Coder[T](abc.ABC):
    """Encapsulate encoding & decoding for a type or types."""

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
        `bream.encode` to encode any child entities.

        Will return an `EncodeError` if encoding isn't possible.
        """

    @abc.abstractmethod
    def decode(
        self,
        data: JsonType,
        fmt: SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> DecodeError | T:
        """Decode `data`, assuming it was encoded with `coder_version` of this coder.

        Note that `data` may contain other encoded types. Implementers should use `fmt`
        and `bream_spec` with `bream.decode` to decode any child entities.

        Will return a `DecodeError` if decoding isn't possible.
        """


@dataclasses.dataclass(frozen=True, slots=True)
class Codec[T]:
    """A combination of one particular type `T` and an associated coder."""

    type_label: TypeLabel
    """A label for the type `T` this codec handles.

    This should be an identifier that is unique within a format. It can NEVER be changed
    once specified if wanting to maintain backwards compatibility for this format.
    """

    type_spec: TypeSpec
    """The `TypeSpec` for the type `T` that this codec handles.

    Note that changing the `TypeSpec` need not trigger a bump in the `version`. For
    example, an `ImportableType` might be renamed, or moved to another module. This
    means that the type spec changes.
    """

    # FIXME: generic on Coder might need to be covariant? We might re-use the same
    #   coder for multiple concrete coders.
    coder: Coder[T]
    """A strategy for encoding and decoding instances of `T`."""


@typing.final
class SerialisationFormat:
    """A serialisation format is conceptually a collection of codecs.

    No two codecs should have the same label, and no two codecs should operate on the
    same type.
    """

    def __init__(self, *, codecs: Iterable[Codec[Any]]) -> None:
        spec_to_codec: dict[TypeSpec, Codec[Any]] = {}
        label_to_codec: dict[TypeLabel, Codec[Any]] = {}
        for codec in codecs:
            spec = codec.type_spec
            if _is_native_type(spec):
                msg = f"cannot add codec for native type: {spec}"
                raise ValueError(msg)
            label = codec.type_label
            if spec in spec_to_codec:
                msg = f"multiple codecs for type spec: {spec}"
                raise ValueError(msg)
            if label in label_to_codec:
                msg = f"multiple codecs for type label: {label}"
                raise ValueError(msg)
            spec_to_codec[spec] = codec
            label_to_codec[label] = codec
        self._spec_to_codec = spec_to_codec
        self._label_to_codec = label_to_codec

    def find_codec_for_value[T](self, obj: T) -> Codec[T] | None:
        """Find a suitable codec for `obj`, or `None` if there isn't one."""
        spec = TypeSpec.from_type(type(obj))
        return self._spec_to_codec.get(spec)

    def find_codec_for_type_label(self, type_label: TypeLabel) -> Codec[Any] | None:
        """Find a suitable codec for `type_label`, or `None` if there isn't one."""
        return self._label_to_codec.get(type_label)


def encode_to_document(obj: object, fmt: SerialisationFormat) -> EncodeError | Document:
    """Encode `obj`, and place inside an bream document."""
    payload = encode(obj, fmt)
    if isinstance(payload, EncodeError):
        return payload

    return {Keys.bream_spec.value: BREAM_SPEC, Keys.payload.value: payload}


def encode(obj: object, fmt: SerialisationFormat) -> EncodeError | JsonType:
    if _is_native_element(obj):
        return obj

    if type(obj) is list:
        return _encode_list(obj, fmt)  # pyright: ignore [reportUnknownArgumentType]

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


def _encode_custom(obj: object, fmt: SerialisationFormat) -> EncodeError | CoderEncoded:
    codec = fmt.find_codec_for_value(obj)
    if codec is None:
        return NoEncoderAvailable(obj)

    payload = codec.coder.encode(obj, fmt)
    if isinstance(payload, EncodeError):
        return payload
    return {
        Keys.type_label.value: codec.type_label,
        Keys.version.value: codec.coder.version,
        Keys.payload.value: payload,
    }


def decode_document(
    document: Document, fmt: SerialisationFormat
) -> DecodeError | object:
    """Decode an bream document."""
    return decode(obj=document["_payload"], fmt=fmt, bream_spec=document["_bream_spec"])


def decode(
    obj: JsonType, fmt: SerialisationFormat, bream_spec: int
) -> DecodeError | object:
    # FIXME: version 0 should get a special error once we go stable.
    if bream_spec != 0:
        return UnsupportedBreamSpec(bream_spec=bream_spec)

    if _is_native_element(obj):
        return obj

    if type(obj) is list:
        return _decode_list(obj, fmt, bream_spec)

    if type(obj) is dict:
        if not _is_coder_encoded(obj):
            return InvalidCoderEncoded(obj)
        return _decode_custom(obj, fmt, bream_spec)

    return InvalidJson(obj)


def _decode_list(
    obj: list[JsonType], fmt: SerialisationFormat, bream_spec: int
) -> DecodeError | list[object]:
    res: list[object] = []
    for x in obj:
        tmp = decode(x, fmt, bream_spec)
        # FIXME: that we're not getting a linter error since the success path might just
        # be an 'object'. We should probably use some kind of 'Result' type if avoiding
        # exceptions.
        if isinstance(tmp, DecodeError):
            return tmp
        res.append(x)
    return res


def _decode_custom(
    obj: CoderEncoded, fmt: SerialisationFormat, bream_spec: int
) -> DecodeError | object:
    type_label = obj[Keys.type_label.value]
    codec = fmt.find_codec_for_type_label(type_label)
    if codec is None:
        return NoDecoderAvailable(type_label)

    version = obj[Keys.version.value]
    payload = obj[Keys.payload.value]

    return codec.coder.decode(payload, fmt, version, bream_spec)

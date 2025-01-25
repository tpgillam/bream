"""Coders for common types that can be used in your serialisation formats."""

from __future__ import annotations

import typing

from bream.core import (
    Coder,
    DecodeError,
    EncodeError,
    InvalidPayloadData,
    JsonType,
    SerialisationFormat,
    UnsupportedCoderVersion,
    decode,
    encode,
)


@typing.final
class DictCoder(Coder[dict[object, object]]):
    """Encode and decode a Python dictionary."""

    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: dict[object, object], fmt: SerialisationFormat
    ) -> EncodeError | JsonType:
        data: list[JsonType] = []
        for k, v in value.items():
            encoded_k = encode(k, fmt)
            if isinstance(encoded_k, EncodeError):
                return encoded_k
            encoded_v = encode(v, fmt)
            if isinstance(encoded_v, EncodeError):
                return encoded_v
            data.append([encoded_k, encoded_v])

        return data

    def decode(  # noqa: PLR0911
        self,
        data: JsonType,
        fmt: SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> DecodeError | dict[object, object]:
        if coder_version != 1:
            return UnsupportedCoderVersion(self, coder_version)
        if type(data) is not list:
            return InvalidPayloadData(self, data)
        result: dict[object, object] = {}
        for encoded_item in data:
            if not (isinstance(encoded_item, list) and len(encoded_item) == 2):
                return InvalidPayloadData(self, data, f"Invalid item: {encoded_item}")
            encoded_k, encoded_v = encoded_item
            k = decode(encoded_k, fmt, bream_spec)
            if isinstance(k, DecodeError):
                return k
            if k in result:
                return InvalidPayloadData(self, data, f"Duplicate key: {k}")
            v = decode(encoded_v, fmt, bream_spec)
            if isinstance(v, DecodeError):
                return v
            result[k] = v

        return result

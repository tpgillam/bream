"""Coders for common types that can be used in your serialisation formats."""

from __future__ import annotations

import typing
from typing import Any

from bream.core import (
    Coder,
    DecodeError,
    EncodeError,
    JsonType,
    SerialisationFormat,
    UnsupportedCoderVersion,
    decode,
    encode,
)


@typing.final
class DictCoder(Coder[dict[Any, Any]]):
    """Encode and decode a Python dictionary."""

    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: dict[Any, Any], fmt: SerialisationFormat
    ) -> EncodeError | JsonType:
        return [[encode(k, fmt), encode(v, fmt)] for k, v in value.items()]

    def decode(
        self,
        data: JsonType,
        fmt: SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> DecodeError | dict[Any, Any]:
        if coder_version != 1:
            return UnsupportedCoderVersion(self, coder_version)
        assert isinstance(data, list)
        return {
            decode(encoded_k, fmt, bream_spec): decode(encoded_v, fmt, bream_spec)
            for encoded_k, encoded_v in data
        }

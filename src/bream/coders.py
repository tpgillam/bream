"""Coders for common types that can be used in your serialisation formats."""

from __future__ import annotations

import typing

from bream.core import Coder, JsonType, SerialisationFormat, decode, encode


@typing.final
class DictCoder(Coder[dict[object, object]]):
    """Encode and decode a Python dictionary."""

    @property
    def version(self) -> int:
        return 1

    def encode(self, value: dict[object, object], fmt: SerialisationFormat) -> JsonType:
        return [[encode(k, fmt), encode(v, fmt)] for k, v in value.items()]

    def decode(
        self,
        data: JsonType,
        fmt: SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> dict[object, object]:
        if coder_version != 1:
            msg = f"Unsupported coder_version: {coder_version}"
            raise ValueError(msg)
        if type(data) is not list:
            msg = f"Invalid payload data: {self}, {data}"
            raise ValueError(msg)
        result: dict[object, object] = {}
        for encoded_item in data:
            if not (isinstance(encoded_item, list) and len(encoded_item) == 2):
                msg = f"Invalid payload data: {self}, {data}, bad item: {encoded_item}"
                raise ValueError(msg)
            encoded_k, encoded_v = encoded_item
            k = decode(encoded_k, fmt, bream_spec)
            if k in result:
                msg = f"Invalid payload data: {self}, {data}, duplicate key: {k}"
                raise ValueError(msg)
            result[k] = decode(encoded_v, fmt, bream_spec)

        return result

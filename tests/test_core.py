from __future__ import annotations

from typing import Any

import bream
from bream.core import EncodeError


def test_scalar_encode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    assert bream.encode(None, fmt) is None
    assert bream.encode(2, fmt) == 2
    assert bream.encode(4.2, fmt) == 4.2
    assert bream.encode("moo", fmt) == "moo"


def test_list_encode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    x = [None, 2, 4.2, "moo"]
    x_encoded = bream.encode(x, fmt)
    assert x_encoded == x
    assert x_encoded is not x


def test_unsupported_encode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    assert bream.encode(1j, fmt) == bream.core.NoEncoderAvailable(value=1j)
    assert bream.encode((42,), fmt) == bream.core.NoEncoderAvailable(value=(42,))
    assert bream.encode({3}, fmt) == bream.core.NoEncoderAvailable(value={3})


def test_scalar_decode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    bream_spec = 0
    assert bream.decode(None, fmt, bream_spec) is None
    assert bream.decode(2, fmt, bream_spec) == 2
    assert bream.decode(4.2, fmt, bream_spec) == 4.2
    assert bream.decode("moo", fmt, bream_spec) == "moo"


def test_list_decode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    bream_spec = 0
    x: list[bream.JsonType] = [None, 2, 4.2, "moo"]
    x_decoded = bream.decode(x, fmt, bream_spec)
    assert x_decoded == x
    assert x_decoded is not x


def test_nested_structure_round_trip() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    x = [None, 2, 4.2, "moo"]
    y = ["a", None, x]
    y_encoded = bream.encode(y, fmt)
    assert not isinstance(y_encoded, EncodeError)
    assert y_encoded == y
    assert y_encoded is not y
    y_decoded = bream.decode(y_encoded, fmt, bream.core.BREAM_SPEC)
    assert y_decoded is not y
    assert y_decoded == y


def test_simple_document_round_trip() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    for x in (None, 2, 4.2, "moo", [1, None, 3], ["a", [3, 4], "b", ["c", 4.2]]):
        document = bream.encode_to_document(x, fmt)
        assert not isinstance(document, bream.EncodeError)
        assert document == {"_bream_spec": bream.core.BREAM_SPEC, "_payload": x}
        new_x = bream.decode_document(document, fmt)
        assert new_x == x
        if isinstance(x, list | dict):
            # Mutable python structures should not be identically equal, lest mutation
            # occurs.
            assert document["_payload"] is not x
            assert new_x is not document["_payload"]
            assert new_x is not x


class _MyFloat(float):
    pass


def test_float_subtype_not_accepted() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    x = _MyFloat(1)
    assert isinstance(x, float)
    x_encoded = bream.encode(x, fmt)
    assert x_encoded == bream.core.NoEncoderAvailable(x)


class _MyList(list[Any]):
    pass


def test_list_subtype_not_accepted() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    x = _MyList([1, 2, 3])
    assert isinstance(x, list)
    x_encoded = bream.encode(x, fmt)
    assert x_encoded == bream.core.NoEncoderAvailable(x)

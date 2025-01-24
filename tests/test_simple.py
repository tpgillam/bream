from __future__ import annotations

import bream


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


def test_dict_encode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    x = {"a": None, "b": 2, "c": 4.2, "d": "moo"}
    x_encoded = bream.encode(x, fmt)
    assert x_encoded == x
    assert x_encoded is not x


def test_nested_structure_encode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    x = [None, 2, 4.2, "moo"]
    y = {"a": None, "b": 2, "c": 4.2, "d": "moo", "e": x}
    y_encoded = bream.encode(y, fmt)
    assert y_encoded == y
    assert y_encoded is not y


def test_unsupported_encode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    assert bream.encode(1j, fmt) == bream.NoEncoderAvailable(value=1j)
    assert bream.encode((42,), fmt) == bream.NoEncoderAvailable(value=(42,))
    assert bream.encode({3}, fmt) == bream.NoEncoderAvailable(value={3})


def test_scalar_decode() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    bream_spec = 0
    assert bream.decode(None, fmt, bream_spec) is None
    assert bream.decode(2, fmt, bream_spec) == 2
    assert bream.decode(4.2, fmt, bream_spec) == 4.2
    assert bream.decode("moo", fmt, bream_spec) == "moo"


# FIXME: test decode basic types
# FIXME: test decode basic types
# FIXME: test decode basic types


def test_simple_document_round_trip() -> None:
    fmt = bream.SerialisationFormat(codecs=())
    for x in (None, 2, 4.2, "moo", [1, None, 3], {"a": [3, 4], "b": {"c": 4.2}}):
        document = bream.encode_to_document(x, fmt)
        assert not isinstance(document, bream.EncodeError)
        assert document == {"_bream_spec": bream.BREAM_SPEC, "_payload": x}
        new_x = bream.decode_document(document, fmt)
        assert new_x == x
        if isinstance(x, list | dict):
            # Mutable python structures should not be identically equal, lest mutation
            # occurs.
            assert document["_payload"] is not x
            assert new_x is not document["_payload"]
            assert new_x is not x

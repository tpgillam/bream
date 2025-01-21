from __future__ import annotations

import amber


def test_scalar_encode() -> None:
    fmt = amber.SerialisationFormat(coders=())
    assert amber.encode(None, fmt) is None
    assert amber.encode(2, fmt) == 2
    assert amber.encode(4.2, fmt) == 4.2
    assert amber.encode("moo", fmt) == "moo"


def test_list_encode() -> None:
    fmt = amber.SerialisationFormat(coders=())
    x = [None, 2, 4.2, "moo"]
    x_encoded = amber.encode(x, fmt)
    assert x_encoded == x
    assert x_encoded is not x


def test_dict_encode() -> None:
    fmt = amber.SerialisationFormat(coders=())
    x = {"a": None, "b": 2, "c": 4.2, "d": "moo"}
    x_encoded = amber.encode(x, fmt)
    assert x_encoded == x
    assert x_encoded is not x


def test_nested_structure_encode() -> None:
    fmt = amber.SerialisationFormat(coders=())
    x = [None, 2, 4.2, "moo"]
    y = {"a": None, "b": 2, "c": 4.2, "d": "moo", "e": x}
    y_encoded = amber.encode(y, fmt)
    assert y_encoded == y
    assert y_encoded is not y


def test_unsupported_encode() -> None:
    fmt = amber.SerialisationFormat(coders=())
    assert amber.encode(1j, fmt) == amber.NoEncoderAvailable(value=1j)
    assert amber.encode((42,), fmt) == amber.NoEncoderAvailable(value=(42,))
    assert amber.encode({3}, fmt) == amber.NoEncoderAvailable(value={3})


# FIXME: test decode basic types
# FIXME: test decode basic types
# FIXME: test decode basic types

def test_document() -> None:
    fmt = amber.SerialisationFormat(coders=())
    for x in (None, 2, 4.2, "moo", [1, None, 3], {"a": [3, 4], "b": {"c": 4.2}}):
        document = amber.encode_to_document(x, fmt)
        assert not isinstance(document, amber.EncodeError)
        assert document == {"_amber_version": amber.AMBER_VERSION, "_payload": x}
        new_x = amber.decode_document(document, fmt)
        assert new_x == x
        if isinstance(x, list | dict):
            # Mutable python structures should not be identically equal, lest mutation
            # occurs.
            assert document["_payload"] is not x
            assert new_x is not document["_payload"]
            assert new_x is not x

from __future__ import annotations

import bream


def _serialisation_format() -> bream.SerialisationFormat:
    """A serialisation format including built-in coders."""
    return bream.SerialisationFormat(
        codecs=[
            bream.Codec(
                bream.TypeLabel("dict"),
                bream.TypeSpec.from_type(dict),
                bream.coders.DictCoder(),
            )
        ]
    )


def test_dict_str_key_round_trip() -> None:
    fmt = _serialisation_format()
    x = {"a": None, "b": 2, "c": 4.2, "d": "moo"}
    x_encoded = bream.encode(x, fmt)
    assert isinstance(x_encoded, dict)
    assert x_encoded is not x

    assert x_encoded == {
        "_type": "dict",
        "_version": 1,
        "_payload": [["a", None], ["b", 2], ["c", 4.2], ["d", "moo"]],
    }
    x_decoded = bream.decode(x_encoded, fmt, bream.core.BREAM_SPEC)
    assert x_decoded is not x
    assert x_decoded == x


def test_dict_non_str_key_round_trip() -> None:
    fmt = _serialisation_format()
    x = {1: None, False: 2, "c": 4.2, None: "moo"}
    x_encoded = bream.encode(x, fmt)
    assert isinstance(x_encoded, dict)
    assert x_encoded is not x

    assert x_encoded == {
        "_type": "dict",
        "_version": 1,
        "_payload": [[1, None], [False, 2], ["c", 4.2], [None, "moo"]],
    }
    x_decoded = bream.decode(x_encoded, fmt, bream.core.BREAM_SPEC)
    assert x_decoded is not x
    assert x_decoded == x


def test_nested_structure_round_trip() -> None:
    fmt = _serialisation_format()
    x = [None, 2, 4.2, "moo"]
    y = {"a": None, False: 2, "c": 4.2, None: "moo", "e": x}
    y_encoded = bream.encode(y, fmt)
    assert isinstance(y_encoded, dict)
    assert y_encoded is not y
    assert y_encoded == {
        "_type": "dict",
        "_version": 1,
        "_payload": [
            ["a", None],
            [False, 2],
            ["c", 4.2],
            [None, "moo"],
            ["e", [None, 2, 4.2, "moo"]],
        ],
    }

    y_decoded = bream.decode(y_encoded, fmt, bream.core.BREAM_SPEC)
    assert y_decoded is not y
    assert y_decoded == y

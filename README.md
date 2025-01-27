# **WARNING** 
bream is currently in pre-alpha development, and does _NOT_ yet have a
    stable serialisation format.

Any release in the 0.0.x series may contain breaking changes.

Please do test-drive and give feedback, or else check back soon for a stable version!

**END WARNING**   

---

# bream

[![image](https://img.shields.io/pypi/v/bream.svg)](https://pypi.python.org/pypi/bream)
[![image](https://img.shields.io/pypi/l/bream.svg)](https://github.com/tpgillam/bream/blob/main/LICENSE)
[![image](https://img.shields.io/pypi/pyversions/bream.svg)](https://pypi.python.org/pypi/bream)
[![Actions status](https://github.com/tpgillam/bream/workflows/CI/badge.svg)](https://github.com/tpgillam/bream/actions)

`bream` is an explictly versioned encode/decode framework targetting JSON-like trees.

## Goals and non-goals
`bream` aims to be the following:
- Simple: encode to a human-readable JSON tree.
- Explicit: no silent conversion. User-provided versions, easy upgrades.
- Modular: bring-your-own codecs.

It _does not_ aim to be fast. Speed isn't a current design goal.

## Data structure
A JSON-like tree is a nested combination of `dict` (with `str` keys only), `list`, `int`,
`float`, `str`, `bool` and `None`.

A bream document is a `dict` with some metadata and a payload; many JSON trees
will be valid payload. For example:
```json
{
    "_bream_spec": 1,
    "_payload": {
        "serialised": ["data", "goes", "here"]
    }
}
```

## Encoded objects
Certain JSON trees represent 'encoded' Python objects. Any such tree is a
`dict` with a particular structure. Here's how `complex(0.123, 0.456)` might be
encoded:
```json
{
    "_type_label": "complex",
    "_version": 1,
    "_payload": {
        "real": 0.123,
        "imag": 0.456
    }
}
```
The three top-level fields are special:
- `_type_label` is a unique label for the type.
- `_version` is incremented whenever the structure of `_payload` needs to change.
- `_payload` is some JSON data (that may or may not be a dict).

A `Coder` is an object which knows how to convert from the payload back to a Python
object. For example, for the `complex` format above:
```python
@typing.final
class ComplexCoder(bream.Coder[complex]):
    """An demonstration coder for Python's `complex` type."""

    @property
    def version(self) -> int:
        return 1

    def encode(
        self, value: complex, fmt: bream.SerialisationFormat
    ) -> bream.EncodeError | bream.JsonType:
        del fmt
        return {"real": value.real, "imag": value.imag}

    def decode(
        self,
        data: bream.JsonType,
        fmt: bream.SerialisationFormat,
        coder_version: int,
        bream_spec: int,
    ) -> bream.DecodeError | complex:
        del bream_spec, fmt
        if coder_version != 1:
            return bream.core.UnsupportedCoderVersion(self, coder_version)
        if not isinstance(data, dict) or data.keys() != {"real", "imag"}:
            return bream.core.InvalidPayloadData(self, data, "Invalid keys")
        if not isinstance(data["real"], float):
            return bream.core.InvalidPayloadData(self, data, "Invalid 'real'")
        if not isinstance(data["imag"], float):
            return bream.core.InvalidPayloadData(self, data, "Invalid 'imag'")
        return complex(data["real"], data["imag"])
````

A `Coder` instance has a particular version associated with it. It is the
responsibility of `Coder.decode` to be able to decode _older_ versions too, if
possible.

We tell bream to use particular `Coder`s for particular types by creating a
`SerialisationFormat`. This lists all coders, and explicitly ties them to
concrete types:
```python
bream.SerialisationFormat(
    codecs=[
        bream.Codec(
            bream.TypeLabel("complex"),
            bream.TypeSpec.from_type(complex),
            coder_complex,
        ),
```

A few notes:
- the serialisation format is _not_ itself serialised. This is deliberate!
- the choice of `TypeLabel` is arbitrary; it's just a name that shouldn't be changed within a serialisation format
- the `TypeSpec` tells bream the module & name of the type. If a custom type is moved, this lets you reflect that and
    not break serialised data (unlike pickled, which effectively serialises the type spec).


## Advantages of versioning
The main advantage of explicitly encoding & decoding your objects with bream is the
ability to _version_ the encoded form, and then provide a "compatibility decode" pathway
to decode an older encoded representation into the latest in-memory representation.

This also means that upgrading an 'old' file on disk is as simple as decoding then
encoding again.

Separating the `Coder`s from the type being encoded also has the advantage that you can
write custom serialisation for builtin or third-party types not under your direct
control.

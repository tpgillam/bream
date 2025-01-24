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

An bream tree is a `dict` with some metadata and a payload; any valid JSON tree is a valid
payload. For example:
```json
{
    "_bream_spec": 1,
    "_payload": {
        "serialised": ["data", "goes", "here"]
    }
}
```

Any JSON tree is a valid bream payload.

## Encoded objects
Certain JSON trees within a payload represent 'encoded' Python objects. Any such tree
is a `dict` with a particular structure. Here's how `complex(0.123, 0.456)` might be
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
object.


## Advantages of versioning
The main advantage of explicitly encoding & decoding your objects with bream is the
ability to _version_ the encoded form, and then provide a "compatibility decode" pathway
to decode an older encoded representation into the latest in-memory representation.

This also means that upgrading an 'old' file on disk is as simple as decoding then
encoding again.

Separating the `Coder`s from the type being encoded also has the advantage that you can
write custom serialisation for builtin or third-party types not under your direct
control.

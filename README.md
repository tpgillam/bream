# amber
amber is an explictly versioned encode/decode library for JSON-like trees.

## Data structure
A JSON tree is a nested combination of `dict` (with `str` keys only), `list`, `int`,
`float`, `str`, `bool` and `None`.

An amber tree is a `dict` with some metadata and a payload; any valid JSON tree is a valid
payload. For example:
```json
{
    "__amber_version": 1,
    "__payload": {<<...serialised data here...>>}
}
```

Any JSON tree is a valid amber payload.

## Encoded objects
Certain JSON trees within a payload represent 'encoded' Python objects. Any such tree
is a `dict` with a particular structure. Here's how `complex(0.123, 0.456)` might be
encoded:
```json
{
    "__type_label": "complex",
    "__version": 1,
    "__payload": {
        "real": 0.123,
        "imag": 0.456
    }
}
```
The three top-level fields are special:
- `__type_label` is a unique label for the type.
- `__version` is incremented whenever the structure of `__payload` needs to change.
- `__payload` is some JSON data (that may or may not be a dict).

A `Coder` is an object which knows how to convert from the payload back to a Python
object.

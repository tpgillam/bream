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

### Coders
Certain JSON trees within a payload can be 'decoded' into Python objects. Any such tree
is a `dict` with particular metadata. Here's how `complex(0.123, 0.456)` might be
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


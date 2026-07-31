# EmBody protocol codec

[![PyPI](https://img.shields.io/pypi/v/embody-codec.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/embody-codec.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/embody-codec)][python version]
[![License](https://img.shields.io/pypi/l/embody-codec)][license]

[![Tests](https://github.com/aidee-health/embody-codec/workflows/Tests/badge.svg)][tests]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)][ruff]

[pypi_]: https://pypi.org/project/embody-codec/
[status]: https://pypi.org/project/embody-codec/
[python version]: https://pypi.org/project/embody-codec
[tests]: https://github.com/aidee-health/embody-codec/actions?workflow=Tests
[pre-commit]: https://github.com/pre-commit/pre-commit
[ruff]: https://github.com/astral-sh/ruff

This is a Python based implementation library for the Aidee EmBody communication protocol.

## Features

- **High-performance message decoding** with O(1) lookup using optimized message registries
- **Comprehensive protocol support** for all EmBody message types
- **Robust error handling** with detailed error messages and optional CRC validation bypass
- **Type-safe implementations** with full type annotations for better IDE support
- **Zero dependencies** for the core library
- **Extensive test coverage** ensuring protocol compliance

## Requirements

- This library does not require any external libraries
- Requires Python 3.12+

## Installation

You can install _embody codec_ via [pip] from [PyPI]:

```console
pip install embody-codec
```

## Usage Examples

### Basic Message Encoding/Decoding

```python
from embodycodec import codec

# Create and encode a heartbeat message
heartbeat = codec.Heartbeat()
encoded_data = heartbeat.encode()

# Decode received data
decoded_msg = codec.decode(encoded_data)
print(f"Received: {type(decoded_msg).__name__}")
```

### Working with Attributes

```python
from embodycodec import codec, attributes

# Create a set attribute message
attr = attributes.BatteryLevelAttribute(value=85)
msg = codec.SetAttribute(attribute_id=attr.attribute_id, value=attr)
encoded = msg.encode()

# Decode and access attribute value
decoded = codec.decode(encoded)
print(f"Battery level: {decoded.value.value}%")
```

### Error Handling

```python
from embodycodec import codec
from embodycodec.exceptions import CrcError, DecodeError

try:
    # Decode with CRC validation
    msg = codec.decode(data)
except CrcError:
    # Handle CRC error - optionally decode anyway
    msg = codec.decode(data, accept_crc_error=True)
except DecodeError as e:
    print(f"Decode failed: {e}")
```

## Upgrading to 2.0.0

Every break below is the removal of an API that never worked correctly. Nothing here
changes behaviour that was previously right.

**`codec.SendFileResponse.crc` is renamed to `file_crc`.** The old name collided with
`Message.crc`, which holds the message footer CRC and is assigned during decode — so the
file CRC was silently overwritten. Reading `.crc` on this class never returns the file
CRC, so it must be replaced rather than left alone:

```python
SendFileResponse(crc=x)   ->  SendFileResponse(file_crc=x)
response.crc              ->  response.file_crc
```

**`file_codec.BatteryDiagnostics.length()` returns 26, not 24.** It excluded the two-byte
timestamp that every other message counts, so a parser walking a file by advancing
`1 + length()` desynced by two bytes on every such record. If you compensated for this,
remove the compensation.

**`file_codec.BatteryDiagnostics.struct_format` is gone**, replaced by `unpack_format`
(the name its base class actually reads). Note this is the `file_codec` class; the
unrelated `types.BatteryDiagnostics.struct_format` is unchanged.

**`file_codec.PulseBlockEcg.encode()` and `PulseBlockPpg.encode()` raise
`NotImplementedError`.** They previously returned two zero bytes regardless of contents.
File-format messages are produced by the device and are decode-only.

One fix that needs no code change but does change bytes on the wire: `SetAttribute` now
writes the true payload length for variable-length attributes (`ModelAttribute`,
`VendorAttribute`, `SystemStatusNamesAttribute`, `SystemStatusAttribute`,
`PulseRawListAttribute`). It previously wrote `0`, so a conforming parser dropped those
values. Fixed-size attributes encode exactly as before.

## Changelog

See the [releases page](https://github.com/aidee-health/embody-codec/releases) for the changelog.

## Contributing

Contributions are very welcome. To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license].

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

Inspiration collected from [Cookiecutter UV] template.

[pypi]: https://pypi.org/
[Cookiecutter UV]: https://github.com/fpgmaas/cookiecutter-uv
[file an issue]: https://github.com/aidee-health/embody-codec/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/aidee-health/embody-codec/blob/main/LICENSE
[contributor guide]: https://github.com/aidee-health/embody-codec/blob/main/CONTRIBUTING.md

<!-- done github-only -->

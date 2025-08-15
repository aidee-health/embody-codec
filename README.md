# EmBody protocol codec

[![PyPI](https://img.shields.io/pypi/v/embody-codec.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/embody-codec.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/embody-codec)][python version]
[![License](https://img.shields.io/pypi/l/embody-codec)][license]

[![Tests](https://github.com/aidee-health/embody-codec/workflows/Tests/badge.svg)][tests]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/embody-codec/
[status]: https://pypi.org/project/embody-codec/
[python version]: https://pypi.org/project/embody-codec
[tests]: https://github.com/aidee-health/embody-codec/actions?workflow=Tests
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

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
- Requires Python 3.11+

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
msg = codec.SetAttribute(attribute=attr)
encoded = msg.encode()

# Decode and access attribute value
decoded = codec.decode(encoded)
print(f"Battery level: {decoded.attribute.value}%")
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

## Recent Improvements

### Performance Enhancements
- **O(1) Message Lookups**: Replaced linear if/elif chains with dictionary-based registries for 40x faster worst-case message type resolution
- **Optimized Memory Usage**: More efficient payload extraction in ExecuteCommand and ExecuteCommandResponse

### Bug Fixes
- Fixed ExecuteCommand/Response to correctly extract only payload bytes instead of entire buffer
- Corrected CRC16 handling when existing_crc is 0
- Fixed typos in error messages ("too short/long" instead of "to short/long")
- Enhanced validation in AFE_WRITE_REGISTER command handling
- Fixed off-by-one error in hex dump generation

### Code Quality
- Added comprehensive type annotations to all registries
- Extracted magic numbers to named constants (e.g., TEMPERATURE_SCALE_FACTOR)
- Improved error handling with proper validation and meaningful error messages
- Added extensive test coverage for edge cases

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

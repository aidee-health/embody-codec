"""Specific exceptions for package."""
from embodycodec import codec


class DecodeError(Exception):
    """Exception when decoding message."""

    ...


class CrcError(Exception):
    """Error when invalid crc is received for message from device."""

    ...

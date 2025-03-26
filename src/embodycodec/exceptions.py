"""Specific exceptions for package."""


class DecodeError(Exception):
    """Exception when decoding message."""

    pass

    ...


class CrcError(Exception):
    """Error when invalid crc is received for message from device."""

    pass

    ...

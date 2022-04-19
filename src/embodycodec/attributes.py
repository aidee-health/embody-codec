"""Attribute types for the EmBody device

All attribute types inherits from the Attribute class, and provides self-contained encoding and decoding of
attributes.
"""

from abc import ABC
import struct
from dataclasses import dataclass, astuple
import time
from .types import *


@dataclass
class Attribute(ABC):
    """Abstract base class for attribute types"""

    struct_format = None
    """struct format used to pack/unpack object - must be set by subclasses"""

    attribute_id = None
    """attribute id field - must be set by subclasses"""

    @classmethod
    def length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls, data: bytes):
        """Decode bytes into attribute object"""
        if len(data) < cls.length():
            raise BufferError("Buffer too short for message")
        attr = cls(*(struct.unpack(cls.struct_format, data[0:cls.length()])))
        return attr

    def encode(self) -> bytes:
        """Encode an attribute object to bytes"""
        return struct.pack(self.struct_format, *astuple(self))


@dataclass
class BatteryLevel(Attribute):
    struct_format = ">B"
    attribute_id = 0xA1
    level: int


@dataclass
class PulseRawAllAttribute(Attribute):
    struct_format = PulseRawAll.struct_format
    attribute_id = 0xA2
    value: PulseRawAll


@dataclass
class CurrentTime(Attribute):
    struct_format = ">Q"
    attribute_id = 0x71
    datetime: int = time.time_ns() // 1_000_000


def decode_attribute(attribute_id, data: bytes) -> Attribute:
    """Decodes a bytes object into proper attribute object - raises BufferError if data buffer is too short.
    Returns None if unknown attribute"""

    if attribute_id == CurrentTime.attribute_id:
        return CurrentTime.decode(data)
    return None

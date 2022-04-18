"""Codec for the EmBody device
A full embodycodec for the protocol specified for the EmBody device

All protocol message types inherits from the Message class, and provides self-contained encoding and decoding of
messages.
"""

from abc import ABC, abstractmethod
import struct
from dataclasses import dataclass, field
from .crc import crc16


@dataclass
class Message(ABC):
    # unpack format to be overridden by sub-classes, see https://docs.python.org/3/library/struct.html#format-characters
    # does not include header (type and length field) or footer (crc)
    struct_format = None
    # Protocol type field - must be set by subclasses
    msg_type = None
    # crc footer is dynamically set
    crc = None

    @classmethod
    def __body_length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def __full_length(cls) -> int:
        return cls.__body_length() + 5  # body length + header length + footer length

    @classmethod
    def decode(cls, data: bytes):
        """Decode bytes into message object"""
        if len(data) < cls.__body_length():
            raise BufferError("Buffer too short for message")
        msg = cls(*(struct.unpack(cls.struct_format, data[0:cls.__body_length()])))
        msg.crc, = struct.unpack(">H", data[cls.__body_length():])
        return msg

    def encode(self) -> bytes:
        """Encode a message object to bytes"""
        header = struct.pack(">BH", self.msg_type, type(self).__full_length())
        body = self._encode_body()
        header_and_body = header + body
        crc_calculated = crc16(header_and_body)
        crc = struct.pack(">H", crc_calculated)
        return header_and_body + crc

    @abstractmethod
    def _encode_body(self) -> bytes:
        return b''  # should be overridden by subclasses


@dataclass
class Heartbeat(Message):
    struct_format = ""  # heartbeat message has no attributes
    msg_type = 0x01

    def _encode_body(self):
        return b''


@dataclass
class GetAttribute(Message):
    struct_format = ">B"
    msg_type = 0x12
    attribute_id: int

    def _encode_body(self):
        return struct.pack(self.struct_format, self.attribute_id)


# Decode message - raises BufferError if data buffer is too short. Returns None if unknown message type
def decode(data: bytes) -> Message:
    """Decodes a bytes object into proper message object"""
    message_type = data[0]
    if message_type == Heartbeat.msg_type:
        return Heartbeat.decode(data[3:])
    if message_type == GetAttribute.msg_type:
        return GetAttribute.decode(data[3:])
    return None

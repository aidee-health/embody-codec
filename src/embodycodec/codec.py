"""Codec for the EmBody device
A full embodycodec for the protocol specified for the EmBody device

All protocol message types inherits from the Message class, and provides self-contained encoding and decoding of
messages.
"""

from abc import ABC, abstractmethod
import struct
from dataclasses import dataclass
from .crc import crc16


@dataclass
class Message(ABC):
    """Abstract base class for protocol messages"""

    struct_format = ""
    """unpack format to be overridden by sub-classes, see 
    https://docs.python.org/3/library/struct.html#format-characters 
    does not include header (type and length field) or footer (crc)"""

    msg_type = None
    """Protocol type field - must be set by subclasses"""

    crc = None
    """crc footer is dynamically set"""

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
        return bytes()


@dataclass
class Heartbeat(Message):

    msg_type = 0x01

    def _encode_body(self) -> bytes:
        return bytes()


@dataclass
class HeartbeatResponse(Message):

    msg_type = 0x81

    def _encode_body(self) -> bytes:
        return bytes()


@dataclass
class NackResponse(Message):

    struct_format = ">B"
    error_messages = {0x01: 'Unknown message type', 0x02: 'Unknown message content', 0x03: 'Unknown attribute',
                      0x04: 'Message to short', 0x05: 'Message to long', 0x06: 'Message with illegal CRC',
                      0x07: 'Message buffer full', 0x08: 'File system error', 0x09: 'Delete file error',
                      0x0A: 'File not found', 0x0B: 'Retransmit failed', 0x0C: 'File not opened'}
    msg_type = 0x82
    response_code: int

    def _encode_body(self) -> bytes:
        return struct.pack(self.struct_format, self.response_code)

    def error_message(self) -> str:
        if self.response_code is None:
            return None
        return self.error_messages.get(self.response_code)


@dataclass
class GetAttribute(Message):

    struct_format = ">B"
    msg_type = 0x12
    attribute_id: int

    def _encode_body(self):
        return struct.pack(self.struct_format, self.attribute_id)


def decode(data: bytes) -> Message:
    """Decodes a bytes object into proper message object - raises BufferError if data buffer is too short.
    Returns None if unknown message type"""

    message_type = data[0]
    if message_type == Heartbeat.msg_type:
        return Heartbeat.decode(data[3:])
    if message_type == HeartbeatResponse.msg_type:
        return HeartbeatResponse.decode(data[3:])
    if message_type == NackResponse.msg_type:
        return NackResponse.decode(data[3:])
    if message_type == GetAttribute.msg_type:
        return GetAttribute.decode(data[3:])
    return None

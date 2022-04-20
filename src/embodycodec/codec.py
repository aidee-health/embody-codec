"""Codec for the EmBody device
A full embodycodec for the protocol specified for the EmBody device

All protocol message types inherits from the Message class, and provides self-contained encoding and decoding of
messages.
"""

from abc import ABC
import struct
from dataclasses import dataclass, astuple
from .crc import crc16
from .attributes import *
from .types import *


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
    def decode(cls, data: bytes):
        """Decode bytes into message object"""
        msg = cls(*(struct.unpack(cls.struct_format, data[0:cls.__body_length()])))
        msg.crc, = struct.unpack(">H", data[cls.__body_length():])
        return msg

    def encode(self) -> bytes:
        """Encode a message object to bytes"""
        body = self._encode_body()
        header = struct.pack(">BH", self.msg_type, len(body) + 5)
        header_and_body = header + body
        crc_calculated = crc16(header_and_body)
        crc = struct.pack(">H", crc_calculated)
        return header_and_body + crc

    def _encode_body(self) -> bytes:
        return struct.pack(self.struct_format, *astuple(self))


@dataclass
class Heartbeat(Message):
    msg_type = 0x01


@dataclass
class HeartbeatResponse(Message):
    msg_type = 0x81


@dataclass
class NackResponse(Message):
    struct_format = ">B"
    error_messages = {0x01: 'Unknown message type', 0x02: 'Unknown message content', 0x03: 'Unknown attribute',
                      0x04: 'Message to short', 0x05: 'Message to long', 0x06: 'Message with illegal CRC',
                      0x07: 'Message buffer full', 0x08: 'File system error', 0x09: 'Delete file error',
                      0x0A: 'File not found', 0x0B: 'Retransmit failed', 0x0C: 'File not opened'}
    msg_type = 0x82
    response_code: int

    def error_message(self) -> str:
        if self.response_code is None:
            return None
        return self.error_messages.get(self.response_code)


@dataclass
class SetAttribute(Message):
    msg_type = 0x11
    length = None
    attribute_id: int
    value: Attribute

    @classmethod
    def decode(cls, data: bytes):
        attribute_id, = struct.unpack(">B", data[0:1])
        length, = struct.unpack(">B", data[1:2])
        value = decode_attribute(attribute_id, data[2:])
        msg = SetAttribute(attribute_id=attribute_id, value=value)
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">B", self.attribute_id)
        length_part = struct.pack(">B", self.value.length())
        attribute_part = self.value.encode()
        return first_part_of_body + length_part + attribute_part


@dataclass
class SetAttributeResponse(Message):
    msg_type = 0x91


@dataclass
class GetAttribute(Message):
    struct_format = ">B"
    msg_type = 0x12
    attribute_id: int


@dataclass
class GetAttributeResponse(Message):
    msg_type = 0x92
    length = None
    attribute_id: int
    changed_at: int
    reporting: Reporting
    value: Attribute

    @classmethod
    def decode(cls, data: bytes):
        attribute_id, = struct.unpack(">B", data[0:1])
        changed_at, = struct.unpack(">Q", data[1:9])
        reporting = Reporting.decode(data[9:9+Reporting.length()])
        length, =  struct.unpack(">B", data[9+Reporting.length():9+Reporting.length()+1])
        value = decode_attribute(attribute_id, data[9+Reporting.length()+1:])
        msg = GetAttributeResponse(attribute_id=attribute_id, changed_at=changed_at, reporting=reporting,
                                   value=value)
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">BQ", self.attribute_id, self.changed_at)
        reporting_part = self.reporting.encode()
        length_part = struct.pack(">B", self.value.length())
        attribute_part = self.value.encode()
        return first_part_of_body + reporting_part + length_part + attribute_part


@dataclass
class ResetAttribute(Message):
    struct_format = ">B"
    msg_type = 0x13
    attribute_id: int


@dataclass
class ResetAttributeResponse(Message):
    msg_type = 0x93


@dataclass
class ConfigureReporting(Message):
    msg_type = 0x14
    attribute_id: int
    reporting: Reporting

    @classmethod
    def decode(cls, data: bytes):
        attribute_id, = struct.unpack(">B", data[0:1])
        reporting = Reporting.decode(data[1:1+Reporting.length()])
        msg = ConfigureReporting(attribute_id=attribute_id, reporting=reporting)
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">B", self.attribute_id)
        reporting_part = self.reporting.encode()
        return first_part_of_body + reporting_part


@dataclass
class ConfigureReportingResponse(Message):
    msg_type = 0x94


@dataclass
class ResetReporting(Message):
    struct_format = ">B"
    msg_type = 0x15
    attribute_id: int


@dataclass
class ResetReportingResponse(Message):
    msg_type = 0x95


@dataclass
class PeriodicRecording(Message):
    msg_type = 0x16
    recording: Recording

    @classmethod
    def decode(cls, data: bytes):
        recording = Recording.decode(data[0:Recording.length()])
        msg = PeriodicRecording(recording=recording)
        return msg

    def _encode_body(self) -> bytes:
        return self.recording.encode()


@dataclass
class PeriodicRecordingResponse(Message):
    msg_type = 0x96


@dataclass
class AttributeChanged(Message):
    msg_type = 0x21
    length = None
    changed_at: int
    attribute_id: int
    value: Attribute

    @classmethod
    def decode(cls, data: bytes):
        changed_at, = struct.unpack(">Q", data[0:8])
        attribute_id, = struct.unpack(">B", data[8:9])
        length, =  struct.unpack(">B", data[9:10])
        value = decode_attribute(attribute_id, data[10:])
        msg = AttributeChanged(changed_at=changed_at, attribute_id=attribute_id, value=value)
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">QB", self.changed_at, self.attribute_id)
        length_part = struct.pack(">B", self.value.length())
        attribute_part = self.value.encode()
        return first_part_of_body + length_part + attribute_part


@dataclass
class AttributeChangedResponse(Message):
    msg_type = 0xA1


def decode(data: bytes) -> Message:
    """Decodes a bytes object into proper message object - raises BufferError if data buffer is too short.
    Returns None if unknown message type"""

    message_type = data[0]
    length, = struct.unpack(">H", data[1:3])
    if len(data) < length:
        raise BufferError("Buffer too short for message")
    if message_type == Heartbeat.msg_type:
        return Heartbeat.decode(data[3:])
    if message_type == HeartbeatResponse.msg_type:
        return HeartbeatResponse.decode(data[3:])
    if message_type == NackResponse.msg_type:
        return NackResponse.decode(data[3:])
    if message_type == SetAttribute.msg_type:
        return SetAttribute.decode(data[3:])
    if message_type == SetAttributeResponse.msg_type:
        return SetAttributeResponse.decode(data[3:])
    if message_type == GetAttribute.msg_type:
        return GetAttribute.decode(data[3:])
    if message_type == GetAttributeResponse.msg_type:
        return GetAttributeResponse.decode(data[3:])
    if message_type == ResetAttribute.msg_type:
        return ResetAttribute.decode(data[3:])
    if message_type == ResetAttributeResponse.msg_type:
        return ResetAttributeResponse.decode(data[3:])
    if message_type == ConfigureReporting.msg_type:
        return ConfigureReporting.decode(data[3:])
    if message_type == ConfigureReportingResponse.msg_type:
        return ConfigureReportingResponse.decode(data[3:])
    if message_type == ResetReporting.msg_type:
        return ResetReporting.decode(data[3:])
    if message_type == ResetReportingResponse.msg_type:
        return ResetReportingResponse.decode(data[3:])
    if message_type == PeriodicRecording.msg_type:
        return PeriodicRecording.decode(data[3:])
    if message_type == PeriodicRecordingResponse.msg_type:
        return PeriodicRecordingResponse.decode(data[3:])
    if message_type == AttributeChanged.msg_type:
        return AttributeChanged.decode(data[3:])
    if message_type == AttributeChangedResponse.msg_type:
        return AttributeChangedResponse.decode(data[3:])
    return None

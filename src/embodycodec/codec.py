"""Codec for the EmBody device
A full embodycodec for the protocol specified for the EmBody device

All protocol message types inherits from the Message class, and provides self-contained encoding and decoding of
messages.
"""

from abc import ABC
import struct
from dataclasses import dataclass, astuple
from typing import List
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

    length = None
    """Length of entire message (header + body + crc). length is dynamically set"""

    @classmethod
    def __body_length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls, data: bytes):
        """Decode bytes into message object"""
        pos = 2 # offset to start of body (skips length field)
        msg = cls(*(struct.unpack(cls.struct_format, data[pos:pos+cls.__body_length()])))
        msg.crc, = struct.unpack(">H", data[pos+cls.__body_length():])
        msg.length, = struct.unpack(">H", data[0:pos])
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
        pos = 2 # offset to start of body (skips length field)
        attribute_id, = struct.unpack(">B", data[pos:pos+1])
        attrib_len, = struct.unpack(">B", data[pos+1:pos+2])
        value = decode_attribute(attribute_id, data[pos+2:pos+2+attrib_len])
        msg = SetAttribute(attribute_id=attribute_id, value=value)
        msg.length, = struct.unpack(">H", data[0:pos])
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
        pos = 2 # offset to start of body (skips length field)
        attribute_id, = struct.unpack(">B", data[pos+0:pos+1])
        changed_at, = struct.unpack(">Q", data[pos+1:pos+9])
        reporting = Reporting.decode(data[pos+9:pos+9+Reporting.length()])
        length, =  struct.unpack(">B", data[pos+9+Reporting.length():pos+9+Reporting.length()+1])
        value = decode_attribute(attribute_id, data[pos+9+Reporting.length()+1:])
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
        pos = 2 # offset to start of body (skips length field)
        attribute_id, = struct.unpack(">B", data[pos+0:pos+1])
        reporting = Reporting.decode(data[pos+1:pos+1+Reporting.length()])
        msg = ConfigureReporting(attribute_id=attribute_id, reporting=reporting)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">B", self.attribute_id)
        reporting_part = self.reporting.encode()
        return first_part_of_body + reporting_part


@dataclass
class ConfigureReportingResponse(Message):
    msg_type = 0x94

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        msg = ConfigureReportingResponse()
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg


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
        pos = 2 # offset to start of body (skips length field)
        recording = Recording.decode(data[pos+0:pos+Recording.length()])
        msg = PeriodicRecording(recording=recording)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        return self.recording.encode()


@dataclass
class PeriodicRecordingResponse(Message):
    msg_type = 0x96


@dataclass
class AttributeChanged(Message):
    msg_type = 0x21
    changed_at: int
    attribute_id: int
    value: Attribute

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        changed_at, = struct.unpack(">Q", data[pos+0:pos+8])
        attribute_id, = struct.unpack(">B", data[pos+8:pos+9])
        value = decode_attribute(attribute_id, data[pos+10:])
        msg = AttributeChanged(changed_at=changed_at, attribute_id=attribute_id, value=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">QB", self.changed_at, self.attribute_id)
        length_part = struct.pack(">B", self.value.length())
        attribute_part = self.value.encode()
        return first_part_of_body + length_part + attribute_part


@dataclass
class AttributeChangedResponse(Message):
    msg_type = 0xA1


@dataclass
class RawPulseChanged(Message):
    msg_type = 0x22
    changed_at: int
    value: PulseRaw

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        changed_at, = struct.unpack(">H", data[pos+0:pos+2])
        value = PulseRaw.decode(data[pos+2:])
        msg = RawPulseChanged(changed_at=changed_at, value=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">H", self.changed_at)
        raw_pulse_part = self.value.encode()
        return first_part_of_body + raw_pulse_part


@dataclass
class RawPulseChangedResponse(Message):
    msg_type = 0xA2


@dataclass
class Alarm(Message):
    struct_format = ">QB"
    alarm_types = {0x01: 'Low battery', 0x02: 'Device off body', 0x03: 'Device error'}
    msg_type = 0x31
    changed_at: int
    alarm_type: int

    def alarm_message(self) -> str:
        if self.alarm_type is None:
            return None
        return self.alarm_types.get(self.alarm_type)


@dataclass
class AlarmResponse(Message):
    msg_type = 0xB1


@dataclass
class ListFiles(Message):
    msg_type = 0x41


@dataclass
class ListFilesResponse(Message):
    struct_format = ">26cI"
    msg_type = 0xC1
    files: List[FileWithLength]

    @classmethod
    def decode(cls, data: bytes):
        # ListFiles length
        msg = ListFilesResponse(files=[])
        msg.length, = struct.unpack(">H", data[0:2])

        if msg.length > 5:
            pos = 2
            while pos + FileWithLength.length() <= msg.length - 1:
                msg.files.append(FileWithLength.decode(data[pos:pos + FileWithLength.length()]))
                pos += FileWithLength.length()
        return msg

    def _encode_body(self) -> bytes:
        body = b''
        if self.files is None or len(self.files) == 0:
            return b''
        for file in self.files:
            body += file.encode()
        return body


@dataclass
class GetFile(Message):
    msg_type = 0x42
    file: File

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        value = File.decode(data[pos:])
        msg = GetFile(file=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        return self.file.encode()


@dataclass
class GetFileResponse(Message):
    msg_type = 0xC2


@dataclass
class SendFile(Message):
    msg_type = 0x43
    file_name: File
    index: int
    total_parts: int
    payload: bytes

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        file_name = File.decode(data[pos:])
        index, = struct.unpack(">H", data[pos+File.length():pos+File.length()+2])
        total_parts, = struct.unpack(">H", data[pos+File.length()+2:pos+File.length()+4])
        payload = data[pos+File.length()+4:len(data)-2]
        msg = SendFile(file_name=file_name, index=index, total_parts=total_parts, payload=payload)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        body = self.file_name.encode()
        body += struct.pack(">H", self.index)
        body += struct.pack(">H", self.total_parts)
        body += self.payload
        return body


@dataclass
class SendFileResponse(Message):
    struct_format = ">H"
    msg_type = 0xC3
    crc: int


@dataclass
class DeleteFile(Message):
    msg_type = 0x44
    file: File

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        value = File.decode(data[pos:])
        msg = DeleteFile(file=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        return self.file.encode()


@dataclass
class DeleteFileResponse(Message):
    msg_type = 0xC4


@dataclass
class GetFileUart(Message):
    msg_type = 0x45
    file: File

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        value = File.decode(data[pos:])
        msg = GetFileUart(file=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        return self.file.encode()


@dataclass
class GetFileUartResponse(Message):
    msg_type = 0xC5


@dataclass
class DeleteAllFiles(Message):
    msg_type = 0x46


@dataclass
class DeleteAllFilesResponse(Message):
    msg_type = 0xC6


@dataclass
class ReformatDisk(Message):
    msg_type = 0x47


@dataclass
class ReformatDiskResponse(Message):
    msg_type = 0xC7


@dataclass
class ExecuteCommand(Message):
    RESET_DEVICE = 0x01
    REBOOT_DEVICE = 0x02
    command_types = {0x01: 'Reset device', 0x02: 'Reboot device', 0xA1: 'AFE: Read all registers',
                     0xA2: 'AFE: Write register <Addr (1 byte)><Value (4 bytes)>',
                     0xA3: 'AFE: Calibration command <Cmd (1 byte))', 0xA4: 'AFE: Gain setting <Cmd (1 byte)'}
    msg_type = 0x51
    command_id: int
    value: None

    def command_message(self) -> str:
        if self.command_id is None:
            return None
        return self.command_types.get(self.alarm_type)

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        command_id, = struct.unpack(">B", data[pos+0:pos+1])
        value = decode_executive_command_response(command_id, data[pos+1:])
        msg = ExecuteCommand(command_id=command_id, value=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        if self.command_id == ExecuteCommandType.AFE_CALIBRATION_COMMAND.value:
            attribute_part = struct.pack(">B", self.command_id)
            value_part = struct.pack(">B", self.value)
            return attribute_part + value_part

        if self.command_id == ExecuteCommandType.AFE_GAIN_SETTING.value:
            attribute_part = struct.pack(">B", self.command_id)
            value_part = struct.pack(">B", self.value)
            return attribute_part + value_part

        if self.command_id == ExecuteCommandType.AFE_WRITE_REGISTER.value:
            attribute_part = struct.pack(">B", self.command_id)
            address_part = struct.pack(">B", self.value[0])
            value_part = struct.pack(">I", self.value[1])
            return attribute_part + address_part + value_part

        attribute_part = struct.pack(">B", self.command_id)
        return attribute_part


@dataclass
class ExecuteCommandResponse(Message):
    msg_type = 0xD1
    response_code: int
    value: None

    @classmethod
    def decode(cls, data: bytes):
        pos = 2 # offset to start of body (skips length field)
        response_code, = struct.unpack(">B", data[pos+0:pos+1])
        value = decode_executive_command_response(response_code, data[pos+1:])
        msg = ExecuteCommandResponse(response_code=response_code, value=value)
        msg.length, = struct.unpack(">H", data[0:pos])
        return msg

    def _encode_body(self) -> bytes:
        if self.response_code == ExecuteCommandType.AFE_READ_ALL_REGISTERS.value:
            attribute_part = struct.pack(">B", self.response_code)
            address_part = struct.pack(">B", self.value[0])
            value_part = struct.pack(">I", self.value[1])
            return attribute_part + address_part + value_part
        
        attribute_part = struct.pack(">B", self.response_code)
        return attribute_part


def decode(data: bytes) -> Message:
    """Decodes a bytes object into proper message object - raises BufferError if data buffer is too short.
    Returns None if unknown message type"""

    message_type = data[0]
    length, = struct.unpack(">H", data[1:3])
    if len(data) < length:
        raise BufferError(f"Buffer too short for message: Received {len(data)} bytes, expected {length} bytes")
    if message_type == Heartbeat.msg_type:
        return Heartbeat.decode(data[1:])
    if message_type == HeartbeatResponse.msg_type:
        return HeartbeatResponse.decode(data[1:])
    if message_type == NackResponse.msg_type:
        return NackResponse.decode(data[1:])
    if message_type == SetAttribute.msg_type:
        return SetAttribute.decode(data[1:])
    if message_type == SetAttributeResponse.msg_type:
        return SetAttributeResponse.decode(data[1:])
    if message_type == GetAttribute.msg_type:
        return GetAttribute.decode(data[1:])
    if message_type == GetAttributeResponse.msg_type:
        return GetAttributeResponse.decode(data[1:])
    if message_type == ResetAttribute.msg_type:
        return ResetAttribute.decode(data[1:])
    if message_type == ResetAttributeResponse.msg_type:
        return ResetAttributeResponse.decode(data[1:])
    if message_type == ConfigureReporting.msg_type:
        return ConfigureReporting.decode(data[1:])
    if message_type == ConfigureReportingResponse.msg_type:
        return ConfigureReportingResponse.decode(data[1:])
    if message_type == ResetReporting.msg_type:
        return ResetReporting.decode(data[1:])
    if message_type == ResetReportingResponse.msg_type:
        return ResetReportingResponse.decode(data[1:])
    if message_type == PeriodicRecording.msg_type:
        return PeriodicRecording.decode(data[1:])
    if message_type == PeriodicRecordingResponse.msg_type:
        return PeriodicRecordingResponse.decode(data[1:])
    if message_type == AttributeChanged.msg_type:
        return AttributeChanged.decode(data[1:])
    if message_type == AttributeChangedResponse.msg_type:
        return AttributeChangedResponse.decode(data[1:])
    if message_type == RawPulseChanged.msg_type:
        return RawPulseChanged.decode(data[1:])
    if message_type == RawPulseChangedResponse.msg_type:
        return RawPulseChangedResponse.decode(data[1:])
    if message_type == Alarm.msg_type:
        return Alarm.decode(data[1:])
    if message_type == AlarmResponse.msg_type:
        return AlarmResponse.decode(data[1:])
    if message_type == ListFiles.msg_type:
        return ListFiles.decode(data[1:])
    if message_type == ListFilesResponse.msg_type:
        return ListFilesResponse.decode(data[1:])
    if message_type == GetFile.msg_type:
        return GetFile.decode(data[1:])
    if message_type == GetFileResponse.msg_type:
        return GetFileResponse.decode(data[1:])
    if message_type == SendFile.msg_type:
        return SendFile.decode(data[1:])
    if message_type == SendFileResponse.msg_type:
        return SendFileResponse.decode(data[1:])
    if message_type == DeleteFile.msg_type:
        return DeleteFile.decode(data[1:])
    if message_type == DeleteFileResponse.msg_type:
        return DeleteFileResponse.decode(data[1:])
    if message_type == GetFileUart.msg_type:
        return GetFileUart.decode(data[1:])
    if message_type == GetFileUartResponse.msg_type:
        return GetFileUartResponse.decode(data[1:])
    if message_type == ReformatDisk.msg_type:
        return ReformatDisk.decode(data[1:])
    if message_type == ReformatDiskResponse.msg_type:
        return ReformatDiskResponse.decode(data[1:])
    if message_type == ExecuteCommand.msg_type:
        return ExecuteCommand.decode(data[1:])
    if message_type == ExecuteCommandResponse.msg_type:
        return ExecuteCommandResponse.decode(data[1:])
    return None

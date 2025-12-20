"""Codec for the EmBody device.

A full embodycodec for the protocol specified for the EmBody device

All protocol message types inherits from the Message class, and provides self-contained encoding and decoding of
messages.

This module uses a dictionary-based registry pattern (_MESSAGE_REGISTRY) for O(1) message type lookups,
providing significant performance improvements over linear searches.
"""

import struct
from abc import ABC
from dataclasses import astuple
from dataclasses import dataclass
from typing import TypeVar

from embodycodec import attributes as a
from embodycodec import types as t
from embodycodec.crc import crc16
from embodycodec.exceptions import CrcError
from embodycodec.exceptions import DecodeError


T = TypeVar("T", bound="Message")
AT = TypeVar("AT", bound="a.Attribute")


@dataclass
class Message(ABC):
    """Abstract base class for protocol messages"""

    hdr_len = 3
    """Header length to avoid checking every time"""

    crc_len = 2
    """CRC length to avoid magic numbers"""

    struct_hdr_format = ">BH"
    """unpack format that is fixed for all headers, taking up hdr_len bytes"""

    struct_format = ""
    """unpack format to be overridden by sub-classes, see
    https://docs.python.org/3/library/struct.html#format-characters
    does not include header (type and length field) or footer (crc)"""

    msg_type = -1
    """Protocol type field - must be set by subclasses"""

    crc = -1
    """crc footer is dynamically set"""

    length = -1
    """Length of entire message (header + body + crc). length is dynamically set"""

    @classmethod
    def __body_length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def _check_crc_and_get_metadata(cls, data: bytes, accept_crc_error: bool = False) -> tuple[int, int]:
        if len(data) < cls.hdr_len:
            # Note: This is not technically an error as more data may arrive allowing the message to be decoded,
            # but raised as error to split it from the resulting length found in the process of checking crc
            raise BufferError(
                f"Buffer too short for header in type {data[0]:02X}: Received {len(data)} bytes, required {cls.hdr_len} bytes"
            )
        (
            data_type,
            data_length,
        ) = struct.unpack(cls.struct_hdr_format, data[0 : cls.hdr_len])
        if len(data) < data_length:
            # Note: This is not technically an error as more data may arrive allowing the message to be decoded,
            # but raised as error to split it from the resulting length found in the process of checking crc
            raise BufferError(
                f"Buffer too short for message type {data_type:02X}: Received {len(data)} bytes, expected {data_length} bytes"
            )
        (crc,) = struct.unpack(">H", data[data_length - 2 : data_length])
        calculated_crc = crc16(data[0 : data_length - 2])
        if crc != calculated_crc and not accept_crc_error:
            raise CrcError(f"CRC error: Calculated {calculated_crc:04X}, received {crc:04X}")
        return crc, data_length

    @classmethod
    def decode(cls: type[T], data: bytes, accept_crc_error: bool = False) -> T:
        """Decode bytes into message object"""
        (crc, length) = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        msg = cls(*(struct.unpack(cls.struct_format, data[pos : pos + cls.__body_length()])))
        msg.crc = crc
        msg.length = length
        return msg

    # Note: Default method encodes dataclass with fixed length and format
    def encode(self) -> bytes:
        """Encode a message object to bytes"""
        body = self._encode_body()
        header = self._encode_header(body)
        header_and_body = header + body
        return header_and_body + self._encode_crc(header_and_body)

    def _encode_body(self) -> bytes:
        return struct.pack(self.struct_format, *astuple(self))

    def _encode_crc(self, header_and_body: bytes) -> bytes:
        crc_calculated = crc16(header_and_body)
        crc = struct.pack(">H", crc_calculated)
        return crc

    def _encode_header(self, body: bytes) -> bytes:
        return struct.pack(
            self.struct_hdr_format,
            self.msg_type,
            len(body) + self.hdr_len + self.crc_len,
        )

    @classmethod
    def get_meta(cls, data: bytes) -> tuple[int, int]:
        if len(data) < cls.hdr_len:
            # raised as error to allow more bufring
            raise BufferError(
                f"Buffer too short for message: Received {len(data)} bytes, Metadata requires at least {Message.hdr_len} bytes!"
            )
        (
            data_type,
            data_length,
        ) = struct.unpack(cls.struct_hdr_format, data[0 : cls.hdr_len])
        return data_type, data_length


@dataclass
class Heartbeat(Message):
    msg_type = 0x01


@dataclass
class HeartbeatResponse(Message):
    msg_type = 0x81


@dataclass
class NackResponse(Message):
    struct_format = ">B"
    error_messages = {
        0x01: "Unknown message type",
        0x02: "Unknown message content",
        0x03: "Unknown attribute",
        0x04: "Message too short",
        0x05: "Message too long",
        0x06: "Message with illegal CRC",
        0x07: "Message buffer full",
        0x08: "File system error",
        0x09: "Delete file error",
        0x0A: "File not found",
        0x0B: "Retransmit failed",
        0x0C: "File not opened",
    }
    msg_type = 0x82
    response_code: int

    def error_message(self) -> str | None:
        return self.error_messages.get(self.response_code)


@dataclass
class SetAttribute(Message):
    msg_type = 0x11
    attribute_id: int
    value: a.Attribute

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "SetAttribute":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (
            attribute_id,
            attrib_len,
        ) = struct.unpack(">BB", data[pos : pos + 2])
        value = a.decode_attribute(attribute_id, data[pos + 2 : pos + 2 + attrib_len])
        msg = SetAttribute(attribute_id=attribute_id, value=value)
        msg.crc = crc
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
    attribute_id: int
    changed_at: int
    reporting: t.Reporting
    value: a.Attribute

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "GetAttributeResponse":
        crc, data_length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (attribute_id,) = struct.unpack(">B", data[pos + 0 : pos + 1])
        (changed_at,) = struct.unpack(">Q", data[pos + 1 : pos + 9])
        reporting = t.Reporting.decode(data[pos + 9 : pos + 9 + t.Reporting.default_length()])
        pos = pos + 9 + t.Reporting.default_length()
        (length,) = struct.unpack(">B", data[pos : pos + 1])
        value = a.decode_attribute(attribute_id, data[pos + 1 : pos + length + 1])
        msg = GetAttributeResponse(
            attribute_id=attribute_id,
            changed_at=changed_at,
            reporting=reporting,
            value=value,
        )
        msg.crc = crc
        msg.length = data_length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">BQ", self.attribute_id, self.changed_at)
        reporting_part = self.reporting.encode()
        attribute_part = self.value.encode()
        length_part = struct.pack(">B", len(attribute_part))
        return first_part_of_body + reporting_part + length_part + attribute_part

    def value_as(self, attr_type: type[AT]) -> AT:
        """Type-safe accessor for the attribute value with runtime type checking."""
        if not isinstance(self.value, attr_type):
            raise TypeError(f"Expected {attr_type.__name__}, got {type(self.value).__name__}")
        return self.value


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
    reporting: t.Reporting

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "ConfigureReporting":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (attribute_id,) = struct.unpack(">B", data[pos + 0 : pos + 1])
        reporting = t.Reporting.decode(data[pos + 1 : pos + 1 + t.Reporting.default_length()])
        msg = ConfigureReporting(attribute_id=attribute_id, reporting=reporting)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">B", self.attribute_id)
        reporting_part = self.reporting.encode()
        return first_part_of_body + reporting_part


@dataclass
class ConfigureReportingResponse(Message):
    msg_type = 0x94

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "ConfigureReportingResponse":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        msg = ConfigureReportingResponse()
        msg.crc = crc
        msg.length = length
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
    recording: t.Recording

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "PeriodicRecording":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        recording = t.Recording.decode(data[pos + 0 : pos + t.Recording.default_length()])
        msg = PeriodicRecording(recording=recording)
        msg.crc = crc
        msg.length = length
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
    value: a.Attribute

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "AttributeChanged":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (changed_at,) = struct.unpack(">Q", data[pos + 0 : pos + 8])
        (attribute_id,) = struct.unpack(">B", data[pos + 8 : pos + 9])
        (attr_length,) = struct.unpack(">B", data[pos + 9 : pos + 10])
        value = a.decode_attribute(attribute_id, data[pos + 10 : pos + 10 + attr_length])
        msg = AttributeChanged(changed_at=changed_at, attribute_id=attribute_id, value=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">QB", self.changed_at, self.attribute_id)
        attribute_part = self.value.encode()
        length_part = struct.pack(">B", len(attribute_part))
        return first_part_of_body + length_part + attribute_part


@dataclass
class AttributeChangedResponse(Message):
    msg_type = 0xA1


@dataclass
class RawPulseChanged(Message):
    msg_type = 0x22
    changed_at: int
    value: t.PulseRawAll | t.PulseRaw

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "RawPulseChanged":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        header_crc = 7  # attrib_id (1B) + length (2B) + changed_at (2B) + crc (2B)
        (changed_at,) = struct.unpack(">H", data[pos + 0 : pos + 2])
        # Determine if payload contains 1 or 3 PPGs
        if length - header_crc == t.PulseRawAll.default_length():
            value = t.PulseRawAll.decode(data[pos + 2 :])  # type: Union[t.PulseRawAll, t.PulseRaw]
        else:
            value = t.PulseRaw.decode(data[pos + 2 :])
        msg = RawPulseChanged(changed_at=changed_at, value=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">H", self.changed_at)
        raw_pulse_part = self.value.encode()
        return first_part_of_body + raw_pulse_part


@dataclass
class RawPulseChangedResponse(Message):
    msg_type = 0xA2


@dataclass
class RawPulseListChanged(Message):
    msg_type = 0x24
    attribute_id: int
    value: a.PulseRawListAttribute

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "RawPulseListChanged":
        (crc, length) = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (attribute_id,) = struct.unpack(">B", data[pos : pos + 1])
        value = a.PulseRawListAttribute.decode(data[pos + 1 :])
        msg = RawPulseListChanged(attribute_id=attribute_id, value=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        first_part_of_body = struct.pack(">B", self.attribute_id)
        raw_pulse_part = self.value.encode()
        return first_part_of_body + raw_pulse_part


@dataclass
class RawPulseListChangedResponse(Message):
    msg_type = 0xA4


@dataclass
class Alarm(Message):
    struct_format = ">QB"
    alarm_types = {0x01: "Low battery", 0x02: "Device off body", 0x03: "Device error"}
    msg_type = 0x31
    changed_at: int | None
    alarm_type: int | None

    def alarm_message(self) -> str | None:
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
    files: list[t.FileWithLength]

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "ListFilesResponse":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        # ListFiles length
        msg = ListFilesResponse(files=[])
        msg.crc = crc
        msg.length = length

        if msg.length > 5:
            while pos + t.FileWithLength.default_length() <= msg.length - 1:
                msg.files.append(t.FileWithLength.decode(data[pos : pos + t.FileWithLength.default_length()]))
                pos += t.FileWithLength.default_length()
        return msg

    def _encode_body(self) -> bytes:
        body = b""
        if self.files is None or len(self.files) == 0:
            return b""
        for file in self.files:
            body += file.encode()
        return body


@dataclass
class FileDataChunk(Message):
    struct_format = "<BI"
    """Format of new package uses little endian inside for maximum speed of transfer at device side"""
    msg_type = 0xCA
    fileref: int = 0
    """Used to identify to the host which file the chunk belongs to. Taken from the send command as supplied by host"""
    offset: int = 0
    file_data: bytes = b""

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "FileDataChunk":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        msg = FileDataChunk()
        # fileref and offset
        (
            msg.fileref,
            msg.offset,
        ) = struct.unpack(cls.struct_format, data[pos : pos + 1 + 4])
        msg.file_data = bytes(data[pos + 1 + 4 : length - cls.crc_len])
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        data_hdr = struct.pack(self.struct_format, self.fileref, self.offset)
        return data_hdr + self.file_data


@dataclass
class GetFile(Message):
    msg_type = 0x42
    file: t.File

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "GetFile":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        value = t.File.decode(data[pos:])
        msg = GetFile(file=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        return self.file.encode()


@dataclass
class GetFileResponse(Message):
    msg_type = 0xC2


@dataclass
class SendFile(Message):
    msg_type = 0x43
    file_name: t.File
    index: int
    total_parts: int
    payload: bytes

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "SendFile":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        file_name = t.File.decode(data[pos:])
        (index,) = struct.unpack(
            ">H",
            data[pos + t.File.default_length() : pos + t.File.default_length() + 2],
        )
        (total_parts,) = struct.unpack(
            ">H",
            data[pos + t.File.default_length() + 2 : pos + t.File.default_length() + 4],
        )
        payload = data[pos + t.File.default_length() + 4 : len(data) - 2]
        msg = SendFile(file_name=file_name, index=index, total_parts=total_parts, payload=payload)
        msg.crc = crc
        msg.length = length
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
    file: t.File

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "DeleteFile":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        value = t.File.decode(data[pos:])
        msg = DeleteFile(file=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        return self.file.encode()


@dataclass
class DeleteFileResponse(Message):
    msg_type = 0xC4


@dataclass
class GetFileUart(Message):
    msg_type = 0x45
    file: t.File

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "GetFileUart":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        value = t.File.decode(data[pos:])
        msg = GetFileUart(file=value)
        msg.crc = crc
        msg.length = length
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
    command_types = {
        0x01: "Reset device",
        0x02: "Reboot device",
        0x03: "Press button <press count (1 byte)><press duration in ms (2 bytes)>",
        0x04: "On Body: <Force Off (0) | Force On (1) | Force Disable (255) (1 byte)>",
        0x05: "USB Connection: <Force Off (0) | Force On (1) | Force Disable (0xFF) (1 byte)>",
        0x06: "BLE Connection: <Force Off (0) | Force On (1) | Force Disable (0xFF) (1 byte)>",
        0x07: "Battery level: <Force value | Force Disable (0xFF) (1 byte)>",
        0x08: "Reinit Service: <Service (1 byte)><Parameter (4 bytes/int)) 0x00000000>",
        0xA1: "AFE: Read all registers",
        0xA2: "AFE: Write register <Addr (1 byte)><Value (4 bytes)>",
        0xA3: "AFE: Calibration command <Cmd (1 byte))",
        0xA4: "AFE: Gain setting <Cmd (1 byte)",
    }
    msg_type = 0x51
    command_id: int
    value: bytes | int | None

    def command_message(self) -> str | None:
        return self.command_types.get(self.command_id)

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "ExecuteCommand":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (command_id,) = struct.unpack(">B", data[pos + 0 : pos + 1])
        # Extract only the payload bytes after command_id, excluding CRC
        value = data[pos + 1 : length - cls.crc_len] if length > pos + 1 + cls.crc_len else b""
        msg = ExecuteCommand(command_id=command_id, value=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        if self.command_id == t.ExecuteCommandType.PRESS_BUTTON.value:
            attribute_part = struct.pack(">B", self.command_id)
            return attribute_part + (self.value if isinstance(self.value, bytes) else b"")

        if self.command_id == t.ExecuteCommandType.FORCE_ON_BODY.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">B", self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">B", self.value)
            else:
                value_part = b"\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.FORCE_USB_CONNECTION.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">B", self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">B", self.value)
            else:
                value_part = b"\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.FORCE_BLE_CONNECTION.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">B", self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">B", self.value)
            else:
                value_part = b"\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.FORCE_BATTERY_LEVEL.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">B", self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">B", self.value)
            else:
                value_part = b"\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.REINIT_SERVICE.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">BBBB", self.value[3], self.value[2], self.value[1], self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">I", self.value)
            else:
                value_part = b"\x00\x00\x00\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.AFE_CALIBRATION_COMMAND.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">B", self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">B", self.value)
            else:
                value_part = b"\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.AFE_GAIN_SETTING.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) > 0:
                value_part = struct.pack(">B", self.value[0])
            elif isinstance(self.value, int):
                value_part = struct.pack(">B", self.value)
            else:
                value_part = b"\x00"
            return attribute_part + value_part

        if self.command_id == t.ExecuteCommandType.AFE_WRITE_REGISTER.value:
            attribute_part = struct.pack(">B", self.command_id)
            if isinstance(self.value, bytes) and len(self.value) >= 5:
                address_part = struct.pack(">B", self.value[0])
                value_part = struct.pack(">I", int.from_bytes(self.value[1:5], byteorder="big"))
                return attribute_part + address_part + value_part
            data_len = len(self.value) if isinstance(self.value, bytes) else 0
            raise ValueError(f"AFE_WRITE_REGISTER requires 5 bytes of data, got {data_len}")

        attribute_part = struct.pack(">B", self.command_id)
        return attribute_part


@dataclass
class ExecuteCommandResponse(Message):
    msg_type = 0xD1
    response_code: int
    value: bytes | None

    @classmethod
    def decode(cls, data: bytes, accept_crc_error: bool = False) -> "ExecuteCommandResponse":
        crc, length = cls._check_crc_and_get_metadata(data, accept_crc_error)
        pos = cls.hdr_len  # offset to start of body (skips msg_type and length field)
        (response_code,) = struct.unpack(">B", data[pos + 0 : pos + 1])
        # Extract only the payload bytes after response_code, excluding CRC
        value = data[pos + 1 : length - cls.crc_len] if length > pos + 1 + cls.crc_len else b""
        msg = ExecuteCommandResponse(response_code=response_code, value=value)
        msg.crc = crc
        msg.length = length
        return msg

    def _encode_body(self) -> bytes:
        if self.response_code == t.ExecuteCommandType.AFE_READ_ALL_REGISTERS.value:
            attribute_part = struct.pack(">B", self.response_code)
            if isinstance(self.value, bytes) and len(self.value) >= 5:
                address_part = struct.pack(">B", self.value[0])
                value_part = struct.pack(">I", int.from_bytes(self.value[1:5], byteorder="big"))
                return attribute_part + address_part + value_part
            return attribute_part

        attribute_part = struct.pack(">B", self.response_code)
        return attribute_part


# Message type registry for efficient O(1) lookup
_MESSAGE_REGISTRY: dict[int, type[Message]] = {
    0x01: Heartbeat,
    0x81: HeartbeatResponse,
    0x82: NackResponse,
    0x11: SetAttribute,
    0x91: SetAttributeResponse,
    0x12: GetAttribute,
    0x92: GetAttributeResponse,
    0x13: ResetAttribute,
    0x93: ResetAttributeResponse,
    0x14: ConfigureReporting,
    0x94: ConfigureReportingResponse,
    0x15: ResetReporting,
    0x95: ResetReportingResponse,
    0x16: PeriodicRecording,
    0x96: PeriodicRecordingResponse,
    0x21: AttributeChanged,
    0xA1: AttributeChangedResponse,
    0x22: RawPulseChanged,
    0xA2: RawPulseChangedResponse,
    0x24: RawPulseListChanged,
    0xA4: RawPulseListChangedResponse,
    0x31: Alarm,
    0xB1: AlarmResponse,
    0x41: ListFiles,
    0xC1: ListFilesResponse,
    0x42: GetFile,
    0xC2: GetFileResponse,
    0xCA: FileDataChunk,
    0x43: SendFile,
    0xC3: SendFileResponse,
    0x44: DeleteFile,
    0xC4: DeleteFileResponse,
    0x45: GetFileUart,
    0xC5: GetFileUartResponse,
    0x46: DeleteAllFiles,
    0xC6: DeleteAllFilesResponse,
    0x47: ReformatDisk,
    0xC7: ReformatDiskResponse,
    0x51: ExecuteCommand,
    0xD1: ExecuteCommandResponse,
}


def decode(data: bytes, accept_crc_error: bool = False) -> Message:
    """Decodes a bytes object into proper message object.

    raises BufferError if data buffer is too short.
    raises DecodeError if error decoding message.
    raises LookupError if unknown message type.
    raises CrcError if checksum fails.
    """
    if not data:
        raise BufferError("No data provided!")

    # Get metadata
    (
        message_type,
        length,
    ) = Message.get_meta(data)
    # Since we trim the data to catch any erronous decoding not matching packet length we must have enough data
    if len(data) < length:
        raise BufferError(
            f"Buffer too short for decoding type 0x{data[0]:02X}: Received {len(data)} bytes, required {length} bytes"
        )
    # Prepare the data by trimming off any additional data not part of packet
    trimmed_data = data[0:length]

    # Lookup message class from registry
    message_class = _MESSAGE_REGISTRY.get(message_type)
    if message_class is None:
        raise LookupError(f"Unknown message type {hex(message_type)}")

    try:
        return message_class.decode(trimmed_data, accept_crc_error)
    except BufferError as e:
        raise e
    except CrcError as e:
        raise e
    except Exception as e:
        hexdump = data.hex() if len(data) <= 1024 else f"{data[0:1024].hex()}..."
        raise DecodeError(f"Error decoding message type {hex(message_type)}. Message payload: {hexdump}") from e

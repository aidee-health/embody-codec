"""File Codec for the Aidee EmBody device.

This class separates out the parsing of different message types from the EmBody device's file format. The first part
consists of all the different messages wrapped as subclasses of the ProtocolMessage dataclass. The bottom part
provides access methods for parsing one and one message from a bytes object.

This module uses a dictionary-based registry pattern (ProtocolMessage.subclasses) for O(1) message type lookups.
Temperature conversions use the TEMPERATURE_SCALE_FACTOR constant (0.0078125 = 1/128).
"""

from __future__ import annotations

import struct
from dataclasses import astuple
from dataclasses import dataclass
from dataclasses import field
from typing import ClassVar
from embodycodec.exceptions import DecodeError

# Temperature sensor conversion factor (degrees Celsius per raw unit)
# This factor converts raw sensor values to degrees Celsius
TEMPERATURE_SCALE_FACTOR = 0.0078125  # 1/128


@dataclass
class ProtocolMessage:
    # unpack format to be overridden by sub-classes, see https://docs.python.org/3/library/struct.html#format-characters
    unpack_format: ClassVar[str] = ""

    registry: ClassVar[dict[int, type[ProtocolMessage]]] = {}
    message_id: ClassVar[int | None] = None  # Safe sentinel

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Only register concrete classes that have a valid ID assigned
        if cls.message_id is not None:
            ProtocolMessage.registry[cls.message_id] = cls

    @classmethod
    def get_header_size(cls) -> int:
        """Minimum bytes needed to calculate the total packet size."""
        # Default: 1 (ID)
        return 1

    @classmethod
    def get_expected_length(cls, header_data: bytes) -> int:
        """
        Calculates total length based on header peeking.
        header_data starts at the Timestamp (ID is already stripped).
        """
        # Default for fixed-length messages
        return 1 + 2 + struct.calcsize(cls.payload_format)

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        return cls(*(struct.unpack(cls.unpack_format, data[0 : cls.default_length(version)])))


@dataclass
class TimetickedMessage(ProtocolMessage):
    # This class still has message_id = None, so it won't be registered
    unpack_format: ClassVar[str] = ">H"

    # None is the safe sentinel for 'not yet decoded'
    two_lsb_of_timestamp: int | None = field(init=False, default=None)

    @classmethod
    def decode(cls, data: bytes) -> TimetickedMessage:
        timestamp = struct.unpack(">H", data[:2])[0]
        return cls._decode_payload(timestamp, data[2:])

    def encode(self) -> bytes:
        header = struct.pack(">H", self.two_lsb_of_timestamp)
        return header + self._encode_payload()


@dataclass
@ProtocolMessage.register(0x01)
class Header(ProtocolMessage):
    unpack_format = ">Qc3scQ"
    serial: int
    fw_att: bytes
    firmware_version: bytes
    time_att: bytes
    current_time: int


@dataclass
@ProtocolMessage.register(0x71)
class Timestamp(TimetickedMessage):
    payload_format = ">Q"
    current_time: int


def flatten_deep(arbitrary_list):
    for item in arbitrary_list:
        if isinstance(item, list):
            yield from flatten_deep(item)
        else:
            yield item


@dataclass
class AfeSettingsOld(TimetickedMessage):
    payload_format = ">bbbdddd"
    rf_gain: int
    cf_values: int
    ecg_gain: int
    i_led: list[int]
    ioff_dac_led: float
    ioff_dac_amb: float

    def encode(self) -> bytes:
        return struct.pack(self.unpack_format, *flatten_deep([*astuple(self)]))

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.unpack_format, data)
        return AfeSettingsOld(raw[0], raw[1], raw[2], raw[3], [*raw[4:6]], raw[6], raw[7])


@dataclass
class AfeSettings(TimetickedMessage):
    payload_format = ">BBBBIIif"
    rf_gain: int
    cf_value: int
    ecg_gain: int
    ioffdac_range: int
    i_led: list[int]
    off_dac: list[int]
    relative_gain: float

    def encode(self) -> bytes:
        return struct.pack(self.unpack_format, *flatten_deep([*astuple(self)]))

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.unpack_format, data)
        return AfeSettings(raw[0], raw[1], raw[2], raw[3], raw[4], [*raw[5:7]], [*raw[7:8]], raw[8])


@dataclass
@ProtocolMessage.register(0x07)
class AfeSettingsAll(TimetickedMessage):
    payload_format = ">BBBBIIIIiiif"
    rf_gain: int
    cf_value: int
    ecg_gain: int
    ioffdac_range: int
    i_led: list[int]
    off_dac: list[int]
    relative_gain: float

    subclasses: ClassVar[dict[int, type[AfeSettingsAll]]] = {}

    @classmethod
    def register(cls, key):
        def wrapper(subclass):
            cls.subclasses[key] = subclass
            return subclass

        return wrapper

    def encode(self) -> bytes:
        c = self.subclasses[4 + 4 * len(self.i_led) + 4 * len(self.off_dac) + 4]
        return struct.pack(c.payload_format, *flatten_deep([*astuple(self)]))

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.payload_format, data)
        return AfeSettingsAll(raw[0], raw[1], raw[2], raw[3], raw[4], [*raw[5:9]], [*raw[9:12]], raw[12])


@dataclass
@ProtocolMessage.register(0x09)
class AfeSettings0(TimetickedMessage):
    payload_format = ">BBBBf"

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.payload_format, data)
        return AfeSettings0(raw[0], raw[1], raw[2], raw[3], raw[4], [], [], raw[5])


@dataclass
@ProtocolMessage.register(0x0A)
class AfeSettings1(TimetickedMessage):
    payload_format = ">BBBBIif"

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.payload_format, data)
        return AfeSettings1(raw[0], raw[1], raw[2], raw[3], raw[4], [*raw[5:6]], [*raw[6:7]], raw[7])


@dataclass
@ProtocolMessage.register(0x0B)
class AfeSettings2(TimetickedMessage):
    payload_format = ">BBBBIIiif"

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.payload_format, data)
        return AfeSettings2(raw[0], raw[1], raw[2], raw[3], raw[4], [*raw[5:7]], [*raw[7:9]], raw[9])


@dataclass
@ProtocolMessage.register(0x0C)
class AfeSettings3(TimetickedMessage):
    payload_format = ">BBBBIIIiiif"

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.payload_format, data)
        return AfeSettings3(raw[0], raw[1], raw[2], raw[3], raw[4], [*raw[5:8]], [*raw[8:11]], raw[11])


@dataclass
@ProtocolMessage.register(0x0D)
class AfeSettings4(TimetickedMessage):
    payload_format = ">BBBBIIIIiiiif"

    @classmethod
    def decode(cls, data: bytes):
        raw = struct.unpack(cls.payload_format, data)
        return AfeSettings4(raw[0], raw[1], raw[2], raw[3], raw[4], [*raw[5:9]], [*raw[9:13]], raw[13])


@dataclass
@ProtocolMessage.register(0xB1)
class PpgRaw(TimetickedMessage):
    ecg: int
    ppg: int

    @classmethod
    def default_length(cls, version: tuple[int, int, int] | None = None) -> int:
        return 8

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="big", signed=False)
        ecg = int.from_bytes(data[2:5], byteorder="big", signed=True)
        ppg = int.from_bytes(data[5:8], byteorder="big", signed=True)
        msg = PpgRaw(ts_lsb, ecg, ppg)
        return msg


@dataclass
@ProtocolMessage.register(0xA2)
class PpgRawAll(TimetickedMessage):
    ecg: int
    ppg: int
    ppg_red: int
    ppg_ir: int

    @classmethod
    def default_length(cls, version: tuple[int, int, int] | None = None) -> int:
        return 11

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="big", signed=False)
        ecg = int.from_bytes(data[2:5], byteorder="big", signed=True)
        ppg = int.from_bytes(data[5:8], byteorder="big", signed=True)
        ppg_red = int.from_bytes(data[8:11], byteorder="big", signed=True)
        ppg_ir = ppg_red
        msg = PpgRawAll(ts_lsb, ecg, ppg, ppg_red, ppg_ir)
        return msg


@dataclass
@ProtocolMessage.register(0xAC)
class ImuRaw(TimetickedMessage):
    payload_format = ">hhhhhh"
    acc_x: int = 0
    acc_y: int = 0
    acc_z: int = 0
    gyr_x: int = 0
    gyr_y: int = 0
    gyr_z: int = 0


@dataclass
@ProtocolMessage.register(0xA4)
class Imu(TimetickedMessage):
    payload_format = ">B"
    orientation_and_activity: int


@dataclass
@ProtocolMessage.register(0xB2)
class AccRaw(TimetickedMessage):
    payload_format = ">hhh"
    acc_x: int = 0
    acc_y: int = 0
    acc_z: int = 0


@dataclass
@ProtocolMessage.register(0xB3)
class GyroRaw(TimetickedMessage):
    payload_format = ">hhh"
    gyr_x: int = 0
    gyr_y: int = 0
    gyr_z: int = 0


@dataclass
@ProtocolMessage.register(0xA1)
class BatteryLevel(TimetickedMessage):
    payload_format = ">B"
    level: int


@dataclass
@ProtocolMessage.register(0xA5)
class HeartRate(TimetickedMessage):
    payload_format = ">H"
    rate: int


@dataclass
@ProtocolMessage.register(0xAD)
class HeartRateInterval(TimetickedMessage):
    payload_format = ">H"
    interval: int


@dataclass
@ProtocolMessage.register(0x74)
class NoOfPpgValues(TimetickedMessage):
    payload_format = ">B"
    ppg_values: int


@dataclass
@ProtocolMessage.register(0xA9)
class ChargeState(TimetickedMessage):
    payload_format = ">B"
    state: int


@dataclass
@ProtocolMessage.register(0xAA)
class BeltOnBody(TimetickedMessage):
    payload_format = ">B"
    on_body: int


@dataclass
@ProtocolMessage.register(0xB4)
class Temperature(TimetickedMessage):
    payload_format = ">h"
    temp_raw: int

    def temp_celsius(self) -> float:
        return self.temp_raw * TEMPERATURE_SCALE_FACTOR


@dataclass
@ProtocolMessage.register(0xB6)
class PulseRawList(TimetickedMessage):
    format: int
    no_of_ecgs: int
    no_of_ppgs: int
    ecgs: list[int]
    ppgs: list[int]
    len: int = 6  # actual length, since this is instance specific, not static

    @classmethod
    def default_length(cls, version: tuple[int, int, int] | None = None) -> int:
        """Return a dummy value, since this is instance specific for this class."""
        return 6

    def length(self, version: tuple[int, int, int] | None = None) -> int:
        return self.len

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None):
        if len(data) < 3:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected at least 10 bytes")
        (tick,) = struct.unpack("<H", data[0:2])
        (format_and_sizes,) = struct.unpack("<B", data[2:3])
        fmt, no_of_ecgs, no_of_ppgs = PulseRawList.to_format_and_lengths(format_and_sizes)
        ecgs = []
        ppgs = []
        bytes_per_ecg_and_ppg = 1 if fmt == 0 else 2 if fmt == 1 else 3 if fmt == 2 else 4
        length = 3 + (no_of_ecgs * bytes_per_ecg_and_ppg) + (no_of_ppgs * bytes_per_ecg_and_ppg)
        if len(data) < length:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected {length} bytes")
        pos = 3
        for _ in range(no_of_ecgs):
            ecg = int.from_bytes(data[pos : pos + bytes_per_ecg_and_ppg], byteorder="little", signed=True)
            ecgs.append(ecg)
            pos += bytes_per_ecg_and_ppg
        for _ in range(no_of_ppgs):
            ppg = int.from_bytes(data[pos : pos + bytes_per_ecg_and_ppg], byteorder="little", signed=True)
            ppgs.append(ppg)
            pos += bytes_per_ecg_and_ppg
        msg = PulseRawList(
            format=fmt,
            two_lsb_of_timestamp=tick,
            no_of_ecgs=no_of_ecgs,
            no_of_ppgs=no_of_ppgs,
            ecgs=ecgs,
            ppgs=ppgs,
        )
        msg.len = length
        return msg

    @staticmethod
    def to_format_and_lengths(format_and_sizes: int) -> tuple:
        fmt = format_and_sizes & 0x3
        no_of_ecgs = (format_and_sizes & 0x0F) >> 2
        no_of_ppgs = (format_and_sizes & 0xF0) >> 4
        return fmt, no_of_ecgs, no_of_ppgs


@dataclass
@ProtocolMessage.register(0xB8)
class PulseBlockEcg(TimetickedMessage):
    time: int
    channel: int
    num_samples: int
    samples: list[int]
    pkg_length: int

    @classmethod
    def default_length(cls, version: tuple[int, int, int] | None = None) -> int:
        """Return a dummy value, since this is instance specific for this class."""
        return 14

    def length(self, version: tuple[int, int, int] | None = None) -> int:
        return self.pkg_length

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None) -> PulseBlockEcg:
        if len(data) < 14:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes")
        channel = data[0]
        packed_ecgs = data[1]
        pkg_length = 1 + 1 + 8 + 4 + (packed_ecgs * 2)
        if len(data) < pkg_length:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes")
        (time,) = struct.unpack("<Q", data[2:10])
        samples = []
        ref = int.from_bytes(data[10:14], byteorder="little", signed=True)
        samples.append(ref)
        pos = 14
        for _ in range(packed_ecgs):
            sample = ref + int.from_bytes(data[pos : pos + 2], byteorder="little", signed=True)
            samples.append(sample)
            pos += 2
        msg = PulseBlockEcg(
            two_lsb_of_timestamp=tick,
            time=time,
            channel=channel,
            num_samples=packed_ecgs + 1,
            samples=samples,
            pkg_length=pkg_length,
        )
        return msg

    def encode(self) -> bytes:
        payload = struct.pack("<H", 0)
        return payload


@dataclass
@ProtocolMessage.register(0xB9)
class PulseBlockPpg(TimetickedMessage):
    time: int
    channel: int
    num_samples: int
    samples: list[int]
    pkg_length: int

    @classmethod
    def default_length(cls, version: tuple[int, int, int] | None = None) -> int:
        """Return a dummy value, since this is instance specific for this class."""
        return 14

    def length(self, version: tuple[int, int, int] | None = None) -> int:
        return self.pkg_length

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None) -> PulseBlockPpg:
        if len(data) < 13:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes")
        channel = data[0]
        packed_ppgs = data[1]
        pkg_length = 1 + 1 + 8 + 4 + (packed_ppgs * 2)
        if len(data) < pkg_length:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes")
        (time,) = struct.unpack("<Q", data[2:10])
        samples = []
        ref = int.from_bytes(data[10:14], byteorder="little", signed=True)
        samples.append(ref)
        pos = 14
        for _ in range(packed_ppgs):
            sample = ref + int.from_bytes(data[pos : pos + 2], byteorder="little", signed=True)
            samples.append(sample)
            pos += 2
        msg = PulseBlockPpg(
            time=time,
            channel=channel,
            num_samples=packed_ppgs + 1,
            samples=samples,
            pkg_length=pkg_length,
        )
        return msg

    def encode(self) -> bytes:
        payload = struct.pack("<H", 0)
        return payload


@dataclass
@ProtocolMessage.register(0xBB)
class BatteryDiagnostics(TimetickedMessage):
    payload_format = "<IIHHhhHHHH"
    ttf: int  # s Time To Full
    tte: int  # s Time To Empty
    voltage: int  # mV *10 (0-6553.5 mV) Battery Voltage
    avg_voltage: int  # mV *10 (0-6553.5 mV) Average Battery Voltage
    current: int  # mA *100 (-327.68 - +327.67 mA) Battery Current
    avg_current: int  # mA *100 (-327.68 - +327.67 mA) Average Battery Current
    full_cap: int
    # mAh *100 (0-655.35 mAh) Total battery capacity calculated after each cycle
    rep_cap: int  # mAh *100 (0-655.35 mAh) Remaining capacity
    repsoc: int  # % *100  (0-100.00 %) Reported State Of Charge (Combined and final result)
    vfsoc: int  # % *100  (0-100.00 %) Voltage based fuelgauge State Of Charge

    @classmethod
    def default_length(cls, version: tuple[int, int, int] | None = None) -> int:
        return struct.calcsize(cls.payload_format)

    @classmethod
    def decode(cls, data: bytes, version: tuple[int, int, int] | None = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="little", signed=False)
        msg = BatteryDiagnostics(
            ts_lsb,
            *struct.unpack(
                BatteryDiagnostics.struct_format,
                data[2 : cls.default_length(version) + 2],
            ),
        )
        return msg


# File protocol message registry
_FILE_MESSAGE_REGISTRY_OLD: dict[int, type[ProtocolMessage]] = {
    0x01: Header,
    0x71: Timestamp,
    0xAC: ImuRaw,
    0xA4: Imu,
    0xB1: PpgRaw,
    0xA2: PpgRawAll,
    0xA1: BatteryLevel,
    0xA5: HeartRate,
    0xAD: HeartRateInterval,
    0x74: NoOfPpgValues,
    0xA9: ChargeState,
    0xAA: BeltOnBody,
    0x07: AfeSettingsAll,
    0xB2: AccRaw,
    0xB3: GyroRaw,
    0xB4: Temperature,
    0xB6: PulseRawList,
    0xB8: PulseBlockEcg,
    0xB9: PulseBlockPpg,
    0xBB: BatteryDiagnostics,
}


def decode_message(data: bytes, version: tuple[int, int, int] | None = None) -> ProtocolMessage:
    """Decodes a bytes object into proper subclass of ProtocolMessage.

    raises LookupError if unknown message type.
    """
    message_type = data[0]

    # Special handling for version-dependent AfeSettings
    if message_type == 0x06:
        if isinstance(version, tuple) and version >= (4, 0, 1):
            return AfeSettings.decode(data[1:], version)
        else:
            return AfeSettingsOld.decode(data[1:], version)

    # Lookup message class from registry
    message_class = ProtocolMessage.subclasses.get(message_type)
    if message_class is None:
        raise LookupError(f"Unknown message type {hex(message_type)}")

    return message_class.decode(data[1:], version)

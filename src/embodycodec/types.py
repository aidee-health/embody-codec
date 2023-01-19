"""Complex types for the EmBody device
"""

import enum
import struct
from abc import ABC
from dataclasses import astuple
from dataclasses import dataclass
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union


class ExecuteCommandType(enum.Enum):
    RESET_DEVICE = 0x01
    REBOOT_DEVICE = 0x02
    PRESS_BUTTON = 0x03
    AFE_READ_ALL_REGISTERS = 0xA1
    AFE_WRITE_REGISTER = 0xA2
    AFE_CALIBRATION_COMMAND = 0xA3
    AFE_GAIN_SETTING = 0xA4


T = TypeVar("T", bound="ComplexType")


@dataclass
class ComplexType(ABC):
    """Abstract base class for complex types"""

    struct_format = ""
    """pack/unpack format to be overridden by sub-classes"""

    @classmethod
    def default_length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls: type[T], data: bytes) -> T:
        if len(data) < cls.default_length():
            raise BufferError(
                f"Buffer too short for message. Received "
                f"{len(data)} bytes, expected {cls.default_length()} bytes"
            )
        msg = cls(*(struct.unpack(cls.struct_format, data[0 : cls.default_length()])))
        return msg

    def length(self) -> int:
        return struct.calcsize(self.struct_format)

    def encode(self) -> bytes:
        return struct.pack(self.struct_format, *astuple(self))


@dataclass
class BloodPressure(ComplexType):
    struct_format = ">HHHIH"
    sys: int
    dia: int
    bp_map: int
    pat: int
    pulse: int


@dataclass
class Reporting(ComplexType):
    struct_format = ">HB"
    interval: int
    on_change: int


@dataclass
class PulseRaw(ComplexType):
    struct_format = ">ii"
    ecg: int
    ppg: int


@dataclass
class PulseRawAll(ComplexType):
    struct_format = ">iiii"
    ecg: int
    ppg_green: int
    ppg_red: int
    ppg_ir: int


@dataclass
class PulseRawList(ComplexType):
    tick: int
    format: int
    no_of_ecgs: int
    no_of_ppgs: int
    ecgs: list[int]
    ppgs: list[int]
    len = int(0)

    def length(self) -> int:
        return self.len

    @classmethod
    def decode(cls, data: bytes) -> "PulseRawList":
        if len(data) < 10:
            raise BufferError(
                f"Buffer too short for message. Received {len(data)} bytes, expected at least 10 bytes"
            )
        (tick,) = struct.unpack("<H", data[0:2])
        (format_and_sizes,) = struct.unpack("<B", data[2:3])
        fmt, no_of_ecgs, no_of_ppgs = PulseRawList.to_format_and_lengths(
            format_and_sizes
        )
        ecgs = []
        ppgs = []
        bytes_per_ecg_and_ppg = (
            1 if fmt == 0 else 2 if fmt == 1 else 3 if fmt == 2 else 4
        )
        pos = 3
        for _ in range(no_of_ecgs):
            ecg = int.from_bytes(
                data[pos : pos + bytes_per_ecg_and_ppg], byteorder="little", signed=True
            )
            ecgs.append(ecg)
            pos += bytes_per_ecg_and_ppg
        for _ in range(no_of_ppgs):
            ppg = int.from_bytes(
                data[pos : pos + bytes_per_ecg_and_ppg], byteorder="little", signed=True
            )
            ppgs.append(ppg)
            pos += bytes_per_ecg_and_ppg
        msg = PulseRawList(
            tick=tick,
            format=fmt,
            no_of_ecgs=no_of_ecgs,
            no_of_ppgs=no_of_ppgs,
            ecgs=ecgs,
            ppgs=ppgs,
        )
        msg.len = (
            1
            + (no_of_ecgs * bytes_per_ecg_and_ppg)
            + (no_of_ppgs * bytes_per_ecg_and_ppg)
        )
        return msg

    def encode(self) -> bytes:
        format_and_length = PulseRawList.from_format_and_lengths(
            self.format, self.no_of_ecgs, self.no_of_ppgs
        )
        bytes_per_ecg_and_ppg = (
            1
            if self.format == 0
            else 2
            if self.format == 1
            else 3
            if self.format == 2
            else 4
        )
        payload = struct.pack("<H", self.tick)
        payload += struct.pack("<B", format_and_length)
        for element in range(self.no_of_ecgs):
            payload += int.to_bytes(
                self.ecgs[element],
                length=bytes_per_ecg_and_ppg,
                byteorder="little",
                signed=True,
            )
        for element in range(self.no_of_ppgs):
            payload += int.to_bytes(
                self.ppgs[element],
                length=bytes_per_ecg_and_ppg,
                byteorder="little",
                signed=True,
            )
        return payload

    @staticmethod
    def to_format_and_lengths(format_and_sizes: int) -> tuple:
        fmt = format_and_sizes & 0x3
        no_of_ecgs = (format_and_sizes & 0x0F) >> 2
        no_of_ppgs = (format_and_sizes & 0xF0) >> 4
        return fmt, no_of_ecgs, no_of_ppgs

    @staticmethod
    def from_format_and_lengths(fmt: int, no_of_ecgs: int, no_of_ppgs: int) -> int:
        format_and_sizes = no_of_ppgs & 0xF
        format_and_sizes <<= 2
        format_and_sizes += no_of_ecgs & 0x3
        format_and_sizes <<= 2
        format_and_sizes += fmt & 0x3
        return format_and_sizes & 0xFF


@dataclass
class Imu(ComplexType):
    struct_format = ">B"
    orientation_and_activity: int


@dataclass
class ImuRaw(ComplexType):
    struct_format = ">hhhhhh"
    acc_x: int = 0
    acc_y: int = 0
    acc_z: int = 0
    gyr_x: int = 0
    gyr_y: int = 0
    gyr_z: int = 0


@dataclass
class AccRaw(ComplexType):
    struct_format = ">hhh"
    acc_x: int = 0
    acc_y: int = 0
    acc_z: int = 0


@dataclass
class GyroRaw(ComplexType):
    struct_format = ">hhh"
    gyr_x: int = 0
    gyr_y: int = 0
    gyr_z: int = 0


@dataclass
class Recording(ComplexType):
    struct_format = ">BBBBBB"
    day_start: int
    day_end: int
    day_interval: int
    night_interval: int
    recording_start: int
    recording_stop: int


@dataclass
class Diagnostics(ComplexType):
    struct_format = ">HhHHIIII"
    rep_soc: int
    avg_current: int
    rep_cap: int
    full_cap: int
    tte: int
    ttf: int
    voltage: int
    avg_voltage: int


@dataclass
class AfeSettings(ComplexType):
    struct_format = ">BBBBIIif"
    rf_gain: int
    cf_value: int
    ecg_gain: int
    ioffdac_range: int
    led1: int
    led4: int
    off_dac: int
    relative_gain: float


@dataclass
class AfeSettingsAll(ComplexType):
    struct_format = ">BBBBIIIIiiif"
    rf_gain: Optional[int]
    cf_value: Optional[int]
    ecg_gain: Optional[int]
    ioffdac_range: Optional[int]
    led1: Optional[int]
    led2: Optional[int]
    led3: Optional[int]
    led4: Optional[int]
    off_dac1: Optional[int]
    off_dac2: Optional[int]
    off_dac3: Optional[int]
    relative_gain: Optional[float]


F = TypeVar("F", bound="File")


@dataclass
class File(ComplexType):
    struct_format = ">26s"
    file_name: Union[str, bytes]

    @classmethod
    def decode(cls: type[F], data: bytes) -> F:
        msg = cls(*(struct.unpack(cls.struct_format, data[0 : cls.default_length()])))
        if msg.file_name is not None and isinstance(msg.file_name, bytes):
            msg.file_name = msg.file_name.split(b"\x00", maxsplit=1)[0].decode("utf-8")
        return msg

    def encode(self) -> bytes:
        return struct.pack(self.struct_format, str(self.file_name).encode("utf-8"))


@dataclass
class FileWithLength(File):
    struct_format = File.struct_format + "I"
    file_size: int

    def encode(self) -> bytes:
        return struct.pack(
            self.struct_format, str(self.file_name).encode("utf-8"), self.file_size
        )

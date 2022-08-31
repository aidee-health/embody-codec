"""Complex types for the EmBody device
"""

from abc import ABC
import struct
import enum
from dataclasses import dataclass, astuple


class ExecuteCommandType(enum.Enum):
    RESET_DEVICE = 0x01
    REBOOT_DEVICE = 0x02
    AFE_READ_ALL_REGISTERS = 0xA1
    AFE_WRITE_REGISTER = 0xA2
    AFE_CALIBRATION_COMMAND = 0xA3
    AFE_GAIN_SETTING = 0xA4


@dataclass
class ComplexType(ABC):
    """Abstract base class for complex types"""

    struct_format = ""

    @classmethod
    def length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls, data: bytes):
        if len(data) < cls.length():
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected {cls.length} bytes")
        msg = cls(*(struct.unpack(cls.struct_format, data[0:cls.length()])))
        return msg

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
    ecg: int
    no_of_ppgs: int
    ppgs: list[int]

    @classmethod
    def decode(cls, data: bytes):
        if len(data) < 10:
            raise BufferError(f"Buffer too short for message. Received {len(data)} bytes, expected at least 10 bytes")
        ecg, = struct.unpack("<i", data[0:4])
        no_of_ppgs, = struct.unpack("<B", data[4:5])
        ppgs = []
        pos = 5

        for _ in range(no_of_ppgs):
            ppg, = struct.unpack("<i", data[pos:pos+4])
            ppgs.append(ppg)
            pos += 4
        msg = PulseRawList(ecg=ecg, no_of_ppgs=no_of_ppgs, ppgs=ppgs)
        msg.length = 5 + (no_of_ppgs * 4)
        return msg

    def encode(self) -> bytes:
        payload = struct.pack("<i", self.ecg)
        payload += struct.pack("<B", self.no_of_ppgs)
        for element in range(self.no_of_ppgs):
            payload += struct.pack("<i", self.ppgs[element])
        return payload


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
    rf_gain: int
    cf_value: int
    ecg_gain: int
    ioffdac_range: int
    led1: int
    led2: int
    led3: int
    led4: int
    off_dac1: int
    off_dac2: int
    off_dac3: int
    relative_gain: float


@dataclass
class File(ComplexType):
    struct_format = ">26s"
    file_name: str

    @classmethod
    def decode(cls, data: bytes):
        msg = cls(*(struct.unpack(cls.struct_format, data[0:cls.length()])))
        if msg.file_name is not None and isinstance(msg.file_name, bytes):
            msg.file_name = msg.file_name.split(b'\x00', maxsplit=1)[0].decode('utf-8')
        return msg

    def encode(self) -> bytes:
        return struct.pack(self.struct_format, self.file_name.encode('utf-8'))


@dataclass
class FileWithLength(File):
    struct_format = File.struct_format + "I"
    file_size: int

    def encode(self) -> bytes:
        return struct.pack(self.struct_format, self.file_name.encode('utf-8'), self.file_size)

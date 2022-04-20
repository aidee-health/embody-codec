"""Complex types for the EmBody device
"""

from abc import ABC
import struct
from dataclasses import dataclass, astuple


@dataclass
class ComplexType(ABC):
    """Abstract base class for complex types"""

    struct_format = ""

    @classmethod
    def length(cls) -> int:
        """Length of complex type"""
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls, data: bytes):
        """Decode bytes into complex type object"""
        if len(data) < cls.length():
            raise BufferError("Buffer too short for message")
        msg = cls(*(struct.unpack(cls.struct_format, data[0:cls.length()])))
        return msg

    def encode(self) -> bytes:
        """Encode a complex type object to bytes"""
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

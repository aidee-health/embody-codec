"""Attribute types for the EmBody device

All attribute types inherits from the Attribute class, and provides self-contained encoding and decoding of
attributes.
"""

from abc import ABC
from typing import Optional
from datetime import datetime, timezone
import struct
from dataclasses import dataclass, astuple
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
        if len(data) < cls.length():
            raise BufferError(f"Attribute buffer too short for message. \
                                Received {len(data)} bytes, expected {cls.length} bytes")
        attr = cls(*(struct.unpack(cls.struct_format, data[0:cls.length()])))
        return attr

    def encode(self) -> bytes:
        return struct.pack(self.struct_format, *astuple(self))

    def formatted_value(self) -> Optional[str]:
        if hasattr(self, 'value'):
            return str(self.value)
        return None
    


@dataclass
class ZeroTerminatedStringAttribute(Attribute, ABC):
    value: str

    @classmethod
    def decode(cls, data: bytes):
        attr = cls(None)
        attr.value = (data[0:len(data)-1]).decode('ascii')
        return attr

    def encode(self) -> bytes:
        return bytes(self.value, 'ascii') + b'\x00'

    def formatted_value(self) -> Optional[str]:
        return self.value


@dataclass
class ComplexTypeAttribute(Attribute, ABC):
    value: ComplexType

    @classmethod
    def decode(cls, data: bytes):
        attr = cls(None)
        attr.value = cls.__dataclass_fields__['value'].type.decode(data)
        return attr

    def encode(self) -> bytes:
        return self.value.encode()
    
    def formatted_value(self) -> Optional[str]:
        return str(self.value) if self.value else None


@dataclass
class SerialNoAttribute(Attribute):
    struct_format = ">q"
    attribute_id = 0x01
    value: int

    def formatted_value(self) -> Optional[str]:
        return self.value.to_bytes(8, "big", signed=True).hex() if self.value else None


@dataclass
class FirmwareVersionAttribute(Attribute):
    struct_format = ">q"
    attribute_id = 0x02
    value: int

    def formatted_value(self) -> Optional[str]:
        newval = (self.value & 0xFFFFF).to_bytes(3, "big", signed=True).hex()
        return '.'.join(newval[i:i+2] for i in range(0, len(newval), 2))

@dataclass
class BluetoothMacAttribute(Attribute):
    struct_format = ">q"
    attribute_id = 0x03
    value: int

    def formatted_value(self) -> Optional[str]:
        return self.value.to_bytes(8, "big", signed=True).hex() if self.value else None


@dataclass
class ModelAttribute(ZeroTerminatedStringAttribute):
    attribute_id = 0x04


@dataclass
class VendorAttribute(ZeroTerminatedStringAttribute):
    attribute_id = 0x05


@dataclass
class AfeSettingsAttribute(ComplexTypeAttribute):
    struct_format = AfeSettings.struct_format
    attribute_id = 0x06
    value: AfeSettings


@dataclass
class AfeSettingsAllAttribute(ComplexTypeAttribute):
    struct_format = AfeSettingsAll.struct_format
    attribute_id = 0x07
    value: AfeSettingsAll


@dataclass
class CurrentTimeAttribute(Attribute):
    struct_format = ">Q"
    attribute_id = 0x71
    value: int

    def formatted_value(self) -> Optional[str]:
        return datetime.fromtimestamp(self.value / 1000, tz=timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class MeasurementDeactivatedAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0x72
    value: int


@dataclass
class TraceLevelAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0x73
    value: int


@dataclass
class NoOfPpgValuesAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0x74
    value: int


@dataclass
class BatteryLevelAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0xA1
    value: int


@dataclass
class PulseRawAllAttribute(ComplexTypeAttribute):
    struct_format = PulseRawAll.struct_format
    attribute_id = 0xA2
    value: PulseRawAll


@dataclass
class BloodPressureAttribute(ComplexTypeAttribute):
    struct_format = BloodPressure.struct_format
    attribute_id = 0xA3
    value: BloodPressure


@dataclass
class ImuAttribute(ComplexTypeAttribute):
    struct_format = Imu.struct_format
    attribute_id = 0xA4
    value: Imu


@dataclass
class HeartrateAttribute(Attribute):
    struct_format = ">H"
    attribute_id = 0xA5
    value: int


@dataclass
class SleepModeAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0xA6
    value: int


@dataclass
class BreathRateAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0xA7
    value: int


@dataclass
class HeartRateVariabilityAttribute(Attribute):
    struct_format = ">H"
    attribute_id = 0xA8
    value: int


@dataclass
class ChargeStateAttribute(Attribute):
    struct_format = ">?"
    attribute_id = 0xA9
    value: bool


@dataclass
class BeltOnBodyStateAttribute(Attribute):
    struct_format = ">?"
    attribute_id = 0xAA
    value: bool


@dataclass
class FirmwareUpdateProgressAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0xAB
    value: int


@dataclass
class ImuRawAttribute(ComplexTypeAttribute):
    struct_format = ImuRaw.struct_format
    attribute_id = 0xAC
    value: ImuRaw


@dataclass
class HeartRateIntervalAttribute(Attribute):
    struct_format = ">H"
    attribute_id = 0xAD
    value: int


@dataclass
class PulseRawAttribute(ComplexTypeAttribute):
    struct_format = PulseRaw.struct_format
    attribute_id = 0xB1
    value: PulseRaw


@dataclass
class AccRawAttribute(ComplexTypeAttribute):
    struct_format = AccRaw.struct_format
    attribute_id = 0xB2
    value: AccRaw


@dataclass
class GyroRawAttribute(ComplexTypeAttribute):
    struct_format = GyroRaw.struct_format
    attribute_id = 0xB3
    value: GyroRaw


@dataclass
class TemperatureAttribute(Attribute):
    struct_format = ">h"
    attribute_id = 0xB4
    value: int

    def temp_celsius(self) -> float:
        return self.value * 0.0078125

    def formatted_value(self) -> Optional[str]:
        return str(self.temp_celsius())


@dataclass
class DiagnosticsAttribute(ComplexTypeAttribute):
    struct_format = Diagnostics.struct_format
    attribute_id = 0xB5
    value: Diagnostics


@dataclass
class PulseRawListAttribute(ComplexTypeAttribute):
    struct_format = PulseRawList.struct_format
    attribute_id = 0xB6
    value: PulseRawList


@dataclass
class ExecuteCommandResponseAfeReadAllRegsAttribute(Attribute):
    attribute_id = 0xA1
    struct_format = ">BI"
    address: int
    value: int


def decode_executive_command_response(attribute_id, data: bytes) -> Attribute:
    """Decodes a bytes object into proper attribute object - raises BufferError if data buffer is too short.
    Returns None if unknown attribute"""

    if attribute_id == ExecuteCommandResponseAfeReadAllRegsAttribute.attribute_id:
        return ExecuteCommandResponseAfeReadAllRegsAttribute.decode(data)
    
    return None


def decode_attribute(attribute_id, data: bytes) -> Attribute:
    """Decodes a bytes object into proper attribute object - raises BufferError if data buffer is too short.
    Returns None if unknown attribute"""

    if attribute_id == SerialNoAttribute.attribute_id:
        return SerialNoAttribute.decode(data)
    if attribute_id == FirmwareVersionAttribute.attribute_id:
        return FirmwareVersionAttribute.decode(data)
    if attribute_id == BluetoothMacAttribute.attribute_id:
        return BluetoothMacAttribute.decode(data)
    if attribute_id == ModelAttribute.attribute_id:
        return ModelAttribute.decode(data)
    if attribute_id == VendorAttribute.attribute_id:
        return VendorAttribute.decode(data)
    if attribute_id == AfeSettingsAttribute.attribute_id:
        return AfeSettingsAttribute.decode(data)
    if attribute_id == AfeSettingsAllAttribute.attribute_id:
        return AfeSettingsAllAttribute.decode(data)
    if attribute_id == CurrentTimeAttribute.attribute_id:
        return CurrentTimeAttribute.decode(data)
    if attribute_id == MeasurementDeactivatedAttribute.attribute_id:
        return MeasurementDeactivatedAttribute.decode(data)
    if attribute_id == TraceLevelAttribute.attribute_id:
        return TraceLevelAttribute.decode(data)
    if attribute_id == NoOfPpgValuesAttribute.attribute_id:
        return NoOfPpgValuesAttribute.decode(data)
    if attribute_id == BatteryLevelAttribute.attribute_id:
        return BatteryLevelAttribute.decode(data)
    if attribute_id == PulseRawAllAttribute.attribute_id:
        return PulseRawAllAttribute.decode(data)
    if attribute_id == BloodPressureAttribute.attribute_id:
        return BloodPressureAttribute.decode(data)
    if attribute_id == ImuAttribute.attribute_id:
        return ImuAttribute.decode(data)
    if attribute_id == HeartrateAttribute.attribute_id:
        return HeartrateAttribute.decode(data)
    if attribute_id == SleepModeAttribute.attribute_id:
        return SleepModeAttribute.decode(data)
    if attribute_id == BreathRateAttribute.attribute_id:
        return BreathRateAttribute.decode(data)
    if attribute_id == HeartRateVariabilityAttribute.attribute_id:
        return HeartRateVariabilityAttribute.decode(data)
    if attribute_id == ChargeStateAttribute.attribute_id:
        return ChargeStateAttribute.decode(data)
    if attribute_id == BeltOnBodyStateAttribute.attribute_id:
        return BeltOnBodyStateAttribute.decode(data)
    if attribute_id == FirmwareUpdateProgressAttribute.attribute_id:
        return FirmwareUpdateProgressAttribute.decode(data)
    if attribute_id == ImuRawAttribute.attribute_id:
        return ImuRawAttribute.decode(data)
    if attribute_id == HeartRateIntervalAttribute.attribute_id:
        return HeartRateIntervalAttribute.decode(data)
    if attribute_id == PulseRawAttribute.attribute_id:
        return PulseRawAttribute.decode(data)
    if attribute_id == AccRawAttribute.attribute_id:
        return AccRawAttribute.decode(data)
    if attribute_id == GyroRawAttribute.attribute_id:
        return GyroRawAttribute.decode(data)
    if attribute_id == TemperatureAttribute.attribute_id:
        return TemperatureAttribute.decode(data)
    if attribute_id == DiagnosticsAttribute.attribute_id:
        return DiagnosticsAttribute.decode(data)
    if attribute_id == PulseRawListAttribute.attribute_id:
        return PulseRawListAttribute.decode(data)
    return None

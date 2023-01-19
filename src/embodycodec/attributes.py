"""Attribute types for the EmBody device

All attribute types inherits from the Attribute class, and provides self-contained encoding and decoding of
attributes.
"""

import struct
from abc import ABC
from dataclasses import astuple
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Optional
from typing import Type
from typing import TypeVar

from embodycodec import types as t


T = TypeVar("T", bound="Attribute")


@dataclass
class Attribute(ABC):
    """Abstract base class for attribute types"""

    struct_format = ""
    """struct format used to pack/unpack object - must be set by subclasses"""

    attribute_id = int(-1)
    """attribute id field - must be set by subclasses"""

    value: Any
    """value is implemented and overridden by subclasses."""

    @classmethod
    def length(cls) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls: type[T], data: bytes) -> T:
        if len(data) < cls.length():
            raise BufferError(
                f"Attribute buffer too short for message. \
                                Received {len(data)} bytes, expected {cls.length()} bytes"
            )
        attr = cls(*(struct.unpack(cls.struct_format, data[0 : cls.length()])))
        return attr

    def encode(self) -> bytes:
        return struct.pack(self.struct_format, *astuple(self))

    def formatted_value(self) -> Optional[str]:
        return str(self.value)


@dataclass
class ZeroTerminatedStringAttribute(Attribute, ABC):
    """Zero terminated string is actually not zero terminated - only length terminated..."""

    value: str

    @classmethod
    def decode(cls, data: bytes) -> "ZeroTerminatedStringAttribute":
        attr = cls((data[0 : len(data)]).decode("ascii"))
        return attr

    def encode(self) -> bytes:
        return bytes(self.value, "ascii")

    def formatted_value(self) -> Optional[str]:
        return self.value


CT = TypeVar("CT", bound="ComplexTypeAttribute")


@dataclass
class ComplexTypeAttribute(Attribute, ABC):
    value: t.ComplexType

    @classmethod
    def decode(cls: type[CT], data: bytes) -> CT:
        attr = cls(cls.__dataclass_fields__["value"].type.decode(data))
        return attr

    def encode(self) -> bytes:
        return self.value.encode()

    def formatted_value(self) -> Optional[str]:
        return str(self.value)


@dataclass
class SerialNoAttribute(Attribute):
    struct_format = ">q"
    attribute_id = 0x01
    value: int

    def formatted_value(self) -> Optional[str]:
        return self.value.to_bytes(8, "big", signed=True).hex() if self.value else None


@dataclass
class FirmwareVersionAttribute(Attribute):
    attribute_id = 0x02
    value: int

    @classmethod
    def decode(cls, data: bytes) -> "FirmwareVersionAttribute":
        if len(data) < cls.length():
            raise BufferError(
                f"FirmwareVersionAttribute buffer too short for message. \
                                Received {len(data)} bytes, expected {cls.length()} bytes"
            )
        return FirmwareVersionAttribute(
            int.from_bytes(data[0:3], byteorder="big", signed=False)
        )

    def encode(self) -> bytes:
        return int.to_bytes(self.value, length=3, byteorder="big", signed=True)

    @classmethod
    def length(cls) -> int:
        return 3

    def formatted_value(self) -> Optional[str]:
        newval = (self.value & 0xFFFFF).to_bytes(3, "big", signed=True).hex()
        return ".".join(newval[i : i + 2] for i in range(0, len(newval), 2))


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
    struct_format = t.AfeSettings.struct_format
    attribute_id = 0x06
    value: t.AfeSettings


@dataclass
class AfeSettingsAllAttribute(ComplexTypeAttribute):
    struct_format = t.AfeSettingsAll.struct_format
    attribute_id = 0x07
    value: t.AfeSettingsAll

    @classmethod
    def decode(cls, data: bytes) -> "AfeSettingsAllAttribute":
        """Special handling. certain versions of the device returns an empty attribute value."""

        if len(data) == 0:
            return AfeSettingsAllAttribute(
                value=t.AfeSettingsAll(
                    rf_gain=None,
                    cf_value=None,
                    ecg_gain=None,
                    ioffdac_range=None,
                    led1=None,
                    led2=None,
                    led3=None,
                    led4=None,
                    off_dac1=None,
                    off_dac2=None,
                    off_dac3=None,
                    relative_gain=None,
                )
            )
        return AfeSettingsAllAttribute(value=t.AfeSettingsAll.decode(data))


@dataclass
class CurrentTimeAttribute(Attribute):
    struct_format = ">Q"
    attribute_id = 0x71
    value: int

    def get_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.value / 1000, tz=timezone.utc)

    def formatted_value(self) -> Optional[str]:
        return self.get_datetime().replace(microsecond=0).isoformat()


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
    struct_format = t.PulseRawAll.struct_format
    attribute_id = 0xA2
    value: t.PulseRawAll


@dataclass
class BloodPressureAttribute(ComplexTypeAttribute):
    struct_format = t.BloodPressure.struct_format
    attribute_id = 0xA3
    value: t.BloodPressure


@dataclass
class ImuAttribute(ComplexTypeAttribute):
    struct_format = t.Imu.struct_format
    attribute_id = 0xA4
    value: t.Imu


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
    struct_format = t.ImuRaw.struct_format
    attribute_id = 0xAC
    value: t.ImuRaw


@dataclass
class HeartRateIntervalAttribute(Attribute):
    struct_format = ">H"
    attribute_id = 0xAD
    value: int


@dataclass
class PulseRawAttribute(ComplexTypeAttribute):
    struct_format = t.PulseRaw.struct_format
    attribute_id = 0xB1
    value: t.PulseRaw


@dataclass
class AccRawAttribute(ComplexTypeAttribute):
    struct_format = t.AccRaw.struct_format
    attribute_id = 0xB2
    value: t.AccRaw


@dataclass
class GyroRawAttribute(ComplexTypeAttribute):
    struct_format = t.GyroRaw.struct_format
    attribute_id = 0xB3
    value: t.GyroRaw


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
    struct_format = t.Diagnostics.struct_format
    attribute_id = 0xB5
    value: t.Diagnostics


@dataclass
class PulseRawListAttribute(ComplexTypeAttribute):
    struct_format = t.PulseRawList.struct_format
    attribute_id = 0xB6
    value: t.PulseRawList


@dataclass
class ExecuteCommandResponseAfeReadAllRegsAttribute(Attribute):
    attribute_id = 0xA1
    struct_format = ">BI"
    address: int
    value: int


@dataclass
class LedsAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0xC2
    value: int

    def led1(self) -> bool:
        return bool(self.value & 0b1)

    def led1_blinking(self) -> bool:
        return bool(self.value & 0b10)

    def led2(self) -> bool:
        return bool(self.value & 0b100)

    def led2_blinking(self) -> bool:
        return bool(self.value & 0b1000)

    def led3(self) -> bool:
        return bool(self.value & 0b10000)

    def led3_blinking(self) -> bool:
        return bool(self.value & 0b100000)

    def formatted_value(self) -> Optional[str]:
        if not self.value:
            return None
        return (
            f"L1: {self.led1()}, L1_blinking: {self.led1_blinking()}, "
            f"L2: {self.led2()}, L2_blinking: {self.led2_blinking()},"
            f"L3: {self.led3()}, L3_blinking: {self.led3_blinking()}"
        )


def decode_executive_command_response(attribute_id, data: bytes) -> Optional[Attribute]:
    """Decodes a bytes object into proper attribute object.

    Raises BufferError if data buffer is too short. Returns None if unknown attribute
    Raises LookupError if unknown message type.
    """

    if attribute_id == ExecuteCommandResponseAfeReadAllRegsAttribute.attribute_id:
        return ExecuteCommandResponseAfeReadAllRegsAttribute.decode(data)

    return None


def decode_attribute(attribute_id, data: bytes) -> Attribute:
    """Decodes a bytes object into proper attribute object.

    Raises BufferError if data buffer is too short.
    Raises LookupError if unknown message type.
    """

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
    if attribute_id == LedsAttribute.attribute_id:
        return LedsAttribute.decode(data)
    raise LookupError(f"Unknown attribute type {attribute_id}")

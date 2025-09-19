"""Attribute types for the EmBody device

All attribute types inherits from the Attribute class, and provides self-contained encoding and decoding of
attributes.

This module uses a dictionary-based registry pattern (_ATTRIBUTE_REGISTRY) for O(1) attribute type lookups.
Temperature conversions use the TEMPERATURE_SCALE_FACTOR constant (0.0078125 = 1/128).
"""

import struct
from abc import ABC
from dataclasses import astuple
from dataclasses import dataclass
from datetime import datetime
from datetime import UTC
from typing import Any
from typing import TypeVar

from embodycodec import types as t

# Temperature sensor conversion factor (degrees Celsius per raw unit)
# This factor converts raw sensor values to degrees Celsius
TEMPERATURE_SCALE_FACTOR = 0.0078125  # 1/128


T = TypeVar("T", bound="Attribute")


@dataclass
class Attribute(ABC):
    """Abstract base class for attribute types"""

    struct_format = ""
    """struct format used to pack/unpack object - must be set by subclasses"""

    attribute_id = -1
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

    def formatted_value(self) -> str | None:
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

    def formatted_value(self) -> str | None:
        return self.value


CT = TypeVar("CT", bound="ComplexTypeAttribute")


@dataclass
class ComplexTypeAttribute(Attribute, ABC):
    value: t.ComplexType

    @classmethod
    def decode(cls: type[CT], data: bytes) -> CT:
        value_type = cls.__annotations__["value"]
        if hasattr(value_type, "__origin__"):
            value_type = value_type.__args__[0]
        attr = cls(value_type.decode(data))
        return attr

    def encode(self) -> bytes:
        return self.value.encode()

    def formatted_value(self) -> str | None:
        return str(self.value)


@dataclass
class SerialNoAttribute(Attribute):
    struct_format = ">q"
    attribute_id = 0x01
    value: int

    def formatted_value(self) -> str | None:
        return self.value.to_bytes(8, "big", signed=True).hex().upper() if self.value else None


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
        return FirmwareVersionAttribute(int.from_bytes(data[0:3], byteorder="big", signed=False))

    def encode(self) -> bytes:
        return int.to_bytes(self.value, length=3, byteorder="big", signed=True)

    @classmethod
    def length(cls) -> int:
        return 3

    def formatted_value(self) -> str | None:
        newval = (self.value & 0xFFFFF).to_bytes(3, "big", signed=True)
        return ".".join(str(newval[i]).zfill(2) for i in range(0, len(newval), 1))


@dataclass
class BluetoothMacAttribute(Attribute):
    struct_format = ">q"
    attribute_id = 0x03
    value: int

    def formatted_value(self) -> str | None:
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
class SystemStatusNamesAttribute(Attribute):
    attribute_id = 0x08
    value: list[str]

    @classmethod
    def decode(cls, data: bytes) -> "SystemStatusNamesAttribute":
        if len(data) == 0:
            return SystemStatusNamesAttribute(value=[])
        string = data.decode("utf-8")
        return SystemStatusNamesAttribute(value=string.split(","))

    def encode(self) -> bytes:
        body = b""
        for n in self.value[:-1]:
            body += bytes(n, "ascii") + b","
        body += bytes(self.value[-1], "ascii")
        return body


@dataclass
class SystemStatusAttribute(ComplexTypeAttribute):
    attribute_id = 0xC3
    value: t.SystemStatus

    @classmethod
    def decode(cls, data: bytes) -> "SystemStatusAttribute":
        if len(data) == 0:
            return SystemStatusAttribute(value=t.SystemStatus(status=[], worst=[]))
        return SystemStatusAttribute(value=t.SystemStatus.decode(data))

    def encode(self) -> bytes:
        return self.value.encode()


@dataclass
class CurrentTimeAttribute(Attribute):
    struct_format = ">Q"
    attribute_id = 0x71
    value: int

    def get_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.value / 1000, tz=UTC)

    def formatted_value(self) -> str | None:
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
class DisableAutoRecAttribute(Attribute):
    struct_format = ">B"
    attribute_id = 0x75
    value: int


@dataclass
class OnBodyDetectAttribute(Attribute):
    struct_format = ">?"
    attribute_id = 0x76
    value: bool


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
        return self.value * TEMPERATURE_SCALE_FACTOR

    def formatted_value(self) -> str | None:
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
class FlashInfoAttribute(ComplexTypeAttribute):
    struct_format = t.FlashInfo.struct_format
    attribute_id = 0xB7
    value: t.FlashInfo


@dataclass
class BatteryDiagnosticsAttribute(ComplexTypeAttribute):
    struct_format = t.BatteryDiagnostics.struct_format
    attribute_id = 0xBB
    value: t.BatteryDiagnostics


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

    def formatted_value(self) -> str | None:
        if not self.value:
            return None
        return (
            f"L1: {self.led1()}, L1_blinking: {self.led1_blinking()}, "
            f"L2: {self.led2()}, L2_blinking: {self.led2_blinking()},"
            f"L3: {self.led3()}, L3_blinking: {self.led3_blinking()}"
        )


def decode_executive_command_response(attribute_id, data: bytes) -> Attribute | None:
    """Decodes a bytes object into proper attribute object.

    Raises BufferError if data buffer is too short. Returns None if unknown attribute
    Raises LookupError if unknown message type.
    """
    if attribute_id == ExecuteCommandResponseAfeReadAllRegsAttribute.attribute_id:
        return ExecuteCommandResponseAfeReadAllRegsAttribute.decode(data)

    return None


# Attribute registry for efficient O(1) lookup
_ATTRIBUTE_REGISTRY: dict[int, type[Attribute]] = {
    0x01: SerialNoAttribute,
    0x02: FirmwareVersionAttribute,
    0x03: BluetoothMacAttribute,
    0x04: ModelAttribute,
    0x05: VendorAttribute,
    0x06: AfeSettingsAttribute,
    0x07: AfeSettingsAllAttribute,
    0x08: SystemStatusNamesAttribute,
    0x71: CurrentTimeAttribute,
    0x72: MeasurementDeactivatedAttribute,
    0x73: TraceLevelAttribute,
    0x74: NoOfPpgValuesAttribute,
    0x75: DisableAutoRecAttribute,
    0x76: OnBodyDetectAttribute,
    0xA1: BatteryLevelAttribute,
    0xA2: PulseRawAllAttribute,
    0xA3: BloodPressureAttribute,
    0xA4: ImuAttribute,
    0xA5: HeartrateAttribute,
    0xA6: SleepModeAttribute,
    0xA7: BreathRateAttribute,
    0xA8: HeartRateVariabilityAttribute,
    0xA9: ChargeStateAttribute,
    0xAA: BeltOnBodyStateAttribute,
    0xAB: FirmwareUpdateProgressAttribute,
    0xAC: ImuRawAttribute,
    0xAD: HeartRateIntervalAttribute,
    0xB1: PulseRawAttribute,
    0xB2: AccRawAttribute,
    0xB3: GyroRawAttribute,
    0xB4: TemperatureAttribute,
    0xB5: DiagnosticsAttribute,
    0xB6: PulseRawListAttribute,
    0xB7: FlashInfoAttribute,
    0xBB: BatteryDiagnosticsAttribute,
    0xC2: LedsAttribute,
    0xC3: SystemStatusAttribute,
}


def decode_attribute(attribute_id, data: bytes) -> Attribute:
    """Decodes a bytes object into proper attribute object.

    Raises BufferError if data buffer is too short.
    Raises LookupError if unknown message type.
    """
    attribute_class = _ATTRIBUTE_REGISTRY.get(attribute_id)
    if attribute_class is None:
        raise LookupError(f"Unknown attribute type {attribute_id}")
    return attribute_class.decode(data)

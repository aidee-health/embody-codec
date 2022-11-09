"""File Codec for the Aidee EmBody device.

This class separates out the parsing of different message types from the EmBody device's file format. The first part
consists of all the different messages wrapped as subclasses of the ProtocolMessage dataclass. The bottom part
provides access methods for parsing one and one message from a bytes object.
"""

import struct
from dataclasses import dataclass
from dataclasses import field


@dataclass
class ProtocolMessage:
    # unpack format to be overridden by sub-classes, see https://docs.python.org/3/library/struct.html#format-characters
    unpack_format = None

    @classmethod
    def length(cls, version: tuple = None) -> int:
        return struct.calcsize(cls.unpack_format)

    @classmethod
    def decode(cls, data: bytes, version: tuple = None):
        if len(data) < cls.length(version):
            raise BufferError("Buffer too short for message")
        return cls(*(struct.unpack(cls.unpack_format, data[0 : cls.length(version)])))


@dataclass
class TimetickedMessage(ProtocolMessage):
    two_lsb_of_timestamp = None  # Dataclass workaround. Not specified with type to avoid having it as a dataclass field

    @classmethod
    def decode(cls, data: bytes, version: tuple = None):
        if len(data) < cls.length(version):
            raise BufferError("Buffer too short for message")
        tuples = struct.unpack(cls.unpack_format, data[0 : cls.length(version)])
        msg = cls(*tuples[1:])
        msg.two_lsb_of_timestamp = tuples[0]
        return msg


@dataclass
class Header(ProtocolMessage):
    unpack_format = ">Qc3scQ"
    serial: int
    fw_att: bytes
    firmware_version: bytes
    time_att: bytes
    current_time: int


@dataclass
class Timestamp(TimetickedMessage):
    unpack_format = ">HQ"
    current_time: int


@dataclass
class AfeSettingsOld(TimetickedMessage):
    unpack_format = ">Hbbbdddd"
    rf_gain: int
    cf_values: int
    ecg_gain: int
    led1: float
    led4: float
    ioff_dac_led1: float
    ioff_dac_amb: float


@dataclass
class AfeSettings(TimetickedMessage):
    unpack_format = ">HBBBBIIif"
    rf_gain: int
    cf_value: int
    ecg_gain: int
    ioffdac_range: int
    led1: int
    led4: int
    off_dac: int
    relative_gain: float


@dataclass
class AfeSettingsAll(TimetickedMessage):
    unpack_format = ">HBBBBIIIIiiif"
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
class PpgRaw(TimetickedMessage):
    ecg: int
    ppg: int

    @classmethod
    def length(cls, version: tuple = None) -> int:
        return 8

    @classmethod
    def decode(cls, data: bytes, version: tuple = None):
        if len(data) < cls.length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="big", signed=False)
        ecg = int.from_bytes(data[2:5], byteorder="big", signed=True)
        ppg = int.from_bytes(data[5:8], byteorder="big", signed=True)
        msg = PpgRaw(ecg, ppg)
        msg.two_lsb_of_timestamp = ts_lsb
        return msg


@dataclass
class PpgRawAll(TimetickedMessage):
    ecg: int
    ppg: int
    ppg_red: int
    ppg_ir: int

    @classmethod
    def length(cls, version: tuple = None) -> int:
        return 14

    @classmethod
    def decode(cls, data: bytes, version: tuple = None):
        if len(data) < cls.length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="big", signed=False)
        ecg = int.from_bytes(data[2:5], byteorder="big", signed=True)
        ppg = int.from_bytes(data[5:8], byteorder="big", signed=True)
        ppg_red = int.from_bytes(data[8:11], byteorder="big", signed=True)
        ppg_ir = int.from_bytes(data[11:14], byteorder="big", signed=True)
        msg = PpgRawAll(ecg, ppg, ppg_red, ppg_ir)
        msg.two_lsb_of_timestamp = ts_lsb
        return msg


@dataclass
class ImuRaw(TimetickedMessage):
    unpack_format = ">Hhhhhhh"
    acc_x: int = 0
    acc_y: int = 0
    acc_z: int = 0
    gyr_x: int = 0
    gyr_y: int = 0
    gyr_z: int = 0


@dataclass
class Imu(TimetickedMessage):
    unpack_format = ">HB"
    orientation_and_activity: int


@dataclass
class AccRaw(TimetickedMessage):
    unpack_format = ">Hhhh"
    acc_x: int = 0
    acc_y: int = 0
    acc_z: int = 0


@dataclass
class GyroRaw(TimetickedMessage):
    unpack_format = ">Hhhh"
    gyr_x: int = 0
    gyr_y: int = 0
    gyr_z: int = 0


@dataclass
class BatteryLevel(TimetickedMessage):
    unpack_format = ">HB"
    level: int


@dataclass
class HeartRate(TimetickedMessage):
    unpack_format = ">HH"
    rate: int


@dataclass
class HeartRateInterval(TimetickedMessage):
    unpack_format = ">HH"
    interval: int


@dataclass
class NoOfPpgValues(TimetickedMessage):
    unpack_format = ">HB"
    ppg_values: int


@dataclass
class ChargeState(TimetickedMessage):
    unpack_format = ">HB"
    state: int


@dataclass
class BeltOnBody(TimetickedMessage):
    unpack_format = ">HB"
    on_body: int


@dataclass
class Temperature(TimetickedMessage):
    unpack_format = ">Hh"
    temp_raw: int

    def temp_celsius(self) -> float:
        return self.temp_raw * 0.0078125


def decode_message(data: bytes, version: tuple = None) -> ProtocolMessage:
    """Decodes a bytes object into proper subclass of ProtocolMessage.

    raises LookupError if unknown message type.
    """

    message_type = data[0]
    if message_type == 0x01:
        return Header.decode(data[1:], version)
    elif message_type == 0x71:
        return Timestamp.decode(data[1:], version)
    elif message_type == 0xAC:
        return ImuRaw.decode(data[1:], version)
    elif message_type == 0xA4:
        return Imu.decode(data[1:], version)
    elif message_type == 0xB1:
        return PpgRaw.decode(data[1:], version)
    elif message_type == 0xA2:
        return PpgRawAll.decode(data[1:], version)
    elif message_type == 0xA1:
        return BatteryLevel.decode(data[1:], version)
    elif message_type == 0xA5:
        return HeartRate.decode(data[1:], version)
    elif message_type == 0xAD:
        return HeartRateInterval.decode(data[1:], version)
    elif message_type == 0x74:
        return NoOfPpgValues.decode(data[1:], version)
    elif message_type == 0xA9:
        return ChargeState.decode(data[1:], version)
    elif message_type == 0xAA:
        return BeltOnBody.decode(data[1:], version)
    elif message_type == 0x06 and version >= (4, 0, 1):
        return AfeSettings.decode(data[1:], version)
    elif message_type == 0x06:
        return AfeSettingsOld.decode(data[1:], version)
    elif message_type == 0x07:
        return AfeSettingsAll.decode(data[1:], version)
    elif message_type == 0xB2:
        return AccRaw.decode(data[1:], version)
    elif message_type == 0xB3:
        return GyroRaw.decode(data[1:], version)
    elif message_type == 0xB4:
        return Temperature.decode(data[1:], version)
    raise LookupError(f"Unknown message type {hex(message_type)}")

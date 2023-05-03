"""File Codec for the Aidee EmBody device.

This class separates out the parsing of different message types from the EmBody device's file format. The first part
consists of all the different messages wrapped as subclasses of the ProtocolMessage dataclass. The bottom part
provides access methods for parsing one and one message from a bytes object.
"""

import struct
from dataclasses import dataclass
from dataclasses import field
from typing import Optional


@dataclass
class ProtocolMessage:
    # unpack format to be overridden by sub-classes, see https://docs.python.org/3/library/struct.html#format-characters
    unpack_format = ""

    @classmethod
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        return struct.calcsize(cls.unpack_format)

    def length(self, version: Optional[tuple[int, int, int]] = None) -> int:
        return self.__class__.default_length(version)

    @classmethod
    def decode(cls, data: bytes, version: Optional[tuple[int, int, int]] = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        return cls(
            *(struct.unpack(cls.unpack_format, data[0 : cls.default_length(version)]))
        )


@dataclass
class TimetickedMessage(ProtocolMessage):
    two_lsb_of_timestamp = None  # Dataclass workaround. Not specified with type to avoid having it as a dataclass field

    @classmethod
    def decode(cls, data: bytes, version: Optional[tuple[int, int, int]] = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        tuples = struct.unpack(cls.unpack_format, data[0 : cls.default_length(version)])
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
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        return 8

    @classmethod
    def decode(cls, data: bytes, version: Optional[tuple[int, int, int]] = None):
        if len(data) < cls.default_length(version):
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
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        return 11

    @classmethod
    def decode(cls, data: bytes, version: Optional[tuple[int, int, int]] = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="big", signed=False)
        ecg = int.from_bytes(data[2:5], byteorder="big", signed=True)
        ppg = int.from_bytes(data[5:8], byteorder="big", signed=True)
        ppg_red = int.from_bytes(data[8:11], byteorder="big", signed=True)
        ppg_ir = ppg_red
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


@dataclass
class PulseRawList(TimetickedMessage):
    format: int
    no_of_ecgs: int
    no_of_ppgs: int
    ecgs: list[int]
    ppgs: list[int]
    len: int = 6  # actual length, since this is instance specific, not static

    @classmethod
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        """Return a dummy value, since this is instance specific for this class."""
        return 6

    def length(self, version: Optional[tuple[int, int, int]] = None) -> int:
        return self.len

    @classmethod
    def decode(cls, data: bytes, version: Optional[tuple[int, int, int]] = None):
        if len(data) < 3:
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
        length = (
            3
            + (no_of_ecgs * bytes_per_ecg_and_ppg)
            + (no_of_ppgs * bytes_per_ecg_and_ppg)
        )
        if len(data) < length:
            raise BufferError(
                f"Buffer too short for message. Received {len(data)} bytes, expected {length} bytes"
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
            format=fmt,
            no_of_ecgs=no_of_ecgs,
            no_of_ppgs=no_of_ppgs,
            ecgs=ecgs,
            ppgs=ppgs,
        )
        msg.two_lsb_of_timestamp = tick
        msg.len = length
        return msg

    @staticmethod
    def to_format_and_lengths(format_and_sizes: int) -> tuple:
        fmt = format_and_sizes & 0x3
        no_of_ecgs = (format_and_sizes & 0x0F) >> 2
        no_of_ppgs = (format_and_sizes & 0xF0) >> 4
        return fmt, no_of_ecgs, no_of_ppgs


@dataclass
class PulseBlockEcg(TimetickedMessage):
    time: int
    channel: int
    num_samples: int
    samples: list[int]
    pkg_length: int

    @classmethod
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        """Return a dummy value, since this is instance specific for this class."""
        return 14

    def length(self, version: Optional[tuple[int, int, int]] = None) -> int:
        return self.pkg_length

    @classmethod
    def decode(
        cls, data: bytes, version: Optional[tuple[int, int, int]] = None
    ) -> "PulseBlockEcg":
        if len(data) < 14:
            raise BufferError(
                f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes"
            )
        channel = data[0]
        packed_ecgs = data[1]
        pkg_length = 1 + 1 + 8 + 4 + (packed_ecgs * 2)
        if len(data) < pkg_length:
            raise BufferError(
                f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes"
            )
        (time,) = struct.unpack("<Q", data[2:10])
        samples = []
        ref = int.from_bytes(data[10:14], byteorder="little", signed=True)
        samples.append(ref)
        pos = 14
        for _ in range(packed_ecgs):
            sample = ref + int.from_bytes(
                data[pos : pos + 2], byteorder="little", signed=True
            )
            samples.append(sample)
            pos += 2
        msg = PulseBlockEcg(
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
class PulseBlockPpg(TimetickedMessage):
    time: int
    channel: int
    num_samples: int
    samples: list[int]
    pkg_length: int

    @classmethod
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        """Return a dummy value, since this is instance specific for this class."""
        return 14

    def length(self, version: Optional[tuple[int, int, int]] = None) -> int:
        return self.pkg_length

    @classmethod
    def decode(
        cls, data: bytes, version: Optional[tuple[int, int, int]] = None
    ) -> "PulseBlockPpg":
        if len(data) < 13:
            raise BufferError(
                f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes"
            )
        channel = data[0]
        packed_ppgs = data[1]
        pkg_length = 1 + 1 + 8 + 4 + (packed_ppgs * 2)
        if len(data) < pkg_length:
            raise BufferError(
                f"Buffer too short for message. Received {len(data)} bytes, expected at least 13 bytes"
            )
        (time,) = struct.unpack("<Q", data[2:10])
        samples = []
        ref = int.from_bytes(data[10:14], byteorder="little", signed=True)
        samples.append(ref)
        pos = 14
        for _ in range(packed_ppgs):
            sample = ref + int.from_bytes(
                data[pos : pos + 2], byteorder="little", signed=True
            )
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
class BatteryDiagnostics(TimetickedMessage):
    struct_format = "<IIHHhhHHHH"
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
    def default_length(cls, version: Optional[tuple[int, int, int]] = None) -> int:
        return struct.calcsize(cls.struct_format)

    @classmethod
    def decode(cls, data: bytes, version: Optional[tuple[int, int, int]] = None):
        if len(data) < cls.default_length(version):
            raise BufferError("Buffer too short for message")
        ts_lsb = int.from_bytes(data[0:2], byteorder="little", signed=False)
        msg = BatteryDiagnostics(
            *struct.unpack(
                BatteryDiagnostics.struct_format,
                data[2 : cls.default_length(version) + 2],
            )
        )
        msg.two_lsb_of_timestamp = ts_lsb
        return msg


def decode_message(
    data: bytes, version: Optional[tuple[int, int, int]] = None
) -> ProtocolMessage:
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
    elif message_type == 0x06 and isinstance(version, tuple) and version >= (4, 0, 1):
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
    elif message_type == 0xB6:
        return PulseRawList.decode(data[1:], version)
    elif message_type == 0xB8:
        return PulseBlockEcg.decode(data[1:], version)
    elif message_type == 0xB9:
        return PulseBlockPpg.decode(data[1:], version)
    elif message_type == 0xBB:
        return BatteryDiagnostics.decode(data[1:], version)
    raise LookupError(f"Unknown message type {hex(message_type)}")

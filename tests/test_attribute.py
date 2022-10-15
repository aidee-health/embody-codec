from datetime import datetime

from embodycodec import attributes
from embodycodec import types


def test_encode_decode_serial_no() -> None:
    do_test_encode_decode_attribute(
        attributes.SerialNoAttribute(12345678),
        b"\x00\x00\x00\x00\x00\xbc\x61\x4e",
    )


def test_serial_no_attribute_format_value() -> None:
    assert (
        attributes.SerialNoAttribute(12345678).formatted_value() == "0000000000bc614e"
    )


def test_encode_decode_firmware_version() -> None:
    do_test_encode_decode_attribute(
        attributes.FirmwareVersionAttribute(0x050202), b"\x05\x02\x02"
    )


def test_firmware_version_format_value() -> None:
    assert attributes.FirmwareVersionAttribute(0x010203).formatted_value() == "01.02.03"


def test_encode_decode_bluetooth_mac() -> None:
    do_test_encode_decode_attribute(
        attributes.BluetoothMacAttribute(12345678),
        b"\x00\x00\x00\x00\x00\xbc\x61\x4e",
    )


def test_encode_decode_model() -> None:
    do_test_encode_decode_attribute(
        attributes.ModelAttribute("Aidee Embody"),
        b"\x41\x69\x64\x65\x65\x20\x45\x6d\x62\x6f\x64\x79",
    )


def test_encode_decode_vendor() -> None:
    do_test_encode_decode_attribute(
        attributes.VendorAttribute("Aidee"), b"\x41\x69\x64\x65\x65"
    )


def test_encode_decode_afe_settings() -> None:
    do_test_encode_decode_attribute(
        attributes.AfeSettingsAttribute(
            value=types.AfeSettings(
                ecg_gain=4,
                ioffdac_range=0,
                off_dac=-463002,
                relative_gain=51.78207015991211,
                rf_gain=2,
                led1=6217,
                led4=6217,
                cf_value=2,
            )
        ),
        b"\x02\x02\x04\x00\x00\x00\x18\x49\x00\x00\x18\x49\xff\xf8\xef\x66\x42\x4f\x20\xd7",
    )


def test_encode_decode_afe_settings_all() -> None:
    do_test_encode_decode_attribute(
        attributes.AfeSettingsAllAttribute(
            value=types.AfeSettingsAll(
                rf_gain=5,
                cf_value=2,
                ecg_gain=4,
                ioffdac_range=0,
                led1=6217,
                led2=6217,
                led3=6217,
                led4=6217,
                off_dac1=-463004,
                off_dac2=-463003,
                off_dac3=-463002,
                relative_gain=51.78207015991211,
            )
        ),
        b"\x05\x02\x04\x00\x00\x00\x18\x49\x00\x00\x18\x49\x00\x00\x18\x49\x00\x00\x18"
        b"\x49\xff\xf8\xef\x64\xff\xf8\xef\x65\xff\xf8\xef\x66\x42\x4f\x20\xd7",
    )


def test_encode_decode_current_time() -> None:
    do_test_encode_decode_attribute(
        attributes.CurrentTimeAttribute(
            int(
                datetime.fromisoformat("2022-04-20 00:05:25.283+00:00").timestamp()
                * 1000
            )
        ),
        b"\x00\x00\x01\x80\x44\x49\xbe\xa3",
    )


def test_current_time_format_value() -> None:
    assert (
        attributes.CurrentTimeAttribute(
            int(
                datetime.fromisoformat("2022-04-20 00:05:25.283+00:00").timestamp()
                * 1000
            )
        ).formatted_value()
        == "2022-04-20T00:05:25+00:00"
    )


def test_encode_decode_measurement_deactivated() -> None:
    do_test_encode_decode_attribute(
        attributes.MeasurementDeactivatedAttribute(1), b"\x01"
    )


def test_encode_decode_measurement_trace_level() -> None:
    do_test_encode_decode_attribute(attributes.TraceLevelAttribute(2), b"\x02")


def test_encode_decode_no_of_ppg_values() -> None:
    do_test_encode_decode_attribute(attributes.NoOfPpgValuesAttribute(3), b"\x03")


def test_encode_decode_battery_level() -> None:
    do_test_encode_decode_attribute(attributes.BatteryLevelAttribute(3), b"\x03")


def test_encode_decode_pulse_raw() -> None:
    do_test_encode_decode_attribute(
        attributes.PulseRawAttribute(value=types.PulseRaw(ecg=1, ppg=1000)),
        b"\x00\x00\x00\x01\x00\x00\x03\xe8",
    )


def test_encode_decode_pulse_raw_all() -> None:
    do_test_encode_decode_attribute(
        attributes.PulseRawAllAttribute(
            value=types.PulseRawAll(ecg=1, ppg_green=1000, ppg_red=100, ppg_ir=5)
        ),
        b"\x00\x00\x00\x01\x00\x00\x03\xe8\x00\x00\x00\x64\x00\x00\x00\x05",
    )


def test_encode_decode_pulse_raw_list() -> None:
    """Special type, since it's little endian"""
    do_test_encode_decode_attribute(
        attributes.PulseRawListAttribute(
            value=types.PulseRawList(
                tick=843,
                format=3,
                no_of_ecgs=1,
                no_of_ppgs=3,
                ecgs=[1],
                ppgs=[1000, 100, 5],
            )
        ),
        b"K\x037\x01\x00\x00\x00\xe8\x03\x00\x00d\x00\x00\x00\x05\x00\x00\x00",
    )


def test_convert_pulse_raw_list_format_from_complex_byte() -> None:
    fmt, ecg_length, ppg_length = types.PulseRawList.to_format_and_lengths(0x37)
    assert fmt == 3
    assert ecg_length == 1
    assert ppg_length == 3


def test_convert_pulse_raw_list_format_to_complex_byte() -> None:
    fmt_and_lengths = types.PulseRawList.from_format_and_lengths(3, 1, 3)
    assert fmt_and_lengths == 0x37


def test_encode_decode_pulse_blood_pressure() -> None:
    do_test_encode_decode_attribute(
        attributes.BloodPressureAttribute(
            value=types.BloodPressure(sys=120, dia=80, bp_map=100, pat=78, pulse=55)
        ),
        b"\x00\x78\x00\x50\x00\x64\x00\x00\x00\x4e\x00\x37",
    )


def test_encode_decode_imu() -> None:
    do_test_encode_decode_attribute(
        attributes.ImuAttribute(value=types.Imu(orientation_and_activity=5)),
        b"\x05",
    )


def test_encode_decode_heart_rate() -> None:
    do_test_encode_decode_attribute(
        attributes.HeartrateAttribute(value=55), b"\x00\x37"
    )


def test_encode_decode_sleep_mode() -> None:
    do_test_encode_decode_attribute(attributes.SleepModeAttribute(value=4), b"\x04")


def test_encode_decode_breath_rate() -> None:
    do_test_encode_decode_attribute(attributes.BreathRateAttribute(value=16), b"\x10")


def test_encode_decode_heart_rate_variability() -> None:
    do_test_encode_decode_attribute(
        attributes.HeartRateVariabilityAttribute(value=102), b"\x00\x66"
    )


def test_encode_decode_charge_state() -> None:
    decoded = do_test_encode_decode_attribute(
        attributes.ChargeStateAttribute(value=True), b"\x01"
    )
    assert decoded.value is True


def test_encode_decode_belt_on_body_state() -> None:
    decoded = do_test_encode_decode_attribute(
        attributes.BeltOnBodyStateAttribute(value=False), b"\x00"
    )
    assert decoded.value is False


def test_encode_decode_firmware_update_progress() -> None:
    do_test_encode_decode_attribute(
        attributes.FirmwareUpdateProgressAttribute(value=95), b"\x5f"
    )


def test_encode_decode_imu_raw() -> None:
    do_test_encode_decode_attribute(
        attributes.ImuRawAttribute(
            value=types.ImuRaw(
                acc_x=271, acc_y=-15381, acc_z=4991, gyr_x=46, gyr_y=-9, gyr_z=-36
            )
        ),
        b"\x01\x0f\xc3\xeb\x13\x7f\x00\x2e\xff\xf7\xff\xdc",
    )


def test_encode_decode_heart_rate_interval() -> None:
    do_test_encode_decode_attribute(
        attributes.HeartRateIntervalAttribute(value=15), b"\x00\x0F"
    )


def test_encode_decode_pulse_raw_attribute() -> None:
    do_test_encode_decode_attribute(
        attributes.PulseRawAttribute(value=types.PulseRaw(ecg=1, ppg=1000)),
        b"\x00\x00\x00\x01\x00\x00\x03\xe8",
    )


def test_encode_decode_pulse_raw_all_attribute() -> None:
    do_test_encode_decode_attribute(
        attributes.PulseRawAllAttribute(
            value=types.PulseRawAll(ecg=1, ppg_green=1000, ppg_red=100, ppg_ir=5)
        ),
        b"\x00\x00\x00\x01\x00\x00\x03\xe8\x00\x00\x00\x64\x00\x00\x00\x05",
    )


def test_encode_decode_acc_raw() -> None:
    do_test_encode_decode_attribute(
        attributes.AccRawAttribute(
            value=types.AccRaw(acc_x=271, acc_y=-15381, acc_z=4991)
        ),
        b"\x01\x0f\xc3\xeb\x13\x7f",
    )


def test_encode_decode_gyro_raw() -> None:
    do_test_encode_decode_attribute(
        attributes.GyroRawAttribute(value=types.GyroRaw(gyr_x=46, gyr_y=-9, gyr_z=-36)),
        b"\x00\x2e\xff\xf7\xff\xdc",
    )


def test_encode_decode_temperature() -> None:
    decoded = do_test_encode_decode_attribute(
        attributes.TemperatureAttribute(value=3200), b"\x0C\x80"
    )
    assert decoded.temp_celsius() == 25.0
    assert decoded.formatted_value() == "25.0"
    decoded = do_test_encode_decode_attribute(
        attributes.TemperatureAttribute(value=-5120), b"\xEC\x00"
    )
    assert decoded.temp_celsius() == -40.0
    assert decoded.formatted_value() == "-40.0"


def test_encode_decode_diagnostics() -> None:
    do_test_encode_decode_attribute(
        attributes.DiagnosticsAttribute(
            value=types.Diagnostics(
                rep_soc=9173,
                avg_current=-375,
                rep_cap=29350,
                full_cap=32000,
                tte=281278112,
                ttf=368634368,
                voltage=406125,
                avg_voltage=406039,
            )
        ),
        b"#\xd5\xfe\x89r\xa6}\x00\x10\xc3\xf6\xa0\x15\xf8\xea\x00\x00\x062m\x00\x062\x17",
    )


def do_test_encode_decode_attribute(
    attribute: attributes.Attribute, expected_encoded: bytes
):
    encoded = attribute.encode()
    assert encoded == expected_encoded
    decoded = attributes.decode_attribute(attribute.attribute_id, encoded)
    assert isinstance(decoded, type(attribute))
    assert decoded.value == attribute.value
    assert decoded.attribute_id == attribute.attribute_id
    assert attribute.formatted_value() is not None
    return decoded

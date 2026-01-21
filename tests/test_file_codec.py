import pytest

from embodycodec import file_codec as codec


def test_decode_header() -> None:
    assert 21 == codec.Header.default_length()
    header = codec.Header.decode(bytes.fromhex("65c6fa2569b1633302040106710000017e5353729d"))
    assert b"\x02" == header.fw_att
    assert b"\x04\x01\x06" == header.firmware_version
    assert (4, 1, 6) == tuple(header.firmware_version)
    assert b"q" == header.time_att
    assert 1642075484829 == header.current_time
    assert 7333824081813398323 == header.serial


def test_decode_timestamp() -> None:
    assert 10 == codec.Timestamp.default_length()
    timestamp = codec.Timestamp.decode(bytes.fromhex("00020000017e5353729d"))
    assert 2 == timestamp.two_lsb_of_timestamp
    assert 1642075484829 == timestamp.current_time


def test_decode_afe_settings_old() -> None:
    assert 37 == codec.AfeSettingsOld.default_length()


def test_decode_afe_settings() -> None:
    assert 22 == codec.AfeSettings.default_length()
    afe_settings = codec.AfeSettings.decode(bytes.fromhex("0002050204000000184900001849fff8ef66424f20d7"))
    assert 2 == afe_settings.two_lsb_of_timestamp
    assert 4 == afe_settings.ecg_gain
    assert 0 == afe_settings.ioffdac_range
    assert -463002 == afe_settings.off_dac[0]
    assert 51.78207015991211 == afe_settings.relative_gain
    assert 6217 == afe_settings.i_led[0]
    assert 6217 == afe_settings.i_led[1]
    assert 2 == afe_settings.cf_value


def test_decode_afe_settings_all() -> None:
    assert 38 == codec.AfeSettingsAll.default_length()
    afe_settings = codec.AfeSettingsAll.decode(
        bytes.fromhex("00020502040000001849000018490000184900001849fff8ef64fff8ef65fff8ef66424f20d7")
    )
    assert 2 == afe_settings.two_lsb_of_timestamp
    assert 5 == afe_settings.rf_gain
    assert 2 == afe_settings.cf_value
    assert 4 == afe_settings.ecg_gain
    assert 0 == afe_settings.ioffdac_range
    assert 6217 == afe_settings.i_led[0]
    assert 6217 == afe_settings.i_led[1]
    assert 6217 == afe_settings.i_led[2]
    assert 6217 == afe_settings.i_led[3]
    assert -463004 == afe_settings.off_dac[0]
    assert -463003 == afe_settings.off_dac[1]
    assert -463002 == afe_settings.off_dac[2]
    assert 51.78207015991211 == afe_settings.relative_gain


def test_decode_ppg_raw() -> None:
    assert 8 == codec.PpgRaw.default_length()
    ppg_raw = codec.PpgRaw.decode(bytes.fromhex("00020002090357f7"))
    assert 2 == ppg_raw.two_lsb_of_timestamp
    assert 521 == ppg_raw.ecg
    assert 219127 == ppg_raw.ppg


def test_decode_ppg_raw_all() -> None:
    assert 11 == codec.PpgRawAll.default_length()
    ppg_raw = codec.PpgRawAll.decode(bytes.fromhex("00020002090357f70357f7"))
    assert 2 == ppg_raw.two_lsb_of_timestamp
    assert 521 == ppg_raw.ecg
    assert 219127 == ppg_raw.ppg
    assert 219127 == ppg_raw.ppg_red
    assert 219127 == ppg_raw.ppg_ir


def test_decode_imu_raw() -> None:
    assert 14 == codec.ImuRaw.default_length()
    imu_raw = codec.ImuRaw.decode(bytes.fromhex("72a7010fc3eb137f002efff7ffdc"))
    assert 29351 == imu_raw.two_lsb_of_timestamp
    assert 271 == imu_raw.acc_x
    assert -15381 == imu_raw.acc_y
    assert 4991 == imu_raw.acc_z
    assert 46 == imu_raw.gyr_x
    assert -9 == imu_raw.gyr_y
    assert -36 == imu_raw.gyr_z


def test_decode_acc_raw() -> None:
    assert 8 == codec.AccRaw.default_length()
    acc_raw = codec.AccRaw.decode(bytes.fromhex("72a7010fc3eb137f"))
    assert 29351 == acc_raw.two_lsb_of_timestamp
    assert 271 == acc_raw.acc_x
    assert -15381 == acc_raw.acc_y
    assert 4991 == acc_raw.acc_z


def test_decode_gyro_raw() -> None:
    assert 8 == codec.GyroRaw.default_length()
    gyro_raw = codec.GyroRaw.decode(bytes.fromhex("72a7002efff7ffdc"))
    assert 29351 == gyro_raw.two_lsb_of_timestamp
    assert 46 == gyro_raw.gyr_x
    assert -9 == gyro_raw.gyr_y
    assert -36 == gyro_raw.gyr_z


def test_decode_imu() -> None:
    assert 3 == codec.Imu.default_length()
    imu = codec.Imu.decode(bytes.fromhex("72a705"))
    assert 29351 == imu.two_lsb_of_timestamp
    assert 5 == imu.orientation_and_activity


def test_battery_level() -> None:
    assert 3 == codec.BatteryLevel.default_length()
    level = codec.BatteryLevel.decode(bytes.fromhex("72a705"))
    assert 29351 == level.two_lsb_of_timestamp
    assert 5 == level.level


def test_heart_rate() -> None:
    assert 4 == codec.HeartRate.default_length()
    rate = codec.HeartRate.decode(bytes.fromhex("72a70005"))
    assert 29351 == rate.two_lsb_of_timestamp
    assert 5 == rate.rate


def test_heart_rate_interval() -> None:
    assert 4 == codec.HeartRateInterval.default_length()
    interval = codec.HeartRateInterval.decode(bytes.fromhex("72a70005"))
    assert 29351 == interval.two_lsb_of_timestamp
    assert 5 == interval.interval


def test_no_of_ppg_values() -> None:
    assert 3 == codec.NoOfPpgValues.default_length()
    vals = codec.NoOfPpgValues.decode(bytes.fromhex("72a703"))
    assert 29351 == vals.two_lsb_of_timestamp
    assert 3 == vals.ppg_values


def test_charge_state() -> None:
    assert 3 == codec.ChargeState.default_length()
    state = codec.ChargeState.decode(bytes.fromhex("72a703"))
    assert 29351 == state.two_lsb_of_timestamp
    assert 3 == state.state


def test_belt_on_body() -> None:
    assert 3 == codec.BeltOnBody.default_length()
    bob = codec.BeltOnBody.decode(bytes.fromhex("72a701"))
    assert 29351 == bob.two_lsb_of_timestamp
    assert 1 == bob.on_body


def test_temperature() -> None:
    assert 4 == codec.Temperature.default_length()
    temp = codec.Temperature.decode(bytes.fromhex("72a70C80"))
    assert 3200 == temp.temp_raw
    assert 25.0 == temp.temp_celsius()
    temp = codec.Temperature.decode(bytes.fromhex("72a7EC00"))
    assert -5120 == temp.temp_raw
    assert -40.0 == temp.temp_celsius()


def test_decode_pulse_raw_list() -> None:
    ppg_raw = codec.PulseRawList.decode(b"K\x037\x01\x00\x00\x00\xe8\x03\x00\x00d\x00\x00\x00\x05\x00\x00\x00")
    assert 843 == ppg_raw.two_lsb_of_timestamp
    assert 1 == ppg_raw.ecgs[0]
    assert 1000 == ppg_raw.ppgs[0]
    assert 100 == ppg_raw.ppgs[1]
    assert 5 == ppg_raw.ppgs[2]
    assert 19 == ppg_raw.len


def test_decode_pulse_raw_list2() -> None:
    ppg_raw = codec.PulseRawList.decode(bytes.fromhex("0b354794dafffffb674100d42d8e00bc0fe900fb7cb400"))
    assert 13579 == ppg_raw.two_lsb_of_timestamp
    assert 1 == ppg_raw.no_of_ecgs
    assert 4 == ppg_raw.no_of_ppgs
    assert -9580 == ppg_raw.ecgs[0]
    assert 4286459 == ppg_raw.ppgs[0]
    assert 9317844 == ppg_raw.ppgs[1]
    assert 15273916 == ppg_raw.ppgs[2]
    assert 11828475 == ppg_raw.ppgs[3]
    assert 23 == ppg_raw.length()


def test_decode_pulse_raw_list_with_too_short_buffer() -> None:
    with pytest.raises(BufferError):
        codec.PulseRawList.decode(bytes.fromhex("0b354794dafffffb674100"))


def test_convert_pulse_raw_list_format_from_complex_byte() -> None:
    fmt, ecg_length, ppg_length = codec.PulseRawList.to_format_and_lengths(0x37)
    assert fmt == 3
    assert ecg_length == 1
    assert ppg_length == 3


def test_decode_battery_diagnostics() -> None:
    diag = codec.BatteryDiagnostics.decode(bytes.fromhex("0b35010000000200000003000400050006000700080009000A00"))
    assert 13579 == diag.two_lsb_of_timestamp
    assert 1 == diag.ttf
    assert 2 == diag.tte
    assert 3 == diag.voltage
    assert 4 == diag.avg_voltage
    assert 5 == diag.current
    assert 6 == diag.avg_current
    assert 7 == diag.full_cap
    assert 8 == diag.rep_cap
    assert 9 == diag.repsoc
    assert 10 == diag.vfsoc


def test_decode_generic_message() -> None:
    msg = codec.decode_message(bytes.fromhex("bb0b35010000000200000003000400050006000700080009000A00"))
    assert isinstance(msg, codec.BatteryDiagnostics)
    assert 24 == msg.length()
    assert 24 == codec.BatteryDiagnostics.default_length()

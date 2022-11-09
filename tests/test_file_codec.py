from embodycodec import file_codec as codec


def test_decode_header() -> None:
    assert 21 == codec.Header.length()
    header = codec.Header.decode(
        bytes.fromhex("65c6fa2569b1633302040106710000017e5353729d")
    )
    assert b"\x02" == header.fw_att
    assert b"\x04\x01\x06" == header.firmware_version
    assert (4, 1, 6) == tuple(header.firmware_version)
    assert b"q" == header.time_att
    assert 1642075484829 == header.current_time
    assert 7333824081813398323 == header.serial


def test_decode_timestamp() -> None:
    assert 10 == codec.Timestamp.length()
    timestamp = codec.Timestamp.decode(bytes.fromhex("00020000017e5353729d"))
    assert 2 == timestamp.two_lsb_of_timestamp
    assert 1642075484829 == timestamp.current_time


def test_decode_afe_settings_old() -> None:
    assert 37 == codec.AfeSettingsOld.length()


def test_decode_afe_settings() -> None:
    assert 22 == codec.AfeSettings.length()
    afe_settings = codec.AfeSettings.decode(
        bytes.fromhex("0002050204000000184900001849fff8ef66424f20d7")
    )
    assert 2 == afe_settings.two_lsb_of_timestamp
    assert 4 == afe_settings.ecg_gain
    assert 0 == afe_settings.ioffdac_range
    assert -463002 == afe_settings.off_dac
    assert 51.78207015991211 == afe_settings.relative_gain
    assert 6217 == afe_settings.led1
    assert 6217 == afe_settings.led4
    assert 2 == afe_settings.cf_value


def test_decode_afe_settings_all() -> None:
    assert 38 == codec.AfeSettingsAll.length()
    afe_settings = codec.AfeSettingsAll.decode(
        bytes.fromhex(
            "00020502040000001849000018490000184900001849fff8ef64fff8ef65fff8ef66424f20d7"
        )
    )
    assert 2 == afe_settings.two_lsb_of_timestamp
    assert 5 == afe_settings.rf_gain
    assert 2 == afe_settings.cf_value
    assert 4 == afe_settings.ecg_gain
    assert 0 == afe_settings.ioffdac_range
    assert 6217 == afe_settings.led1
    assert 6217 == afe_settings.led2
    assert 6217 == afe_settings.led3
    assert 6217 == afe_settings.led4
    assert -463004 == afe_settings.off_dac1
    assert -463003 == afe_settings.off_dac2
    assert -463002 == afe_settings.off_dac3
    assert 51.78207015991211 == afe_settings.relative_gain


def test_decode_ppg_raw() -> None:
    assert 8 == codec.PpgRaw.length()
    ppg_raw = codec.PpgRaw.decode(bytes.fromhex("00020002090357f7"))
    assert 2 == ppg_raw.two_lsb_of_timestamp
    assert 521 == ppg_raw.ecg
    assert 219127 == ppg_raw.ppg


def test_decode_ppg_raw_all() -> None:
    assert 14 == codec.PpgRawAll.length()
    ppg_raw = codec.PpgRawAll.decode(bytes.fromhex("00020002090357f70357f70357f7"))
    assert 2 == ppg_raw.two_lsb_of_timestamp
    assert 521 == ppg_raw.ecg
    assert 219127 == ppg_raw.ppg
    assert 219127 == ppg_raw.ppg_red
    assert 219127 == ppg_raw.ppg_ir


def test_decode_imu_raw() -> None:
    assert 14 == codec.ImuRaw.length()
    imu_raw = codec.ImuRaw.decode(bytes.fromhex("72a7010fc3eb137f002efff7ffdc"))
    assert 29351 == imu_raw.two_lsb_of_timestamp
    assert 271 == imu_raw.acc_x
    assert -15381 == imu_raw.acc_y
    assert 4991 == imu_raw.acc_z
    assert 46 == imu_raw.gyr_x
    assert -9 == imu_raw.gyr_y
    assert -36 == imu_raw.gyr_z


def test_decode_acc_raw() -> None:
    assert 8 == codec.AccRaw.length()
    acc_raw = codec.AccRaw.decode(bytes.fromhex("72a7010fc3eb137f"))
    assert 29351 == acc_raw.two_lsb_of_timestamp
    assert 271 == acc_raw.acc_x
    assert -15381 == acc_raw.acc_y
    assert 4991 == acc_raw.acc_z


def test_decode_gyro_raw() -> None:
    assert 8 == codec.GyroRaw.length()
    gyro_raw = codec.GyroRaw.decode(bytes.fromhex("72a7002efff7ffdc"))
    assert 29351 == gyro_raw.two_lsb_of_timestamp
    assert 46 == gyro_raw.gyr_x
    assert -9 == gyro_raw.gyr_y
    assert -36 == gyro_raw.gyr_z


def test_decode_imu() -> None:
    assert 3 == codec.Imu.length()
    imu = codec.Imu.decode(bytes.fromhex("72a705"))
    assert 29351 == imu.two_lsb_of_timestamp
    assert 5 == imu.orientation_and_activity


def test_battery_level() -> None:
    assert 3 == codec.BatteryLevel.length()
    level = codec.BatteryLevel.decode(bytes.fromhex("72a705"))
    assert 29351 == level.two_lsb_of_timestamp
    assert 5 == level.level


def test_heart_rate() -> None:
    assert 4 == codec.HeartRate.length()
    rate = codec.HeartRate.decode(bytes.fromhex("72a70005"))
    assert 29351 == rate.two_lsb_of_timestamp
    assert 5 == rate.rate


def test_heart_rate_interval() -> None:
    assert 4 == codec.HeartRateInterval.length()
    interval = codec.HeartRateInterval.decode(bytes.fromhex("72a70005"))
    assert 29351 == interval.two_lsb_of_timestamp
    assert 5 == interval.interval


def test_no_of_ppg_values() -> None:
    assert 3 == codec.NoOfPpgValues.length()
    vals = codec.NoOfPpgValues.decode(bytes.fromhex("72a703"))
    assert 29351 == vals.two_lsb_of_timestamp
    assert 3 == vals.ppg_values


def test_charge_state() -> None:
    assert 3 == codec.ChargeState.length()
    state = codec.ChargeState.decode(bytes.fromhex("72a703"))
    assert 29351 == state.two_lsb_of_timestamp
    assert 3 == state.state


def test_belt_on_body() -> None:
    assert 3 == codec.BeltOnBody.length()
    bob = codec.BeltOnBody.decode(bytes.fromhex("72a701"))
    assert 29351 == bob.two_lsb_of_timestamp
    assert 1 == bob.on_body


def test_temperature() -> None:
    assert 4 == codec.Temperature.length()
    temp = codec.Temperature.decode(bytes.fromhex("72a70C80"))
    assert 3200 == temp.temp_raw
    assert 25.0 == temp.temp_celsius()
    temp = codec.Temperature.decode(bytes.fromhex("72a7EC00"))
    assert -5120 == temp.temp_raw
    assert -40.0 == temp.temp_celsius()

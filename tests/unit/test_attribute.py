from unittest import TestCase
from src.embodycodec import attributes
from src.embodycodec import types
from datetime import datetime


class TestAttributes(TestCase):

    def test_encode_decode_serial_no(self):
        do_test_encode_decode_attribute(self, attributes.SerialNoAttribute(12345678),
                                        b'\x00\x00\x00\x00\x00\xbc\x61\x4e')

    def test_encode_decode_firmware_version(self):
        do_test_encode_decode_attribute(self, attributes.FirmwareVersionAttribute(12345678),
                                        b'\x00\x00\x00\x00\x00\xbc\x61\x4e')

    def test_encode_decode_bluetooth_mac(self):
        do_test_encode_decode_attribute(self, attributes.BluetoothMacAttribute(12345678),
                                        b'\x00\x00\x00\x00\x00\xbc\x61\x4e')

    def test_encode_decode_model(self):
        do_test_encode_decode_attribute(self, attributes.ModelAttribute('Aidee Embody'),
                                        b'\x41\x69\x64\x65\x65\x20\x45\x6d\x62\x6f\x64\x79\x00')

    def test_encode_decode_vendor(self):
        do_test_encode_decode_attribute(self, attributes.VendorAttribute('Aidee'),
                                        b'\x41\x69\x64\x65\x65\x00')

    def test_encode_decode_afe_settings(self):
        do_test_encode_decode_attribute(self, attributes.AfeSettingsAttribute(
            value=types.AfeSettings(ecg_gain=4, ioffdac_range=0, off_dac=-463002, relative_gain=51.78207015991211,
                                    rf_gain=2, led1=6217, led4=6217, cf_value=2)),
                                        b'\x02\x02\x04\x00\x00\x00\x18\x49\x00\x00\x18\x49\xff\xf8\xef\x66\x42\x4f\x20\xd7')

    def test_encode_decode_afe_settings_all(self):
        do_test_encode_decode_attribute(self, attributes.AfeSettingsAllAttribute(
            value=types.AfeSettingsAll(rf_gain=5, cf_value=2, ecg_gain=4, ioffdac_range=0, led1=6217, led2=6217,
                                       led3=6217, led4=6217, off_dac1=-463004, off_dac2=-463003, off_dac3=-463002,
                                       relative_gain=51.78207015991211)),
                                        b'\x05\x02\x04\x00\x00\x00\x18\x49\x00\x00\x18\x49\x00\x00\x18\x49\x00\x00\x18'
                                        b'\x49\xff\xf8\xef\x64\xff\xf8\xef\x65\xff\xf8\xef\x66\x42\x4f\x20\xd7')

    def test_encode_decode_current_time(self):
        do_test_encode_decode_attribute(self, attributes.CurrentTimeAttribute(
            int(datetime.fromisoformat('2022-04-20 00:05:25.283+00:00').timestamp() * 1000)),
                                        b'\x00\x00\x01\x80\x44\x49\xbe\xa3')

    def test_encode_decode_measurement_deactivated(self):
        do_test_encode_decode_attribute(self, attributes.MeasurementDeactivatedAttribute(1),
                                        b'\x01')

    def test_encode_decode_measurement_trace_level(self):
        do_test_encode_decode_attribute(self, attributes.TraceLevelAttribute(2),
                                        b'\x02')

    def test_encode_decode_measurement_trace_level(self):
        do_test_encode_decode_attribute(self, attributes.NoOfPpgValuesAttribute(3),
                                        b'\x03')

    def test_encode_decode_battery_level(self):
        do_test_encode_decode_attribute(self, attributes.BatteryLevelAttribute(3),
                                        b'\x03')

    def test_encode_decode_pulse_raw(self):
        do_test_encode_decode_attribute(self, attributes.PulseRawAttribute(value=types.PulseRaw(ecg=1, ppg=1000)),
                                        b'\x00\x00\x00\x01\x00\x00\x03\xe8')

    def test_encode_decode_pulse_raw_all(self):
        do_test_encode_decode_attribute(self, attributes.PulseRawAllAttribute(
            value=types.PulseRawAll(ecg=1, ppg_green=1000, ppg_red=100, ppg_ir=5)),
                                        b'\x00\x00\x00\x01\x00\x00\x03\xe8\x00\x00\x00\x64\x00\x00\x00\x05')

    def test_encode_decode_pulse_blood_pressure(self):
        do_test_encode_decode_attribute(self, attributes.BloodPressureAttribute(
            value=types.BloodPressure(sys=120, dia=80, bp_map=100, pat=78, pulse=55)),
                                        b'\x00\x78\x00\x50\x00\x64\x00\x00\x00\x4e\x00\x37')

    def test_encode_decode_imu(self):
        do_test_encode_decode_attribute(self, attributes.ImuAttribute(
            value=types.Imu(orientation_and_activity=5)),
                                        b'\x05')

    def test_encode_decode_heart_rate(self):
        do_test_encode_decode_attribute(self, attributes.HeartrateAttribute(value=55), b'\x00\x37')

    def test_encode_decode_sleep_mode(self):
        do_test_encode_decode_attribute(self, attributes.SleepModeAttribute(value=4), b'\x04')

    def test_encode_decode_breath_rate(self):
        do_test_encode_decode_attribute(self, attributes.BreathRateAttribute(value=16), b'\x10')

    def test_encode_decode_heart_rate_variability(self):
        do_test_encode_decode_attribute(self, attributes.HeartRateVariabilityAttribute(value=102), b'\x00\x66')

    def test_encode_decode_charge_state(self):
        decoded = do_test_encode_decode_attribute(self, attributes.ChargeStateAttribute(value=1), b'\x01')
        self.assertEqual(decoded.value, True)

    def test_encode_decode_belt_on_body_state(self):
        decoded = do_test_encode_decode_attribute(self, attributes.BeltOnBodyStateAttribute(value=0), b'\x00')
        self.assertEqual(decoded.value, False)

    def test_encode_decode_firmware_update_progress(self):
        do_test_encode_decode_attribute(self, attributes.FirmwareUpdateProgressAttribute(value=95), b'\x5f')

    def test_encode_decode_imu_raw(self):
        do_test_encode_decode_attribute(self, attributes.ImuRawAttribute(
            value=types.ImuRaw(acc_x=271, acc_y=-15381, acc_z=4991, gyr_x=46, gyr_y=-9, gyr_z=-36)),
                                        b'\x01\x0f\xc3\xeb\x13\x7f\x00\x2e\xff\xf7\xff\xdc')

    def test_encode_decode_heart_rate_interval(self):
        do_test_encode_decode_attribute(self, attributes.HeartRateIntervalAttribute(value=15), b'\x00\x0F')

    def test_encode_decode_pulse_raw(self):
        do_test_encode_decode_attribute(self, attributes.PulseRawAttribute(
            value=types.PulseRaw(ecg=1, ppg=1000)), b'\x00\x00\x00\x01\x00\x00\x03\xe8')

    def test_encode_decode_pulse_raw_all(self):
        do_test_encode_decode_attribute(self, attributes.PulseRawAllAttribute(
            value=types.PulseRawAll(ecg=1, ppg_green=1000, ppg_red=100, ppg_ir=5)), b'\x00\x00\x00\x01\x00\x00\x03\xe8\x00\x00\x00\x64\x00\x00\x00\x05')

    def test_encode_decode_acc_raw(self):
        do_test_encode_decode_attribute(self, attributes.AccRawAttribute(
            value=types.AccRaw(acc_x=271, acc_y=-15381, acc_z=4991)), b'\x01\x0f\xc3\xeb\x13\x7f')

    def test_encode_decode_gyro_raw(self):
        do_test_encode_decode_attribute(self, attributes.GyroRawAttribute(
            value=types.GyroRaw(gyr_x=46, gyr_y=-9, gyr_z=-36)),
                                        b'\x00\x2e\xff\xf7\xff\xdc')

    def test_encode_decode_temperature(self):
        decoded = do_test_encode_decode_attribute(self, attributes.TemperatureAttribute(value=3200),
                                                  b'\x0C\x80')
        self.assertEqual(decoded.temp_celsius(), 25.0)
        decoded = do_test_encode_decode_attribute(self, attributes.TemperatureAttribute(value=-5120),
                                                  b'\xEC\x00')
        self.assertEqual(decoded.temp_celsius(), -40.0)

    def test_encode_decode_diagnostics(self):
        do_test_encode_decode_attribute(self, attributes.DiagnosticsAttribute(
            value=types.Diagnostics(rep_soc=9173, avg_current=-375, rep_cap=29350, full_cap=32000, 
            tte=281278112, ttf=368634368, voltage=406125, avg_voltage=406039)),
            b'#\xd5\xfe\x89r\xa6}\x00\x10\xc3\xf6\xa0\x15\xf8\xea\x00\x00\x062m\x00\x062\x17')


def do_test_encode_decode_attribute(test_case: TestCase, attribute: attributes.Attribute, expected_encoded: bytes):
    encoded = attribute.encode()
    print(encoded.hex())
    test_case.assertEqual(encoded, expected_encoded)
    decoded = attributes.decode_attribute(attribute.attribute_id, encoded)
    test_case.assertIsInstance(decoded, type(attribute))
    test_case.assertEqual(decoded.value, attribute.value)
    test_case.assertEqual(decoded.attribute_id, attribute.attribute_id)
    return decoded

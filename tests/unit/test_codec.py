from unittest import TestCase
from src.embodycodec import codec
from datetime import datetime
from src.embodycodec import attributes
from src.embodycodec import types


class TestCodec(TestCase):
    def test_decode_heartbeat(self):
        message = b'\x01\x00\x05\xAB\x09'
        heartbeat = codec.decode(message)
        self.assertIsNotNone(heartbeat)
        self.assertEqual(heartbeat.length, 5)
        self.assertEqual(heartbeat.crc, 43785)

    def test_encode_heartbeat(self):
        heartbeat = codec.Heartbeat()
        self.assertEqual(heartbeat.encode(), b'\x01\x00\x05\xAB\x09')

    def test_heartbeat_response(self):
        heartbeat_response = codec.HeartbeatResponse()
        encoded = heartbeat_response.encode()
        self.assertEqual(encoded, b'\x81\x00\x05\x90\x53')
        decoded = codec.decode(encoded)
        self.assertEqual(decoded.length, 5)
        self.assertIsInstance(decoded, codec.HeartbeatResponse)

    def test_nack_response(self):
        nack_response = codec.NackResponse(0x02)
        encoded = nack_response.encode()
        self.assertEqual(encoded, b'\x82\x00\x06\x02\x3E\x74')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.NackResponse)
        self.assertEqual(decoded.length, 6)
        self.assertEqual(decoded.response_code, 0x02)
        self.assertEqual(decoded.error_message(), 'Unknown message content')
        decoded.response_code = None
        self.assertIsNone(decoded.error_message())
        decoded.response_code = 0xFF
        self.assertIsNone(decoded.error_message())

    def test_set_attribute(self):
        response = codec.SetAttribute(attribute_id=attributes.TemperatureAttribute.attribute_id,
                                      value=attributes.TemperatureAttribute(3200))
        encoded = response.encode()
        self.assertEqual(encoded, b'\x11\x00\x09\xb4\x02\x0c\x80\x57\x0d')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.SetAttribute)
        self.assertEqual(decoded.length, 9)
        self.assertEqual(decoded, response)

    def test_set_attribute_response(self):
        response = codec.SetAttributeResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x91\x00\x05\xD3\x30')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.SetAttributeResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_decode_get_attribute(self):
        message = b'\x12\x00\x06\xA1\x7D\x62'
        get_attribute = codec.decode(message)
        self.assertIsNotNone(get_attribute)
        self.assertEqual(get_attribute.length, 6)
        self.assertEqual(0xA1, get_attribute.attribute_id)
        self.assertEqual(get_attribute.crc, 32098)

    def test_encode_get_attribute(self):
        get_attribute = codec.GetAttribute(0xA1)
        self.assertEqual(get_attribute.encode(), b'\x12\x00\x06\xA1\x7D\x62')

    def test_get_attribute_response_current_time(self):
        decoded = do_test_get_attribute_response_and_return_decoded(self, attributes.CurrentTimeAttribute(
            int(datetime.fromisoformat('2022-04-20 00:05:25.283+00:00').timestamp() * 1000)),
                                                                    b'\x92\x00\x1a\x71\x00\x00\x01\x80\x44\x49\xb6\xd3'
                                                                    b'\x00\x01\x02\x08\x00\x00\x01\x80\x44\x49\xbe\xa3'
                                                                    b'\xdf\x03')

    def test_get_attribute_response_serial_no(self):
        decoded = do_test_get_attribute_response_and_return_decoded(self, attributes.SerialNoAttribute(12345678),
                                                                    b'\x92\x00\x1a\x01\x00\x00\x01\x80\x44\x49\xb6\xd3'
                                                                    b'\x00\x01\x02\x08\x00\x00\x00\x00\x00\xbc\x61\x4e'
                                                                    b'\xa5\x26')
        self.assertEqual(decoded.value.value, 12345678)

    def test_reset_attribute(self):
        response = codec.ResetAttribute(0xA1)
        encoded = response.encode()
        self.assertEqual(encoded, b'\x13\x00\x06\xa1\x0b\xd6')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ResetAttribute)
        self.assertEqual(decoded.length, 6)
        self.assertEqual(decoded, response)

    def test_reset_attribute_response(self):
        response = codec.ResetAttributeResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x93\x00\x05\xBD\x50')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ResetAttributeResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_configure_reporting(self):
        response = codec.ConfigureReporting(attribute_id=0x71, reporting=types.Reporting(interval=50, on_change=1))
        encoded = response.encode()
        self.assertEqual(encoded, b'\x14\x00\x09\x71\x00\x32\x01\xe8\x18')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ConfigureReporting)
        self.assertEqual(decoded.length, 9)
        self.assertEqual(decoded, response)

    def test_configure_reporting_response(self):
        response = codec.ConfigureReportingResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x94\x00\x05\x38\xC0')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ConfigureReportingResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_reset_reporting(self):
        response = codec.ResetReporting(attribute_id=0xA1)
        encoded = response.encode()
        self.assertEqual(encoded, b'\x15\x00\x06\xA1\x2C\x4F')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ResetReporting)
        self.assertEqual(decoded.length, 6)
        self.assertEqual(decoded, response)

    def test_reset_reporting_response(self):
        response = codec.ResetReportingResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x95\x00\x05\x0F\xF0')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ResetReportingResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_periodic_recording(self):
        response = codec.PeriodicRecording(
            types.Recording(day_start=0, day_end=23, day_interval=15, night_interval=20, recording_start=1,
                            recording_stop=2))
        encoded = response.encode()
        self.assertEqual(encoded, b'\x16\x00\x0b\x00\x17\x0f\x14\x01\x02\x61\x9b')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.PeriodicRecording)
        self.assertEqual(decoded.length, 11)
        self.assertEqual(decoded, response)

    def test_periodic_recording_response(self):
        response = codec.PeriodicRecordingResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x96\x00\x05\x56\xA0')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.PeriodicRecordingResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_attribute_changed(self):
        response = codec.AttributeChanged(
            changed_at=int(datetime.fromisoformat('2022-04-20 00:05:23.283+00:00').timestamp() * 1000),
            attribute_id=attributes.BatteryLevelAttribute.attribute_id, value=attributes.BatteryLevelAttribute(50))
        encoded = response.encode()
        self.assertEqual(encoded, b'\x21\x00\x10\x00\x00\x01\x80\x44\x49\xb6\xd3\xa1\x01\x32\x2f\x06')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.AttributeChanged)
        self.assertEqual(decoded.length, 16)
        self.assertEqual(decoded, response)

    def test_attribute_changed_response(self):
        response = codec.AttributeChangedResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xA1\x00\x05\x16\x95')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.AttributeChangedResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_raw_pulse_changed(self):
        response = codec.RawPulseChanged(
            changed_at=1,
            value=types.PulseRaw(ecg=43214321, ppg=123456789))
            # value=types.PulseRawAll(ecg=43214321, ppg_green=123456789, ppg_red=987654321, ppg_ir=432198765))
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'"\x00\x0f\x00\x01\x02\x93e\xf1\x07[\xcd\x15p\x84')
        # self.assertEqual(encoded,
        #                  b'\x22\x00\x17\x00\x01\x02\x93\x65\xF1\x07\x5B\xCD\x15\x3A\xDE\x68\xB1\x19\xC2\xD4\x6D\xCC\x8C')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.RawPulseChanged)
        self.assertEqual(decoded.length, 15)
        self.assertEqual(decoded, response)

    def test_raw_pulse_changed_response(self):
        response = codec.RawPulseChangedResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xA2\x00\x05\x4F\xC5')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.RawPulseChangedResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_alarm(self):
        response = codec.Alarm(
            changed_at=int(datetime.fromisoformat('2022-04-20 00:05:23.283+00:00').timestamp() * 1000), alarm_type=1)
        encoded = response.encode()
        self.assertEqual(encoded, b'\x31\x00\x0e\x00\x00\x01\x80\x44\x49\xb6\xd3\x01\x92\x46')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.Alarm)
        self.assertEqual(decoded.length, 14)
        self.assertEqual(decoded, response)

    def test_alarm_response(self):
        response = codec.AlarmResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xB1\x00\x05\x55\xF6')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.AlarmResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_list_files(self):
        response = codec.ListFiles()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x41\x00\x05\xB6\xA4')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ListFiles)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_list_files_response_empty_list(self):
        response = codec.ListFilesResponse(files=[])
        encoded = response.encode()
        self.assertEqual(encoded, b'\xc1\x00\x05\x8d\xfe')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ListFilesResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_list_files_response_one_file(self):
        response = codec.ListFilesResponse(files=[])
        response.files.append(types.FileWithLength(file_name='test1.bin', file_size=0))
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'\xc1\x00\x23\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe5\xc4')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ListFilesResponse)
        self.assertEqual(decoded.length, 35)
        self.assertEqual(decoded, response)

    def test_list_files_response_one_file_with_invalid_byte(self):
        encoded = bytes([0xc1, 0x0, 0x23, 0x32, 0x32, 0x30, 0x35, 0x30, 0x35, 0x5f, 0x31, 0x30, 0x31, 0x36, 
                         0x5f, 0x30, 0x30, 0x30, 0x31, 0x32, 0x38, 0x2e, 0x6c, 0x6f, 0x67, 0x0, 0xf9, 0x3a, 
                         0x83, 0x0, 0x5f, 0x1b, 0x7, 0xc0, 0xb4])
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ListFilesResponse)
        self.assertEqual(decoded.length, 35)

    def test_list_files_response_two_separate_files(self):
        encoded = bytes([0xc1, 0x0, 0x23, 0x32, 0x32, 0x30, 0x35, 0x31, 0x30, 0x5f, 0x31, 0x34, 0x33, 0x39, 0x5f, 
                   0x30, 0x30, 0x30, 0x30, 0x30, 0x33, 0x2e, 0x6c, 0x6f, 0x67, 0x0, 0x0, 0x0, 0x0, 0x0, 0x73, 
                   0x88, 0xb3, 0xa2, 0xe5, 0xc1, 0x0, 0x23, 0x34, 0x30, 0x34, 0x30, 0x34, 0x30, 0x5f, 0x39, 
                   0x39, 0x39, 0x39, 0x5f, 0x30, 0x30, 0x30, 0x30, 0x2e, 0x6c, 0x6f, 0x67, 0x0, 0x67, 0x0, 0x0, 
                   0x0, 0x0, 0x0, 0x0, 0x0, 0x2, 0x64, 0x40])
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ListFilesResponse)
        self.assertEqual(decoded.length, 35)

    def test_list_files_response_two_files(self):
        response = codec.ListFilesResponse(files=[])
        response.files.append(types.FileWithLength(file_name='test1.bin', file_size=0))
        response.files.append(types.FileWithLength(file_name='test2.bin', file_size=0))
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'\xc1\x00\x41\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x74\x65\x73\x74\x32\x2e\x62\x69\x6e\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf2\x2e')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ListFilesResponse)
        self.assertEqual(decoded.length, 65)
        self.assertEqual(decoded, response)

        # Empty list
        response = codec.ListFilesResponse(files=[])
        encoded = response.encode()
        self.assertEqual(encoded, b'\xc1\x00\x05\x8d\xfe')
        decoded = codec.decode(encoded)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_decode_list_files_response_eight_files(self):
        decoded = codec.decode(b'\xc1\x00\xf5\x32\x32\x30\x34\x30\x36\x5f\x31\x32\x33\x38\x5f\x30\x30\x30\x30\x36\x37'
                               b'\x2e\x6c\x6f\x67\x00\x00\x00\x00\x00\x09\x64\x63\x32\x32\x30\x34\x30\x36\x5f\x31\x32'
                               b'\x34\x38\x5f\x30\x30\x30\x30\x36\x38\x2e\x6c\x6f\x67\x00\x00\x00\x00\x00\x04\x80\x57'
                               b'\x32\x32\x30\x34\x32\x32\x5f\x30\x38\x32\x38\x5f\x30\x30\x30\x30\x36\x39\x2e\x6c\x6f'
                               b'\x67\x00\x00\x00\x00\x02\x61\x89\x0a\x32\x32\x30\x34\x32\x32\x5f\x30\x39\x32\x38\x5f'
                               b'\x30\x30\x30\x30\x37\x30\x2e\x6c\x6f\x67\x00\x00\x00\x00\x02\x61\x87\x6b\x32\x32\x30'
                               b'\x34\x32\x32\x5f\x31\x30\x32\x38\x5f\x30\x30\x30\x30\x37\x31\x2e\x6c\x6f\x67\x00\x00'
                               b'\x00\x00\x02\x61\x94\xa6\x32\x32\x30\x34\x32\x32\x5f\x31\x31\x32\x38\x5f\x30\x30\x30'
                               b'\x30\x37\x32\x2e\x6c\x6f\x67\x00\x00\x00\x00\x02\x61\x87\x6f\x32\x32\x30\x34\x32\x32'
                               b'\x5f\x31\x32\x32\x38\x5f\x30\x30\x30\x30\x37\x33\x2e\x6c\x6f\x67\x00\x00\x00\x00\x02'
                               b'\x61\x73\x31\x32\x32\x30\x34\x32\x32\x5f\x31\x33\x32\x38\x5f\x30\x30\x30\x30\x37\x34'
                               b'\x2e\x6c\x6f\x67\x00\x00\x00\x00\x01\x2d\x6a\x5b\x83\xbc')
        self.assertEqual(decoded.files[0], types.FileWithLength(file_name='220406_1238_000067.log', file_size=615523))
        self.assertEqual(decoded.files[1], types.FileWithLength(file_name='220406_1248_000068.log', file_size=294999))
        self.assertEqual(decoded.length, 245)
        self.assertEqual(len(decoded.files), 8)

    def test_get_file(self):
        response = codec.GetFile(file=types.File(file_name='test1.bin'))
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'\x42\x00\x1f\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\xd4\xf8')
        self.assertEqual(3+26+2, len(encoded))
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.GetFile)
        self.assertEqual(decoded.length, 31)
        self.assertEqual(decoded, response)

    def test_get_file_response(self):
        response = codec.GetFileResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xC2\x00\x05\xD4\xAE')
        decoded = codec.decode(encoded)
        self.assertEqual(decoded.length, 5)
        self.assertIsInstance(decoded, codec.GetFileResponse)

    def test_send_file(self):
        response = codec.SendFile(file_name=types.File(file_name='test1.bin'), index=1, total_parts=2, payload=b'\x01')
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'\x43\x00\x24\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x64\x6e')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.SendFile)
        self.assertEqual(decoded.length, 36)
        self.assertEqual(decoded, response)

    def test_send_file_response(self):
        response = codec.SendFileResponse(9)
        encoded = response.encode()
        self.assertEqual(encoded, b'\xc3\x00\x07\x00\t\xd8\xdf')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.SendFileResponse)
        self.assertEqual(decoded.length, 7)

    def test_delete_file(self):
        response = codec.DeleteFile(types.File('test1.bin'))
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'\x44\x00\x1f\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\xd6\xee')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.DeleteFile)
        self.assertEqual(decoded.length, 31)
        self.assertEqual(decoded, response)

    def test_delete_file_response(self):
        response = codec.DeleteFileResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xC4\x00\x05\x66\x0E')
        decoded = codec.decode(encoded)
        self.assertEqual(decoded.length, 5)
        self.assertIsInstance(decoded, codec.DeleteFileResponse)

    def test_get_file_uart_file(self):
        response = codec.GetFileUart(types.File('test1.bin'))
        encoded = response.encode()
        self.assertEqual(encoded,
                         b'\x45\x00\x1f\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00'
                         b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x26\x08')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.GetFileUart)
        self.assertEqual(decoded.length, 31)
        self.assertEqual(decoded, response)

    def test_get_file_uart_response(self):
        response = codec.GetFileUartResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xC5\x00\x05\x51\x3E')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.GetFileUartResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_reformat_disk(self):
        response = codec.ReformatDisk()
        encoded = response.encode()
        self.assertEqual(encoded, b'\x47\x00\x05\x04\x04')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ReformatDisk)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_reformat_disk_response(self):
        response = codec.ReformatDiskResponse()
        encoded = response.encode()
        self.assertEqual(encoded, b'\xc7\x00\x05\x3f\x5e')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ReformatDiskResponse)
        self.assertEqual(decoded.length, 5)
        self.assertEqual(decoded, response)

    def test_execute_command(self):
        response = codec.ExecuteCommand(1, None)
        encoded = response.encode()
        self.assertEqual(encoded, b'\x51\x00\x06\x01\x3D\xC8')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ExecuteCommand)
        self.assertEqual(decoded.length, 6)
        self.assertEqual(decoded, response)

    def test_execute_command_response(self):
        response = codec.ExecuteCommandResponse(1, None)
        encoded = response.encode()
        self.assertEqual(encoded, b'\xd1\x00\x06\x01\xe0\xf0')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.ExecuteCommandResponse)
        self.assertEqual(decoded.length, 6)
        self.assertEqual(decoded, response)


# helper method for get_attribute_response tests
def do_test_get_attribute_response_and_return_decoded(case: TestCase, attribute: attributes.Attribute,
                                                      expected_encoded: bytes):
    get_attribute_response = codec.GetAttributeResponse(attribute_id=attribute.attribute_id,
                                                        changed_at=int(datetime.fromisoformat(
                                                            '2022-04-20 00:05:23.283+00:00').timestamp() * 1000),
                                                        reporting=types.Reporting(interval=1, on_change=2),
                                                        value=attribute)
    expected_encoded_header = b'\x92\x00\x1a\x01\x00\x00\x01\x80\x44\x49\xb6\xd3\x00\x01\x02'
    encoded = get_attribute_response.encode()
    case.assertEqual(encoded, expected_encoded)
    decoded = codec.decode(encoded)
    case.assertIsInstance(decoded, codec.GetAttributeResponse)
    case.assertEqual(decoded.attribute_id, get_attribute_response.attribute_id)
    case.assertEqual(decoded.changed_at, get_attribute_response.changed_at)
    case.assertEqual(decoded.value, get_attribute_response.value)
    case.assertEqual(decoded.reporting, get_attribute_response.reporting)
    return decoded

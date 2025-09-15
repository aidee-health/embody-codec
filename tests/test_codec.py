import struct
from datetime import datetime

import pytest

from embodycodec import attributes
from embodycodec import codec
from embodycodec import types
from embodycodec.exceptions import CrcError


def test_decode_empty_buffer():
    """Test decode function with empty buffer."""
    with pytest.raises(BufferError, match="No data provided!"):
        codec.decode(b"")


def test_decode_buffer_too_short():
    """Test decode function with buffer that's too short for header."""
    with pytest.raises(BufferError, match="Buffer too short for message"):
        codec.decode(b"\x01\x00")


def test_decode_buffer_too_short_for_decoding():
    """Test decode function with buffer that's too short for full message."""
    with pytest.raises(BufferError, match="Buffer too short for decoding"):
        codec.decode(b"\x01\x00\x10\x00")


def test_decode_unknown_message_type():
    """Test decode function with unknown message type."""
    # Create a message with unknown type but valid length and CRC
    message = bytearray(b"\xff\x00\x05\x00\x00")
    # Calculate and set valid CRC
    crc = codec.crc16(message[0:3])
    message[3:5] = struct.pack(">H", crc)

    with pytest.raises(LookupError, match="Unknown message type 0xff"):
        codec.decode(bytes(message))


def test_decode_invalid_crc():
    """Test decode function with invalid CRC."""
    with pytest.raises(CrcError, match="CRC error"):
        # Heartbeat message with invalid CRC
        codec.decode(b"\x01\x00\x05\x00\x00")


def test_decode_accept_crc_error():
    """Test decode function with accept_crc_error parameter."""
    # Create a message with known bad CRC
    message = bytearray(b"\x01\x00\x05")  # Heartbeat message
    message += b"\xaa\xbb"  # Bad CRC values

    # Should raise CRC error when not accepting CRC errors
    with pytest.raises(CrcError):
        codec.decode(message, accept_crc_error=False)

    # Should successfully decode when accepting CRC errors
    result = codec.decode(message, accept_crc_error=True)
    assert isinstance(result, codec.Heartbeat)
    assert result.length == 5


def test_decode_decoding_exception():
    """Test decode function when actual message decoding fails."""
    # Create a message with valid type and CRC but malformed content
    message = bytearray(b"\x11\x00\x09\x01\x01\x00\x00\x00")
    # Calculate and set valid CRC
    crc = codec.crc16(message[0:6])
    message[6:8] = struct.pack(">H", crc)

    with pytest.raises(
        BufferError,
        match="Buffer too short for decoding type 0x11: Received 8 bytes, required 9 bytes",
    ):
        codec.decode(bytes(message))


def test_decode_heartbeat() -> None:
    message = b"\x01\x00\x05\xab\x09"
    heartbeat = codec.decode(message)
    assert heartbeat is not None
    assert heartbeat.length == 5
    assert heartbeat.crc == 43785


def test_encode_heartbeat() -> None:
    heartbeat = codec.Heartbeat()
    assert heartbeat.encode() == b"\x01\x00\x05\xab\x09"


def test_heartbeat_response() -> None:
    heartbeat_response = codec.HeartbeatResponse()
    encoded = heartbeat_response.encode()
    assert encoded == b"\x81\x00\x05\x90\x53"
    decoded = codec.decode(encoded)
    assert decoded.length == 5
    assert isinstance(decoded, codec.HeartbeatResponse)


def test_nack_response() -> None:
    nack_response = codec.NackResponse(0x02)
    encoded = nack_response.encode()
    assert encoded == b"\x82\x00\x06\x02\x3e\x74"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.NackResponse)
    assert decoded.length == 6
    assert decoded.response_code == 0x02
    assert decoded.error_message() == "Unknown message content"
    decoded.response_code = 0xFF
    assert decoded.error_message() is None


def test_set_attribute() -> None:
    response = codec.SetAttribute(
        attribute_id=attributes.TemperatureAttribute.attribute_id,
        value=attributes.TemperatureAttribute(3200),
    )
    encoded = response.encode()
    assert encoded == b"\x11\x00\x09\xb4\x02\x0c\x80\x57\x0d"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SetAttribute)
    assert decoded.length == 9
    assert decoded == response


def test_set_attribute_response() -> None:
    response = codec.SetAttributeResponse()
    encoded = response.encode()
    assert encoded == b"\x91\x00\x05\xd3\x30"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SetAttributeResponse)
    assert decoded.length == 5
    assert decoded == response


def test_set_attribute_response_in_stream_of_messages() -> None:
    encoded = b"\x91\x00\x05\xd30\x94\x00\x058\xc0"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SetAttributeResponse)
    assert decoded.length == 5


def test_decode_get_attribute() -> None:
    message = b"\x12\x00\x06\xa1\x7d\x62"
    get_attribute = codec.decode(message)
    assert get_attribute is not None
    assert isinstance(get_attribute, codec.GetAttribute)
    assert get_attribute.length == 6
    assert 0xA1 == get_attribute.attribute_id
    assert get_attribute.crc == 32098


def test_encode_get_attribute() -> None:
    get_attribute = codec.GetAttribute(0xA1)
    assert get_attribute.encode() == b"\x12\x00\x06\xa1\x7d\x62"


def test_get_attribute_response_current_time() -> None:
    do_test_get_attribute_response_and_return_decoded(
        attributes.CurrentTimeAttribute(
            int(datetime.fromisoformat("2022-04-20 00:05:25.283+00:00").timestamp() * 1000)
        ),
        b"\x92\x00\x1a\x71\x00\x00\x01\x80\x44\x49\xb6\xd3\x00\x01\x02\x08\x00\x00\x01\x80\x44\x49\xbe\xa3\xdf\x03",
    )


def test_get_attribute_response_system_status_names() -> None:
    do_test_get_attribute_response_and_return_decoded(
        attributes.SystemStatusNamesAttribute(["AFE", "IMU", "TEMP"]),
        b"\x92\x00\x1e\x08\x00\x00\x01\x80\x44\x49\xb6\xd3\x00\x01\x02\x0cAFE,IMU,TEMP\x53\x5a",
    )


def test_get_attribute_response_serial_no() -> None:
    decoded = do_test_get_attribute_response_and_return_decoded(
        attributes.SerialNoAttribute(12345678),
        b"\x92\x00\x1a\x01\x00\x00\x01\x80\x44\x49\xb6\xd3\x00\x01\x02\x08\x00\x00\x00\x00\x00\xbc\x61\x4e\xa5\x26",
    )
    assert decoded.value.value == 12345678


def test_reset_attribute() -> None:
    response = codec.ResetAttribute(0xA1)
    encoded = response.encode()
    assert encoded == b"\x13\x00\x06\xa1\x0b\xd6"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ResetAttribute)
    assert decoded.length == 6
    assert decoded == response


def test_reset_attribute_response() -> None:
    response = codec.ResetAttributeResponse()
    encoded = response.encode()
    assert encoded == b"\x93\x00\x05\xbd\x50"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ResetAttributeResponse)
    assert decoded.length == 5
    assert decoded == response


def test_configure_reporting() -> None:
    response = codec.ConfigureReporting(attribute_id=0x71, reporting=types.Reporting(interval=50, on_change=1))
    encoded = response.encode()
    assert encoded == b"\x14\x00\x09\x71\x00\x32\x01\xe8\x18"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ConfigureReporting)
    assert decoded.length == 9
    assert decoded == response


def test_configure_reporting_response() -> None:
    response = codec.ConfigureReportingResponse()
    encoded = response.encode()
    assert encoded == b"\x94\x00\x05\x38\xc0"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ConfigureReportingResponse)
    assert decoded.length == 5
    assert decoded == response


def test_reset_reporting() -> None:
    response = codec.ResetReporting(attribute_id=0xA1)
    encoded = response.encode()
    assert encoded == b"\x15\x00\x06\xa1\x2c\x4f"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ResetReporting)
    assert decoded.length == 6
    assert decoded == response


def test_reset_reporting_response() -> None:
    response = codec.ResetReportingResponse()
    encoded = response.encode()
    assert encoded == b"\x95\x00\x05\x0f\xf0"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ResetReportingResponse)
    assert decoded.length == 5
    assert decoded == response


def test_periodic_recording() -> None:
    response = codec.PeriodicRecording(
        types.Recording(
            day_start=0,
            day_end=23,
            day_interval=15,
            night_interval=20,
            recording_start=1,
            recording_stop=2,
        )
    )
    encoded = response.encode()
    assert encoded == b"\x16\x00\x0b\x00\x17\x0f\x14\x01\x02\x61\x9b"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.PeriodicRecording)
    assert decoded.length == 11
    assert decoded == response


def test_periodic_recording_response() -> None:
    response = codec.PeriodicRecordingResponse()
    encoded = response.encode()
    assert encoded == b"\x96\x00\x05\x56\xa0"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.PeriodicRecordingResponse)
    assert decoded.length == 5
    assert decoded == response


def test_attribute_changed() -> None:
    response = codec.AttributeChanged(
        changed_at=int(datetime.fromisoformat("2022-04-20 00:05:23.283+00:00").timestamp() * 1000),
        attribute_id=attributes.BatteryLevelAttribute.attribute_id,
        value=attributes.BatteryLevelAttribute(50),
    )
    encoded = response.encode()
    assert encoded == b"\x21\x00\x10\x00\x00\x01\x80\x44\x49\xb6\xd3\xa1\x01\x32\x2f\x06"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.AttributeChanged)
    assert decoded.length == 16
    assert decoded == response


def test_attribute_changed_response() -> None:
    response = codec.AttributeChangedResponse()
    encoded = response.encode()
    assert encoded == b"\xa1\x00\x05\x16\x95"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.AttributeChangedResponse)
    assert decoded.length == 5
    assert decoded == response


def test_raw_pulse_changed_1_ppg() -> None:
    response = codec.RawPulseChanged(changed_at=1, value=types.PulseRaw(ecg=43214321, ppg=123456789))
    encoded = response.encode()
    assert encoded == b'"\x00\x0f\x00\x01\x02\x93e\xf1\x07[\xcd\x15p\x84'
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.RawPulseChanged)
    assert decoded.length == 15
    assert decoded == response


def test_raw_pulse_changed_3_ppgs() -> None:
    response = codec.RawPulseChanged(
        changed_at=1,
        value=types.PulseRawAll(ecg=43214321, ppg_green=123456789, ppg_red=987654321, ppg_ir=432198765),
    )
    encoded = response.encode()
    assert encoded == bytes.fromhex("2200170001029365f1075bcd153ade68b119c2d46dcc8c")
    print(encoded.hex())
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.RawPulseChanged)
    assert decoded.length == 23
    assert decoded == response


def test_raw_pulse_changed_response() -> None:
    response = codec.RawPulseChangedResponse()
    encoded = response.encode()
    assert encoded == b"\xa2\x00\x05\x4f\xc5"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.RawPulseChangedResponse)
    assert decoded.length == 5
    assert decoded == response


def test_raw_pulse_list_changed() -> None:
    response = codec.RawPulseListChanged(
        attribute_id=attributes.PulseRawListAttribute.attribute_id,
        value=attributes.PulseRawListAttribute(
            value=types.PulseRawList(
                tick=843,
                format=3,
                no_of_ecgs=1,
                no_of_ppgs=3,
                ecgs=[12345678],
                ppgs=[87654321, 11223344, 88776655],
            )
        ),
    )
    encoded = response.encode()
    assert encoded == bytes.fromhex("240019b64b03374e61bc00b17f39053041ab00cf9f4a054e53")
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.RawPulseListChanged)
    assert decoded.length == 25
    assert decoded == response


def test_raw_pulse_list_changed_response() -> None:
    response = codec.RawPulseListChangedResponse()
    encoded = response.encode()
    assert encoded == b"\xa4\x00\x05\xfde"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.RawPulseListChangedResponse)
    assert decoded.length == 5
    assert decoded == response


def test_alarm() -> None:
    response = codec.Alarm(
        changed_at=int(datetime.fromisoformat("2022-04-20 00:05:23.283+00:00").timestamp() * 1000),
        alarm_type=1,
    )
    encoded = response.encode()
    assert encoded == b"\x31\x00\x0e\x00\x00\x01\x80\x44\x49\xb6\xd3\x01\x92\x46"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.Alarm)
    assert decoded.length == 14
    assert decoded == response


def test_alarm_response() -> None:
    response = codec.AlarmResponse()
    encoded = response.encode()
    assert encoded == b"\xb1\x00\x05\x55\xf6"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.AlarmResponse)
    assert decoded.length == 5
    assert decoded == response


def test_list_files() -> None:
    response = codec.ListFiles()
    encoded = response.encode()
    assert encoded == b"\x41\x00\x05\xb6\xa4"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ListFiles)
    assert decoded.length == 5
    assert decoded == response


def test_list_files_response_empty_list() -> None:
    response = codec.ListFilesResponse(files=[])
    encoded = response.encode()
    assert encoded == b"\xc1\x00\x05\x8d\xfe"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ListFilesResponse)
    assert decoded.length == 5
    assert decoded == response


def test_list_files_response_one_file() -> None:
    response = codec.ListFilesResponse(files=[])
    response.files.append(types.FileWithLength(file_name="test1.bin", file_size=0))
    encoded = response.encode()
    assert (
        encoded == b"\xc1\x00\x23\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe5\xc4"
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ListFilesResponse)
    assert decoded.length == 35
    assert decoded == response


def test_list_files_response_one_file_with_invalid_byte() -> None:
    encoded = bytes(
        [
            0xC1,
            0x0,
            0x23,
            0x32,
            0x32,
            0x30,
            0x35,
            0x30,
            0x35,
            0x5F,
            0x31,
            0x30,
            0x31,
            0x36,
            0x5F,
            0x30,
            0x30,
            0x30,
            0x31,
            0x32,
            0x38,
            0x2E,
            0x6C,
            0x6F,
            0x67,
            0x0,
            0xF9,
            0x3A,
            0x83,
            0x0,
            0x5F,
            0x1B,
            0x7,
            0xC0,
            0xB4,
        ]
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ListFilesResponse)
    assert decoded.length == 35


def test_list_files_response_two_separate_files() -> None:
    encoded = bytes(
        [
            0xC1,
            0x0,
            0x23,
            0x32,
            0x32,
            0x30,
            0x35,
            0x31,
            0x30,
            0x5F,
            0x31,
            0x34,
            0x33,
            0x39,
            0x5F,
            0x30,
            0x30,
            0x30,
            0x30,
            0x30,
            0x33,
            0x2E,
            0x6C,
            0x6F,
            0x67,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x73,
            0x88,
            0xB3,
            0xA2,
            0xE5,
            0xC1,
            0x0,
            0x23,
            0x34,
            0x30,
            0x34,
            0x30,
            0x34,
            0x30,
            0x5F,
            0x39,
            0x39,
            0x39,
            0x39,
            0x5F,
            0x30,
            0x30,
            0x30,
            0x30,
            0x2E,
            0x6C,
            0x6F,
            0x67,
            0x0,
            0x67,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x0,
            0x2,
            0x64,
            0x40,
        ]
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ListFilesResponse)
    assert decoded.length == 35


def test_list_files_response_two_files() -> None:
    response = codec.ListFilesResponse(files=[])
    response.files.append(types.FileWithLength(file_name="test1.bin", file_size=0))
    response.files.append(types.FileWithLength(file_name="test2.bin", file_size=0))
    encoded = response.encode()
    assert (
        encoded == b"\xc1\x00\x41\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x74\x65\x73\x74\x32\x2e\x62\x69\x6e\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf2\x2e"
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ListFilesResponse)
    assert decoded.length == 65
    assert decoded == response

    # Empty list
    response = codec.ListFilesResponse(files=[])
    encoded = response.encode()
    assert encoded == b"\xc1\x00\x05\x8d\xfe"
    decoded = codec.decode(encoded)
    assert decoded.length == 5
    assert decoded == response


def test_decode_list_files_response_eight_files() -> None:
    decoded = codec.decode(
        b"\xc1\x00\xf5\x32\x32\x30\x34\x30\x36\x5f\x31\x32\x33\x38\x5f\x30\x30\x30\x30\x36\x37"
        b"\x2e\x6c\x6f\x67\x00\x00\x00\x00\x00\x09\x64\x63\x32\x32\x30\x34\x30\x36\x5f\x31\x32"
        b"\x34\x38\x5f\x30\x30\x30\x30\x36\x38\x2e\x6c\x6f\x67\x00\x00\x00\x00\x00\x04\x80\x57"
        b"\x32\x32\x30\x34\x32\x32\x5f\x30\x38\x32\x38\x5f\x30\x30\x30\x30\x36\x39\x2e\x6c\x6f"
        b"\x67\x00\x00\x00\x00\x02\x61\x89\x0a\x32\x32\x30\x34\x32\x32\x5f\x30\x39\x32\x38\x5f"
        b"\x30\x30\x30\x30\x37\x30\x2e\x6c\x6f\x67\x00\x00\x00\x00\x02\x61\x87\x6b\x32\x32\x30"
        b"\x34\x32\x32\x5f\x31\x30\x32\x38\x5f\x30\x30\x30\x30\x37\x31\x2e\x6c\x6f\x67\x00\x00"
        b"\x00\x00\x02\x61\x94\xa6\x32\x32\x30\x34\x32\x32\x5f\x31\x31\x32\x38\x5f\x30\x30\x30"
        b"\x30\x37\x32\x2e\x6c\x6f\x67\x00\x00\x00\x00\x02\x61\x87\x6f\x32\x32\x30\x34\x32\x32"
        b"\x5f\x31\x32\x32\x38\x5f\x30\x30\x30\x30\x37\x33\x2e\x6c\x6f\x67\x00\x00\x00\x00\x02"
        b"\x61\x73\x31\x32\x32\x30\x34\x32\x32\x5f\x31\x33\x32\x38\x5f\x30\x30\x30\x30\x37\x34"
        b"\x2e\x6c\x6f\x67\x00\x00\x00\x00\x01\x2d\x6a\x5b\x83\xbc"
    )
    assert isinstance(decoded, codec.ListFilesResponse)
    assert decoded.files[0] == types.FileWithLength(file_name="220406_1238_000067.log", file_size=615523)
    assert decoded.files[1] == types.FileWithLength(file_name="220406_1248_000068.log", file_size=294999)
    assert decoded.length == 245
    assert len(decoded.files) == 8


def test_get_file() -> None:
    response = codec.GetFile(file=types.File(file_name="test1.bin"))
    encoded = response.encode()
    assert (
        encoded == b"\x42\x00\x1f\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\xd4\xf8"
    )
    assert (3 + 26 + 2) == len(encoded)
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.GetFile)
    assert decoded.length == 31
    assert decoded == response


def test_get_file_response() -> None:
    response = codec.GetFileResponse()
    encoded = response.encode()
    assert encoded == b"\xc2\x00\x05\xd4\xae"
    decoded = codec.decode(encoded)
    assert decoded.length == 5
    assert isinstance(decoded, codec.GetFileResponse)


def test_send_file() -> None:
    response = codec.SendFile(
        file_name=types.File(file_name="test1.bin"),
        index=1,
        total_parts=2,
        payload=b"\x01",
    )
    encoded = response.encode()
    assert (
        encoded == b"\x43\x00\x24\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x64\x6e"
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SendFile)
    assert decoded.length == 36
    assert decoded == response


def test_send_file_response() -> None:
    response = codec.SendFileResponse(9)
    encoded = response.encode()
    assert encoded == b"\xc3\x00\x07\x00\t\xd8\xdf"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SendFileResponse)
    assert decoded.length == 7


def test_delete_file() -> None:
    response = codec.DeleteFile(types.File("test1.bin"))
    encoded = response.encode()
    assert (
        encoded == b"\x44\x00\x1f\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\xd6\xee"
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.DeleteFile)
    assert decoded.length == 31
    assert decoded == response


def test_delete_file_response() -> None:
    response = codec.DeleteFileResponse()
    encoded = response.encode()
    assert encoded == b"\xc4\x00\x05\x66\x0e"
    decoded = codec.decode(encoded)
    assert decoded.length == 5
    assert isinstance(decoded, codec.DeleteFileResponse)


def test_get_file_uart_file() -> None:
    response = codec.GetFileUart(types.File("test1.bin"))
    encoded = response.encode()
    assert (
        encoded == b"\x45\x00\x1f\x74\x65\x73\x74\x31\x2e\x62\x69\x6e\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x26\x08"
    )
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.GetFileUart)
    assert decoded.length == 31
    assert decoded == response


def test_get_file_uart_response() -> None:
    response = codec.GetFileUartResponse()
    encoded = response.encode()
    assert encoded == b"\xc5\x00\x05\x51\x3e"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.GetFileUartResponse)
    assert decoded.length == 5
    assert decoded == response


def test_reformat_disk() -> None:
    response = codec.ReformatDisk()
    encoded = response.encode()
    assert encoded == b"\x47\x00\x05\x04\x04"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ReformatDisk)
    assert decoded.length == 5
    assert decoded == response


def test_reformat_disk_response() -> None:
    response = codec.ReformatDiskResponse()
    encoded = response.encode()
    assert encoded == b"\xc7\x00\x05\x3f\x5e"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ReformatDiskResponse)
    assert decoded.length == 5
    assert decoded == response


def test_execute_command() -> None:
    response = codec.ExecuteCommand(1, b"")
    encoded = response.encode()
    assert encoded == b"\x51\x00\x06\x01\x3d\xc8"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ExecuteCommand)
    assert decoded.length == 6


def test_execute_press_button_command() -> None:
    response = codec.ExecuteCommand(0x03, struct.pack(">BH", 1, 1000))
    encoded = response.encode()
    print(encoded.hex())
    assert encoded == bytes.fromhex("510009030103E88EDD")
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ExecuteCommand)
    assert decoded.length == 9


# def test_execute_on_body_command() -> None:
#     response = codec.ExecuteCommand(0x04, b"\x00")
#     encoded = response.encode()
#     print(encoded.hex())
#     assert encoded == bytes.fromhex("5100070400e73b")
#     decoded = codec.decode(encoded)
#     assert isinstance(decoded, codec.ExecuteCommand)
#     assert decoded.length == 7


def test_execute_command_response() -> None:
    response = codec.ExecuteCommandResponse(1, b"")
    encoded = response.encode()
    assert encoded == b"\xd1\x00\x06\x01\xe0\xf0"
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.ExecuteCommandResponse)
    assert decoded.length == 6


def test_get_attribute_response_model() -> None:
    msg = codec.decode(bytes.fromhex("92001c04000000def8b0c8490000000a4973656e736555204733475f"))
    assert isinstance(msg, codec.GetAttributeResponse)
    assert isinstance(msg.value, attributes.ModelAttribute)
    assert msg.value.formatted_value() == "IsenseU G3"


def test_get_attribute_response_firmware() -> None:
    msg = codec.decode(bytes.fromhex("92001502000000def8e22fec0000000305020269fa"))
    assert isinstance(msg, codec.GetAttributeResponse)
    assert isinstance(msg.value, attributes.FirmwareVersionAttribute)
    assert msg.value.formatted_value() == "05.02.02"


def test_get_attribute_response_afe_settings_all() -> None:
    msg = codec.decode(bytes.fromhex("9200120700000183d6fa48be000002008cc8"))
    assert isinstance(msg, codec.GetAttributeResponse)
    assert isinstance(msg.value, attributes.AfeSettingsAllAttribute)
    assert msg.value.value is not None


def test_get_attribute_response_battery_diagnostics() -> None:
    msg = codec.decode(
        bytes.fromhex("92002CBB000000def8e22fec000000180b35010000000200000003000400050006000700080009000A00ED2C")
    )
    assert isinstance(msg, codec.GetAttributeResponse)
    assert isinstance(msg.value, attributes.BatteryDiagnosticsAttribute)
    assert msg.value.value is not None


# helper method for get_attribute_response tests
def do_test_get_attribute_response_and_return_decoded(attribute: attributes.Attribute, expected_encoded: bytes):
    get_attribute_response = codec.GetAttributeResponse(
        attribute_id=attribute.attribute_id,
        changed_at=int(datetime.fromisoformat("2022-04-20 00:05:23.283+00:00").timestamp() * 1000),
        reporting=types.Reporting(interval=1, on_change=2),
        value=attribute,
    )
    encoded = get_attribute_response.encode()
    assert encoded == expected_encoded
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.GetAttributeResponse)
    assert decoded.attribute_id == get_attribute_response.attribute_id
    assert decoded.changed_at == get_attribute_response.changed_at
    assert decoded.value == get_attribute_response.value
    assert decoded.reporting == get_attribute_response.reporting
    return decoded

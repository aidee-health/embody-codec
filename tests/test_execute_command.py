"""Test ExecuteCommand and ExecuteCommandResponse edge cases."""

import pytest

from embodycodec import codec
from embodycodec import types


def test_execute_command_decode_payload_extraction():
    """Test that ExecuteCommand.decode() extracts only the payload bytes."""
    # Create a valid ExecuteCommand message with command_id=0x01 and no payload
    # Format: msg_type(0x51) + length(0x0006) + command_id(0x01) + crc(2 bytes)
    data = b"\x51\x00\x06\x01\x00\x00"  # Using accept_crc_error for testing

    msg = codec.decode(data, accept_crc_error=True)
    assert isinstance(msg, codec.ExecuteCommand)
    assert msg.command_id == 0x01
    assert msg.value == b""  # Should be empty, not the entire buffer

    # Test with payload data
    # Format: msg_type(0x51) + length(0x0008) + command_id(0x03) + payload(0x01\x02) + crc
    data_with_payload = b"\x51\x00\x08\x03\x01\x02\x00\x00"
    msg2 = codec.decode(data_with_payload, accept_crc_error=True)
    assert isinstance(msg2, codec.ExecuteCommand)
    assert msg2.command_id == 0x03
    assert msg2.value == b"\x01\x02"  # Should be just the payload


def test_execute_command_encode_with_empty_value():
    """Test that ExecuteCommand._encode_body() handles empty values correctly."""
    # Test FORCE_ON_BODY with empty value
    cmd = codec.ExecuteCommand(command_id=0x04, value=b"")
    body = cmd._encode_body()
    assert body == b"\x04\x00"  # command_id + default 0x00

    # Test with None value (should also handle gracefully)
    cmd2 = codec.ExecuteCommand(command_id=0x05, value=None)
    body2 = cmd2._encode_body()
    assert body2 == b"\x05\x00"  # command_id + default 0x00


def test_execute_command_afe_write_register_validation():
    """Test that AFE_WRITE_REGISTER validates data length."""
    # Test with insufficient data
    cmd = codec.ExecuteCommand(command_id=0xA2, value=b"\x01\x02")  # Only 2 bytes, needs 5

    with pytest.raises(ValueError, match="AFE_WRITE_REGISTER requires 5 bytes"):
        cmd._encode_body()

    # Test with correct data
    cmd2 = codec.ExecuteCommand(command_id=0xA2, value=b"\x01\x00\x00\x00\x02")  # 5 bytes
    body = cmd2._encode_body()
    assert body == b"\xa2\x01\x00\x00\x00\x02"  # command_id + address + value


def test_execute_command_response_decode_payload_extraction():
    """Test that ExecuteCommandResponse.decode() extracts only the payload bytes."""
    # Create a valid ExecuteCommandResponse message
    # Format: msg_type(0xD1) + length(0x0006) + response_code(0x01) + crc(2 bytes)
    data = b"\xd1\x00\x06\x01\x00\x00"

    msg = codec.decode(data, accept_crc_error=True)
    assert isinstance(msg, codec.ExecuteCommandResponse)
    assert msg.response_code == 0x01
    assert msg.value == b""  # Should be empty, not the entire buffer

    # Test with payload
    data_with_payload = b"\xd1\x00\x08\xa1\x10\x20\x00\x00"
    msg2 = codec.decode(data_with_payload, accept_crc_error=True)
    assert isinstance(msg2, codec.ExecuteCommandResponse)
    assert msg2.response_code == 0xA1
    assert msg2.value == b"\x10\x20"  # Should be just the payload bytes


def test_execute_command_all_command_types_with_value():
    """Test that all command types handle values correctly."""
    test_cases = [
        (0x04, b"\x01"),  # FORCE_ON_BODY
        (0x05, b"\x00"),  # FORCE_USB_CONNECTION
        (0x06, b"\xff"),  # FORCE_BLE_CONNECTION
        (0x07, b"\x50"),  # FORCE_BATTERY_LEVEL
        (0xA3, b"\x10"),  # AFE_CALIBRATION_COMMAND
        (0xA4, b"\x20"),  # AFE_GAIN_SETTING
    ]

    for command_id, value in test_cases:
        cmd = codec.ExecuteCommand(command_id=command_id, value=value)
        body = cmd._encode_body()
        assert body[0] == command_id
        assert body[1] == value[0]


def test_execute_command_with_integer_value():
    """Test that ExecuteCommand handles integer values correctly."""
    # Test FORCE_BATTERY_LEVEL with integer value
    cmd = codec.ExecuteCommand(command_id=0x07, value=0x50)
    body = cmd._encode_body()
    assert body == b"\x07\x50"  # command_id + value

    # Test AFE_CALIBRATION_COMMAND with integer value
    cmd2 = codec.ExecuteCommand(command_id=0xA3, value=0x10)
    body2 = cmd2._encode_body()
    assert body2 == b"\xa3\x10"  # command_id + value


def test_execute_command_with_none_value():
    """Test that ExecuteCommand handles None values correctly."""
    # Test various command types with None value - should default to 0x00
    test_cases = [
        (0x04, b"\x04\x00"),  # FORCE_ON_BODY
        (0x05, b"\x05\x00"),  # FORCE_USB_CONNECTION
        (0x06, b"\x06\x00"),  # FORCE_BLE_CONNECTION
        (0x07, b"\x07\x00"),  # FORCE_BATTERY_LEVEL
        (0xA3, b"\xa3\x00"),  # AFE_CALIBRATION_COMMAND
        (0xA4, b"\xa4\x00"),  # AFE_GAIN_SETTING
    ]

    for command_id, expected_body in test_cases:
        cmd = codec.ExecuteCommand(command_id=command_id, value=None)
        body = cmd._encode_body()
        assert body == expected_body, f"Failed for command_id {command_id:#x}"

    # Test PRESS_BUTTON with None value - should just have command_id
    cmd_press = codec.ExecuteCommand(command_id=0x03, value=None)
    body_press = cmd_press._encode_body()
    assert body_press == b"\x03"  # Just command_id, no value bytes


def test_every_command_type_encode_body_is_covered() -> None:
    """Every ExecuteCommandType must have its encode shape pinned.

    Before this, REBOOT_DEVICE, FORCE_BLE_CONNECTION, REINIT_SERVICE,
    AFE_READ_ALL_REGISTERS and AFE_GAIN_SETTING had no encode test at all, so the
    refactor of _encode_body could have changed them silently.
    """
    single_byte_value = b"\x2a"
    expected_bodies = {
        types.ExecuteCommandType.RESET_DEVICE: (b"", b"\x01"),
        types.ExecuteCommandType.REBOOT_DEVICE: (b"", b"\x02"),
        types.ExecuteCommandType.PRESS_BUTTON: (b"\x02\x01\xf4", b"\x03\x02\x01\xf4"),
        types.ExecuteCommandType.FORCE_ON_BODY: (single_byte_value, b"\x04\x2a"),
        types.ExecuteCommandType.FORCE_USB_CONNECTION: (single_byte_value, b"\x05\x2a"),
        types.ExecuteCommandType.FORCE_BLE_CONNECTION: (single_byte_value, b"\x06\x2a"),
        types.ExecuteCommandType.FORCE_BATTERY_LEVEL: (single_byte_value, b"\x07\x2a"),
        # Parameter bytes go out reversed: little endian payload in a big endian message.
        types.ExecuteCommandType.REINIT_SERVICE: (b"\x01\x02\x03\x04", b"\x08\x04\x03\x02\x01"),
        types.ExecuteCommandType.AFE_READ_ALL_REGISTERS: (b"", b"\xa1"),
        types.ExecuteCommandType.AFE_WRITE_REGISTER: (b"\x10\x00\x00\x00\x05", b"\xa2\x10\x00\x00\x00\x05"),
        types.ExecuteCommandType.AFE_CALIBRATION_COMMAND: (single_byte_value, b"\xa3\x2a"),
        types.ExecuteCommandType.AFE_GAIN_SETTING: (single_byte_value, b"\xa4\x2a"),
    }
    assert set(expected_bodies) == set(types.ExecuteCommandType), "a command type has no encode expectation"

    for command_type, (value, expected_body) in expected_bodies.items():
        message = codec.ExecuteCommand(command_id=command_type.value, value=value)
        encoded = message.encode()
        body = encoded[codec.Message.hdr_len : len(encoded) - codec.Message.crc_len]
        assert body == expected_body, command_type.name

        decoded = codec.decode(encoded)
        assert isinstance(decoded, codec.ExecuteCommand)
        assert decoded.command_id == command_type.value, command_type.name


def test_reinit_service_accepts_int_value() -> None:
    """The int branch packs big endian, unlike the bytes branch which reverses."""
    message = codec.ExecuteCommand(command_id=types.ExecuteCommandType.REINIT_SERVICE.value, value=0x01020304)
    encoded = message.encode()
    body = encoded[codec.Message.hdr_len : len(encoded) - codec.Message.crc_len]
    assert body == b"\x08\x01\x02\x03\x04"


def test_reinit_service_defaults_to_zero_parameter() -> None:
    message = codec.ExecuteCommand(command_id=types.ExecuteCommandType.REINIT_SERVICE.value, value=None)
    encoded = message.encode()
    body = encoded[codec.Message.hdr_len : len(encoded) - codec.Message.crc_len]
    assert body == b"\x08\x00\x00\x00\x00"

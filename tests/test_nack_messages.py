"""Test NackResponse error messages."""

from embodycodec.codec import NackResponse


def test_nack_error_messages_typos_fixed():
    """Test that NackResponse error messages have correct spelling."""
    nack = NackResponse(response_code=0x04)
    assert nack.error_message() == "Message too short"

    nack = NackResponse(response_code=0x05)
    assert nack.error_message() == "Message too long"

    # Test other messages for completeness
    nack = NackResponse(response_code=0x01)
    assert nack.error_message() == "Unknown message type"

    nack = NackResponse(response_code=0x06)
    assert nack.error_message() == "Message with illegal CRC"

    # Test unknown error code
    nack = NackResponse(response_code=0xFF)
    assert nack.error_message() is None

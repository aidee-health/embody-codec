from embodycodec.crc import crc16


def test_crc() -> None:
    crc = crc16(b"\x12\x00\x06\xa1")
    assert crc == 32098


def test_crc_partial() -> None:
    crc = crc16(b"\x12\x00")
    crc = crc16(data=b"\x06\xa1", existing_crc=crc)
    assert crc == 32098


def test_crc_with_zero_existing() -> None:
    """Test that crc16 works correctly when existing_crc is 0."""
    # This tests the bug fix where existing_crc=0 was incorrectly treated as None
    crc = crc16(b"\x00\x00", existing_crc=0)
    assert crc == 0  # When existing_crc is 0, it should use 0, not 0xFFFF

    # Compare with default behavior
    crc_default = crc16(b"\x00\x00")
    assert crc_default != crc  # Should be different when using default 0xFFFF

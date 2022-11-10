from embodycodec.crc import crc16


def test_crc() -> None:
    crc = crc16(b"\x12\x00\x06\xA1")
    assert crc == 32098


def test_crc_partial() -> None:
    crc = crc16(b"\x12\x00")
    crc = crc16(data=b"\x06\xA1", existing_crc=crc)
    assert crc == 32098

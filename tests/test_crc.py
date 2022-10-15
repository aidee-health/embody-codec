from embodycodec.crc import crc16


def test_crc() -> None:
    crc = crc16(b"\x12\x00\x06\xA1")
    assert crc == 32098

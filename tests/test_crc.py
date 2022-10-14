from embodycodec.crc import crc16


class TestCrc:
    def test_crc(self):
        crc = crc16(b"\x12\x00\x06\xA1")
        assert crc == 32098

from unittest import TestCase
from embodycodec.crc import crc16


class TestCrc(TestCase):
    def test_crc(self):
        crc = crc16(b'\x12\x00\x06\xA1')
        self.assertEqual(crc, 32098)

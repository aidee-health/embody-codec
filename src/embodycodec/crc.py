"""CRC Utility method(s) used by the embodycodec to generate CRC footers."""

from typing import Optional


def crc16(data: bytes, existing_crc: Optional[int] = None, poly: int = 0x1021) -> int:
    data = bytearray(data)
    crc = existing_crc if existing_crc else 0xFFFF
    for byte in data:
        for i in range(0, 8):
            bit = (byte >> (7 - i) & 1) == 1
            c15 = (crc >> 15 & 1) == 1
            crc <<= 1
            if c15 ^ bit:
                crc ^= poly
    crc &= 0xFFFF
    return crc

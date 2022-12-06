"""CRC Utility method(s) used by the embodycodec to generate CRC footers."""

from collections.abc import ByteString
from typing import Optional


def crc16(
    data: ByteString, existing_crc: Optional[int] = None, poly: int = 0x1021
) -> int:
    """Calculate the CRC16 of the given data (bytearray,bytes or memoryview)."""
    crc = existing_crc if existing_crc else 0xFFFF
    for b in data:
        crc = crc ^ (b << 8)
        for _ in range(0, 8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
    return crc & 0xFFFF

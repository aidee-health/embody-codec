"""CRC Utility method(s) used by the embodycodec to generate CRC footers
"""


def crc16(data: bytes, poly=0x1021):
    """Calculate CRC-16 from input bytes"""
    data = bytearray(data)
    crc = 0xFFFF
    for b in data:
        for i in range(0, 8):
            bit = ((b >> (7 - i) & 1) == 1)
            c15 = ((crc >> 15 & 1) == 1)
            crc <<= 1
            if c15 ^ bit:
                crc ^= poly
    crc &= 0xFFFF
    return crc

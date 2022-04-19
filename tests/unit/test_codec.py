from unittest import TestCase
from src.embodycodec import codec
from datetime import datetime
from src.embodycodec import attributes
from src.embodycodec import types


class TestCodec(TestCase):
    def test_decode_heartbeat(self):
        message = b'\x01\x00\x05\xAB\x09'
        heartbeat = codec.decode(message)
        self.assertIsNotNone(heartbeat)
        self.assertEqual(heartbeat.crc, 43785)

    def test_encode_heartbeat(self):
        heartbeat = codec.Heartbeat()
        self.assertEqual(heartbeat.encode(), b'\x01\x00\x05\xAB\x09')

    def test_heartbeat_response(self):
        heartbeat_response = codec.HeartbeatResponse()
        encoded = heartbeat_response.encode()
        self.assertEqual(encoded, b'\x81\x00\x05\x90\x53')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.HeartbeatResponse)

    def test_nack_response(self):
        nack_response = codec.NackResponse(0x02)
        encoded = nack_response.encode()
        self.assertEqual(encoded, b'\x82\x00\x06\x02\x3E\x74')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.NackResponse)
        self.assertEqual(decoded.response_code, 0x02)
        self.assertEqual(decoded.error_message(), 'Unknown message content')
        decoded.response_code = None
        self.assertIsNone(decoded.error_message())
        decoded.response_code = 0xFF
        self.assertIsNone(decoded.error_message())

    def test_decode_get_attribute(self):
        message = b'\x12\x00\x06\xA1\x7D\x62'
        get_attribute = codec.decode(message)
        self.assertIsNotNone(get_attribute)
        self.assertEqual(0xA1, get_attribute.attribute_id)
        self.assertEqual(get_attribute.crc, 32098)

    def test_encode_get_attribute(self):
        get_attribute = codec.GetAttribute(0xA1)
        self.assertEqual(get_attribute.encode(), b'\x12\x00\x06\xA1\x7D\x62')

    def test_get_attribute_Response(self):
        get_attribute_response = codec.GetAttributeResponse(attribute_id=attributes.CurrentTime.attribute_id,
                                                            changed_at=int(datetime.fromisoformat(
                                                                '2022-04-20 00:05:23.283+00:00').timestamp() * 1000),
                                                            reporting=types.Reporting(interval=1, on_change=2),
                                                            value=attributes.CurrentTime(int(datetime.fromisoformat(
                                                                '2022-04-20 00:05:25.283+00:00').timestamp() * 1000)))
        encoded = get_attribute_response.encode()
        print(encoded.hex())
        self.assertEqual(encoded, b'\x92\x00\x1a\x71\x00\x00\x01\x80\x44\x49\xb6\xd3\x00\x01\x02\x08\x00\x00\x01\x80'
                                  b'\x44\x49\xbe\xa3\xdf\x03')
        decoded = codec.decode(encoded)
        self.assertIsInstance(decoded, codec.GetAttributeResponse)
        self.assertEqual(decoded.attribute_id, 0x71)
        self.assertEqual(decoded.changed_at, get_attribute_response.changed_at)
        self.assertEqual(decoded.value, get_attribute_response.value)
        self.assertEqual(decoded.reporting, get_attribute_response.reporting)

"""Regression tests for variable-length payloads.

The original test suite only asserted round-trips for fixed-size payloads, which hid a
family of defects in every attribute and complex type whose encoded size is not static.
Each test here fails against the code as it was before these were fixed.
"""

import pytest

from embodycodec import attributes
from embodycodec import codec
from embodycodec import file_codec
from embodycodec import types


VARIABLE_LENGTH_ATTRIBUTES = [
    attributes.ModelAttribute("EMB123"),
    attributes.VendorAttribute("Aidee"),
    attributes.SystemStatusNamesAttribute(["cpu", "flash", "afe"]),
    attributes.SystemStatusAttribute(
        types.SystemStatus(
            status=[types.SystemStatusType.OK, types.SystemStatusType.WARNING],
            worst=[types.SystemStatusType.OK, types.SystemStatusType.FAILED],
        )
    ),
    attributes.PulseRawListAttribute(
        types.PulseRawList(
            tick=843,
            format=3,
            no_of_ecgs=1,
            no_of_ppgs=3,
            ecgs=[1],
            ppgs=[1000, 100, 5],
        )
    ),
]


@pytest.mark.parametrize("attribute", VARIABLE_LENGTH_ATTRIBUTES, ids=lambda a: type(a).__name__)
def test_set_attribute_declares_real_payload_length(attribute: attributes.Attribute) -> None:
    """SetAttribute wrote a length byte of 0 for every variable-length attribute.

    The payload still went out on the wire, but the length field said zero, so a
    conforming parser dropped the value.
    """
    encoded = codec.SetAttribute(attribute_id=attribute.attribute_id, value=attribute).encode()

    expected_payload = attribute.encode()
    declared_length = encoded[codec.Message.hdr_len + 1]
    assert declared_length == len(expected_payload)
    assert declared_length > 0

    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SetAttribute)
    assert decoded.value == attribute


@pytest.mark.parametrize("attribute", VARIABLE_LENGTH_ATTRIBUTES, ids=lambda a: type(a).__name__)
def test_get_attribute_response_round_trip(attribute: attributes.Attribute) -> None:
    """GetAttributeResponse already derived its length correctly - guard against regression."""
    response = codec.GetAttributeResponse(
        attribute_id=attribute.attribute_id,
        changed_at=1,
        reporting=types.Reporting(interval=1, on_change=1),
        value=attribute,
    )
    decoded = codec.decode(response.encode())
    assert isinstance(decoded, codec.GetAttributeResponse)
    assert decoded.value == attribute


def test_send_file_response_preserves_file_crc() -> None:
    """The payload field used to be named `crc`, colliding with Message.crc.

    Message.decode assigns the footer CRC to `.crc` after construction, so the decoded
    file CRC was silently replaced by the message CRC.
    """
    response = codec.SendFileResponse(file_crc=9)
    encoded = response.encode()
    assert encoded == b"\xc3\x00\x07\x00\t\xd8\xdf"

    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SendFileResponse)
    assert decoded.file_crc == 9
    assert decoded.crc == 0xD8DF  # message footer CRC, a separate value
    assert decoded.length == 7


# format selects the sample width: 0 -> 1 byte, 1 -> 2, 2 -> 3, 3 -> 4.
# to_format_and_lengths() masks ecgs to 2 bits and ppgs to 4 bits, so those are the caps.
@pytest.mark.parametrize("fmt", [0, 1, 2, 3])
@pytest.mark.parametrize(("no_of_ecgs", "no_of_ppgs"), [(0, 0), (1, 3), (3, 15), (0, 15), (3, 0)])
def test_pulse_raw_list_length_matches_encoded_size(fmt: int, no_of_ecgs: int, no_of_ppgs: int) -> None:
    """length() returned 0 on a constructed instance and under-reported by 2 after decode.

    Parameterised over every sample width, since the width table is what length() and the
    truncation check both depend on.
    """
    pulse_raw_list = types.PulseRawList(
        tick=843,
        format=fmt,
        no_of_ecgs=no_of_ecgs,
        no_of_ppgs=no_of_ppgs,
        ecgs=[1] * no_of_ecgs,
        ppgs=[1] * no_of_ppgs,
    )
    encoded = pulse_raw_list.encode()
    assert pulse_raw_list.length() == len(encoded)

    decoded = types.PulseRawList.decode(encoded)
    assert decoded.length() == len(encoded)
    assert decoded.len == len(encoded)
    assert decoded == pulse_raw_list


@pytest.mark.parametrize("fmt", [0, 1, 2, 3])
def test_pulse_raw_list_rejects_truncation_for_every_sample_width(fmt: int) -> None:
    full = types.PulseRawList(
        tick=843,
        format=fmt,
        no_of_ecgs=3,
        no_of_ppgs=15,
        ecgs=[1, 2, 3],
        ppgs=list(range(15)),
    ).encode()

    with pytest.raises(BufferError):
        types.PulseRawList.decode(full[:-1])
    with pytest.raises(BufferError):
        file_codec.PulseRawList.decode(full[:-1])


@pytest.mark.parametrize("truncate_to", [3, 10, 18])
def test_pulse_raw_list_rejects_truncated_buffer(truncate_to: int) -> None:
    """A short buffer used to yield zeroed samples instead of asking for more data.

    Parameterised over both implementations so the two copies cannot drift apart again.
    """
    full = types.PulseRawList(
        tick=843,
        format=3,
        no_of_ecgs=1,
        no_of_ppgs=3,
        ecgs=[1],
        ppgs=[1000, 100, 5],
    ).encode()
    assert len(full) > truncate_to

    with pytest.raises(BufferError):
        types.PulseRawList.decode(full[:truncate_to])
    with pytest.raises(BufferError):
        file_codec.PulseRawList.decode(full[:truncate_to])


def test_oversized_attribute_payload_is_rejected_clearly() -> None:
    """The length field is one byte, so a >255 byte payload cannot be represented.

    Deriving the real length (rather than always writing 0) exposes this; struct's own
    error names only the format character, so raise something that names the problem.
    """
    oversized = attributes.SystemStatusNamesAttribute([f"sensor{i:03d}" for i in range(30)])
    assert len(oversized.encode()) > codec.MAX_ATTRIBUTE_LENGTH

    for message in (
        codec.SetAttribute(attribute_id=oversized.attribute_id, value=oversized),
        codec.AttributeChanged(changed_at=1, attribute_id=oversized.attribute_id, value=oversized),
        codec.GetAttributeResponse(
            attribute_id=oversized.attribute_id,
            changed_at=1,
            reporting=types.Reporting(interval=1, on_change=1),
            value=oversized,
        ),
    ):
        with pytest.raises(ValueError, match="protocol length field"):
            message.encode()


def test_attribute_payload_at_the_length_limit_is_accepted() -> None:
    """Exactly 255 bytes must still encode - the check is > not >=."""
    at_limit = attributes.ModelAttribute("x" * codec.MAX_ATTRIBUTE_LENGTH)
    assert len(at_limit.encode()) == codec.MAX_ATTRIBUTE_LENGTH

    encoded = codec.SetAttribute(attribute_id=at_limit.attribute_id, value=at_limit).encode()
    assert encoded[codec.Message.hdr_len + 1] == codec.MAX_ATTRIBUTE_LENGTH
    decoded = codec.decode(encoded)
    assert isinstance(decoded, codec.SetAttribute)
    assert decoded.value == at_limit


def test_system_status_names_empty_round_trip() -> None:
    """decode(b"") yields an empty list, and encoding it raised IndexError."""
    decoded = attributes.SystemStatusNamesAttribute.decode(b"")
    assert decoded.value == []
    assert decoded.encode() == b""


def test_system_status_names_round_trip() -> None:
    attribute = attributes.SystemStatusNamesAttribute(["cpu", "flash", "afe"])
    assert attribute.encode() == b"cpu,flash,afe"
    assert attributes.SystemStatusNamesAttribute.decode(attribute.encode()) == attribute


@pytest.mark.parametrize("value", [0x000000, 0x050202, 0x7FFFFF, 0x800000, 0x900000, 0xFFFFFF])
def test_firmware_version_round_trip(value: int) -> None:
    """encode() used signed=True while decode() used signed=False.

    Anything from 0x800000 up raised OverflowError on encode.
    """
    attribute = attributes.FirmwareVersionAttribute(value)
    encoded = attribute.encode()
    assert len(encoded) == 3
    assert attributes.FirmwareVersionAttribute.decode(encoded) == attribute


def test_firmware_version_formatted_value_keeps_major_version() -> None:
    """The mask was 0xFFFFF (20 bits), which truncated the top nibble of the major byte."""
    assert attributes.FirmwareVersionAttribute(0x900000).formatted_value() == "144.00.00"
    assert attributes.FirmwareVersionAttribute(0x050301).formatted_value() == "05.03.01"


def test_alarm_round_trip() -> None:
    """changed_at/alarm_type were annotated `int | None`, which ">QB" cannot pack."""
    alarm = codec.Alarm(changed_at=1, alarm_type=0x01)
    decoded = codec.decode(alarm.encode())
    assert isinstance(decoded, codec.Alarm)
    assert decoded == alarm
    assert decoded.alarm_message() == "Low battery"


@pytest.mark.parametrize("message_class", [file_codec.PulseBlockEcg, file_codec.PulseBlockPpg])
def test_pulse_block_encode_is_not_a_silent_stub(
    message_class: type[file_codec.PulseBlockEcg] | type[file_codec.PulseBlockPpg],
) -> None:
    """encode() returned two zero bytes regardless of contents, which looks like valid output."""
    message = message_class(time=1, channel=0, num_samples=1, samples=[5], pkg_length=14)
    with pytest.raises(NotImplementedError):
        message.encode()


@pytest.mark.parametrize("message_class", [file_codec.PulseBlockEcg, file_codec.PulseBlockPpg])
def test_pulse_block_rejects_short_header(
    message_class: type[file_codec.PulseBlockEcg] | type[file_codec.PulseBlockPpg],
) -> None:
    """PulseBlockPpg guarded on 13 bytes while the header is 14."""
    with pytest.raises(BufferError):
        message_class.decode(bytes(file_codec.PULSE_BLOCK_HEADER_LENGTH - 1))

"""Decoders for payloads defined by TRT Protocol v0.1."""

from __future__ import annotations


def decode_info_payload(payload: bytes) -> dict[str, str]:
    if not payload:
        raise ValueError("INFO response payload is empty")
    field_names = {
        0x01: "board_type",
        0x02: "revision",
        0x03: "firmware",
        0x04: "protocol",
        0x05: "serial",
    }
    count = payload[0]
    offset = 1
    fields: dict[str, str] = {}
    for _ in range(count):
        if offset + 2 > len(payload):
            raise ValueError("INFO response has a truncated field header")
        field_id, length = payload[offset], payload[offset + 1]
        offset += 2
        value = payload[offset : offset + length]
        if len(value) != length:
            raise ValueError("INFO response has a truncated field value")
        offset += length
        name = field_names.get(field_id, f"field_{field_id:02X}")
        if field_id == 0x03:
            fields[name] = ".".join(str(part) for part in value)
        elif field_id == 0x04 and len(value) == 1:
            fields[name] = str(value[0])
        else:
            fields[name] = value.decode("utf-8", errors="replace")
    if offset != len(payload):
        raise ValueError("INFO response contains trailing bytes")
    return fields


def decode_capability_ids(payload: bytes) -> tuple[int, ...] | None:
    if not payload or len(payload) != 1 + payload[0] * 2:
        return None
    return tuple(
        int.from_bytes(payload[offset : offset + 2], byteorder="big")
        for offset in range(1, len(payload), 2)
    )

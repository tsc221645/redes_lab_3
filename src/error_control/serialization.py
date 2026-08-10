"""Serialización de MESSAGE y conversión a tramas Hamming."""
from __future__ import annotations
import json
from .hamming import HammingError, encode_bits, decode_bits

class SerializationError(ValueError):
    pass

def _bytes_to_bits(data: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in data)

def _bits_to_bytes(bits: str) -> bytes:
    if len(bits) % 8:
        raise SerializationError("los bits decodificados no forman bytes completos")
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

def serialize_packet(packet: dict) -> str:
    if not isinstance(packet, dict) or packet.get("type") != "MESSAGE":
        raise SerializationError("packet debe ser MESSAGE")
    try:
        raw = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SerializationError("packet no serializable") from exc
    return encode_bits(_bytes_to_bits(raw))

def deserialize_packet(frame: str) -> dict:
    try:
        result = decode_bits(frame)
        packet = json.loads(_bits_to_bytes(result.data_bits).decode("utf-8"))
    except (HammingError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SerializationError("DATA inválido o corrupto") from exc
    if not isinstance(packet, dict) or packet.get("type") != "MESSAGE":
        raise SerializationError("tipo de DATA inválido")
    return packet

def packet_to_frame(packet: dict) -> bytes:
    return (serialize_packet(packet) + "\n").encode("ascii")

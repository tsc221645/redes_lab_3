"""Hamming(7,4) de paridad par."""
from __future__ import annotations
from dataclasses import dataclass

class HammingError(ValueError):
    """Entrada inválida o inconsistente."""

@dataclass(frozen=True)
class DecodeResult:
    data_bits: str
    corrected_blocks: int = 0
    corrected_positions: tuple[int, ...] = ()
    errors_detected: int = 0

def _check(bits: str, length: int) -> None:
    if len(bits) != length or any(c not in "01" for c in bits):
        raise HammingError(f"se esperaban {length} bits binarios")

def encode_nibble(bits4: str) -> str:
    _check(bits4, 4)
    d1, d2, d3, d4 = map(int, bits4)
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}"

def decode_codeword(bits7: str) -> DecodeResult:
    _check(bits7, 7)
    b = [0] + list(map(int, bits7))
    s1 = b[1] ^ b[3] ^ b[5] ^ b[7]
    s2 = b[2] ^ b[3] ^ b[6] ^ b[7]
    s3 = b[4] ^ b[5] ^ b[6] ^ b[7]
    pos = s1 + 2 * s2 + 4 * s3
    if pos:
        b[pos] ^= 1
    data = f"{b[3]}{b[5]}{b[6]}{b[7]}"
    return DecodeResult(data, int(bool(pos)), (pos,) if pos else (), int(bool(pos)))

def encode_bits(data_bits: str) -> str:
    if any(c not in "01" for c in data_bits) or len(data_bits) % 4:
        raise HammingError("los datos deben ser bits y múltiplo de 4")
    return "".join(encode_nibble(data_bits[i:i+4]) for i in range(0, len(data_bits), 4))

def decode_bits(encoded_bits: str) -> DecodeResult:
    if any(c not in "01" for c in encoded_bits) or len(encoded_bits) % 7:
        raise HammingError("la trama debe ser binaria y múltiplo de 7")
    results = [decode_codeword(encoded_bits[i:i+7]) for i in range(0, len(encoded_bits), 7)]
    return DecodeResult("".join(r.data_bits for r in results), sum(r.corrected_blocks for r in results),
                        tuple(p for r in results for p in r.corrected_positions),
                        sum(r.errors_detected for r in results))

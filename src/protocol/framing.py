"""Framing LF para el stream TCP compartido."""
from __future__ import annotations

from dataclasses import dataclass
from .constants import MAX_FRAME_SIZE

class FrameError(ValueError):
    """Una línea no cumple el framing o excede el tamaño permitido."""

def encode_line(text: str) -> bytes:
    data = text.encode("utf-8")
    if len(data) > MAX_FRAME_SIZE:
        raise FrameError("frame demasiado grande")
    return data + b"\n"

@dataclass
class LineBuffer:
    buffer: bytearray = None

    def __post_init__(self) -> None:
        if self.buffer is None:
            self.buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        if len(self.buffer) + len(data) > MAX_FRAME_SIZE:
            raise FrameError("frame incompleto demasiado grande")
        self.buffer.extend(data)
        lines: list[bytes] = []
        while b"\n" in self.buffer:
            end = self.buffer.index(10)
            line = bytes(self.buffer[:end])
            del self.buffer[:end + 1]
            if len(line) > MAX_FRAME_SIZE:
                raise FrameError("frame demasiado grande")
            lines.append(line)
        return lines

def classify_line(line: bytes) -> str:
    stripped = line.strip()
    if stripped.startswith(b"{"):
        return "control"
    if stripped and all(c in (48, 49) for c in stripped):
        return "data"
    raise FrameError("línea desconocida")

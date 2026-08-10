from __future__ import annotations
import socket
from .config import NeighborConfig
from ..protocol.constants import CONNECT_TIMEOUT

def send_bytes(ip: str, port: int, data: bytes, timeout: float = CONNECT_TIMEOUT) -> None:
    with socket.create_connection((ip, port), timeout=timeout) as sock:
        sock.sendall(data)

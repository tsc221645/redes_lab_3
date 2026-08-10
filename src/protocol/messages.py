"""Validadores pequeños para mensajes de control."""
from __future__ import annotations

def validate_control(message: dict) -> bool:
    kind=message.get("type")
    if kind in {"HELLO","HELLO_ACK"}: return isinstance(message.get("from"),str)
    if kind=="LSA": return isinstance(message.get("origin"),str) and isinstance(message.get("seq"),int) and isinstance(message.get("links"),list)
    return False

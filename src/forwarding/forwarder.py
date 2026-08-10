from __future__ import annotations
from ..error_control.serialization import packet_to_frame
from ..protocol.constants import MAX_HOPS

def prepare_forward(packet: dict) -> dict:
    if packet.get("type") != "MESSAGE": raise ValueError("tipo inválido")
    hops=packet.get("hops",0)
    if not isinstance(hops,int) or hops >= MAX_HOPS: raise ValueError("MAX_HOPS excedido")
    result=dict(packet); result["hops"]=hops+1; return result

def frame_for_forward(packet: dict) -> bytes: return packet_to_frame(prepare_forward(packet))

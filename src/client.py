from __future__ import annotations
import json, socket
from .common.config import NodeConfig
from .common.networking import send_bytes
from .protocol.framing import encode_line

def send_message(config: NodeConfig, destination: str, message: str) -> None:
    packet={"type":"MESSAGE","from":config.node_id,"to":destination,"hops":0,"payload":message}
    gateway=config.gateway
    if not gateway: raise ValueError("client requiere gateway")
    send_bytes(gateway["ip"],gateway["port"],encode_line(json.dumps(packet,ensure_ascii=False,separators=(",",":"))))

from __future__ import annotations
import json, socket
from .common.config import NodeConfig
from .common.networking import send_bytes
from .protocol.framing import encode_line

def send_message(config: NodeConfig, destination: str, message: str) -> None:
    packet={"type":"MESSAGE","from":config.node_id,"to":destination,"hops":0,"payload":message}
    gateway=config.gateway
    import logging
    log = logging.getLogger(__name__)
    try:
        send_bytes(
            gateway["ip"],
            gateway["port"],
            encode_line(
                json.dumps(
                    packet,
                    ensure_ascii=False,
                    separators=(",", ":")
                )
            )
        )

    except ConnectionRefusedError:
        log.error("El router no está disponible.")

    except TimeoutError:
        log.error("Tiempo de espera agotado.")

    except OSError as exc:
        log.error("No fue posible enviar el mensaje: %s", exc)

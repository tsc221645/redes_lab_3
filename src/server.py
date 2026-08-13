from __future__ import annotations
import json, logging, socket
from .common.config import NodeConfig
from .protocol.framing import LineBuffer

log=logging.getLogger(__name__)

def run_server(config: NodeConfig) -> None:
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM); server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); server.bind((config.listen_ip,config.listen_port)); server.listen(); server.settimeout(1)
    log.info("[%s] servidor escuchando en %s:%s",config.node_id,config.listen_ip,config.listen_port)
    try:
        while True:
            try: conn,_=server.accept()
            except socket.timeout: continue
            except OSError as exc:
                log.error("Error aceptando conexión: %s", exc)
                continue
            with conn:
                buf=LineBuffer()
                for line in buf.feed(conn.recv(65536)):
                    try:
                        packet=json.loads(line.decode("utf-8")); log.info("[%s] recibido mensaje de %s (hops=%s)",config.node_id,packet.get("from"),packet.get("hops"))
                    except (UnicodeDecodeError,json.JSONDecodeError): log.warning("mensaje inválido")
    except KeyboardInterrupt:
        log.info("Servidor detenido por el usuario.")
    finally: server.close()

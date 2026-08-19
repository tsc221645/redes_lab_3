"""Router Link State: I/O TCP separado de workers de control y datos."""
from __future__ import annotations
import json, logging, queue, socket, threading, time
from pathlib import Path
from .common.config import NodeConfig, NeighborConfig
from .common.networking import send_bytes
from .error_control.serialization import packet_to_frame, deserialize_packet, SerializationError
from .protocol.constants import DEAD_INTERVAL, HELLO_INTERVAL, SOCKET_READ_TIMEOUT
from .protocol.framing import LineBuffer, FrameError, encode_line, classify_line
from .routing.lsdb import LSDB
from .routing.dijkstra import shortest_routes
from .routing.routing_table import write_csv

log=logging.getLogger(__name__)

class Router:
    def __init__(self, config: NodeConfig, output_dir: str|Path="output"):
        self.config=config; self.output_dir=output_dir; self.stop=threading.Event(); self.lock=threading.RLock()
        self.lsdb=LSDB(config.node_id); self.seq=0; self.active: dict[str,float]={}; self.routes={}
        self.neighbors={n.node_id:n for n in config.neighbors}; self.server: socket.socket|None=None
        self.routing_queue: queue.Queue[tuple[dict, socket.socket]] = queue.Queue()
        self.forwarding_queue: queue.Queue[tuple[str, dict|None]] = queue.Queue()
        self.workers: list[threading.Thread] = []

    def start(self) -> None:
        self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM); self.server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.server.settimeout(1); self.server.bind((self.config.listen_ip,self.config.listen_port)); self.server.listen()
        self._change_lsa(force=True)
        threads=[
            threading.Thread(target=self._routing_worker, daemon=True,name=f"{self.config.node_id}-routing"),
            threading.Thread(target=self._forwarding_worker, daemon=True,name=f"{self.config.node_id}-forwarding"),
            threading.Thread(target=self._hello_loop, daemon=True,name=f"{self.config.node_id}-hello"),
            threading.Thread(target=self._dead_loop, daemon=True, name=f"{self.config.node_id}-dead"),
        ]
        self.workers=threads
        for t in threads: t.start()
        log.info("[%s] router escuchando en %s:%s",self.config.node_id,self.config.listen_ip,self.config.listen_port)
        try:
            while not self.stop.is_set():
                try: conn,_=self.server.accept()
                except socket.timeout: continue
                threading.Thread(target=self._connection, args=(conn,), daemon=True).start()
        except KeyboardInterrupt: log.info("[%s] interrupción recibida",self.config.node_id)
        except Exception as exc:
            log.exception("[%s] Error del router: %s",
                        self.config.node_id,
                        exc)
        finally: self.shutdown()
        log.info("[%s] Router detenido.", self.config.node_id)
        

    def shutdown(self) -> None:
        if self.stop.is_set(): return
        self.stop.set()
        if self.server:
            try: self.server.close()
            except OSError: pass
        self.routing_queue.put((None, None))  # type: ignore[arg-type]
        self.forwarding_queue.put((None, None))
        for worker in self.workers:
            if worker is not threading.current_thread(): worker.join(timeout=2)

    def _connection(self, conn: socket.socket) -> None:
        buffer=LineBuffer(); conn.settimeout(SOCKET_READ_TIMEOUT)
        try:
            while not self.stop.is_set():
                try: data=conn.recv(65536)
                except socket.timeout: continue
                if not data: break
                for line in buffer.feed(data): self._dispatch(line,conn)
        
        except ConnectionResetError:
            log.info("[%s] Cliente desconectado.", self.config.node_id)
        except (OSError, FrameError) as exc:
            log.debug(
                "[%s] conexión terminada: %s",
                self.config.node_id,
                exc,
            )
        finally: conn.close()

    def _dispatch(
        self,
        line: bytes,
        conn: socket.socket,
    ) -> None:

        kind = classify_line(line)

        if kind == "data":
            try:
                frame = line.decode("ascii")
                self.forwarding_queue.put(
                    ("frame", frame)
                )

            except UnicodeDecodeError:
                log.warning(
                    "[%s] DATA contiene caracteres inválidos.",
                    self.config.node_id,
                )

            return

        try:
            message = json.loads(
                line.decode("utf-8")
            )

        except UnicodeDecodeError:
            log.warning(
                "[%s] Mensaje no UTF-8 recibido.",
                self.config.node_id,
            )
            return

        except json.JSONDecodeError:
            log.warning(
                "[%s] JSON inválido recibido.",
                self.config.node_id,
            )
            return

        if not isinstance(message, dict):
            log.warning(
                "[%s] Mensaje de control inválido.",
                self.config.node_id,
            )
            return

        self.routing_queue.put(
            (message, conn)
        )

    def _routing_worker(self) -> None:
        """Procesa exclusivamente HELLO, ACK y LSA."""
        while not self.stop.is_set():
            message, conn = self.routing_queue.get()
            try:
                self._handle_control(message, conn)
            except Exception as exc:
                log.exception(
                    "[%s] Error procesando mensaje de control: %s",
                    self.config.node_id,
                    exc
                )
            finally:
                self.routing_queue.task_done()

    def _forwarding_worker(self) -> None:
        """Procesa exclusivamente DATA y el reenvío entre routers."""
        while not self.stop.is_set():
            kind, value = self.forwarding_queue.get()
            try:
                if kind is None: return
                if kind == "frame": self._handle_data(value)  # type: ignore[arg-type]
                elif kind == "packet": self._handle_data_packet(value)  # type: ignore[arg-type]
            finally:
                self.forwarding_queue.task_done()

    def _handle_control(self,m:dict,conn:socket.socket|None) -> None:
        sender=m.get("from")
        if sender not in self.neighbors: return
        if m.get("type")=="HELLO":
            self._mark_up(sender)
            # El listener puede haber cerrado `conn` antes de que el worker
            # procese el mensaje. Abrimos una conexión independiente para el ACK.
            neighbor=self.neighbors[sender]
            ack=encode_line(json.dumps({"type":"HELLO_ACK","from":self.config.node_id,"to":sender}))
            try:
                send_bytes(neighbor.ip,neighbor.port,ack)
            except (OSError,ConnectionError):
                log.debug("[%s] no se pudo enviar HELLO_ACK a %s",self.config.node_id,sender)
        elif m.get("type")=="HELLO_ACK" and m.get("to")==self.config.node_id: self._mark_up(sender)
        elif m.get("type")=="LSA" and self.lsdb.accept(m):
            log.info("[%s] [LSA] accepted origin=%s seq=%s",self.config.node_id,m.get("origin"),m.get("seq")); self._recalculate(); self._flood(m,sender)

    def _mark_up(self,nid:str) -> None:
        changed=False
        with self.lock:
            if nid not in self.active: changed=True
            self.active[nid]=time.monotonic()
        if changed: log.info("[%s] [NEIGHBOR] %s -> UP",self.config.node_id,nid); self._change_lsa()

    def _change_lsa(self,force=False) -> None:
        with self.lock:
            links=[{"to":nid,"cost":self.neighbors[nid].cost} for nid in sorted(self.active)]
            old=self.lsdb.snapshot().get(self.config.node_id)
            if not force and old and tuple((x["to"],x["cost"]) for x in links)==old.links: return
            self.seq+=1; self.lsdb.set_local(self.seq,links)
            lsa={"type":"LSA","origin":self.config.node_id,"seq":self.seq,"links":links,"from":self.config.node_id}
        log.info("[%s] [LSA] generated seq=%s",self.config.node_id,self.seq); self._recalculate(); self._flood(lsa,None)

    def _recalculate(self) -> None:
        with self.lock: self.routes=shortest_routes(self.config.node_id,self.lsdb.snapshot())
        write_csv(self.config.node_id,self.routes,self.neighbors,self.output_dir)
        log.info("[%s] [DIJKSTRA] table updated entries=%s",self.config.node_id,len(self.routes))

    def _flood(self,lsa:dict,exclude:str|None) -> None:
        for nid,n in self.neighbors.items():
            if nid!=exclude and nid in self.active:
                copy=dict(lsa); copy["from"]=self.config.node_id
                try: send_bytes(n.ip,n.port,encode_line(json.dumps(copy,separators=(",",":"))))
                except (OSError, ConnectionError) as exc:
                    log.debug(
                        "[%s] No se pudo enviar LSA a %s (%s)",
                        self.config.node_id,
                        nid,
                        exc
                    )

    def _hello_loop(self) -> None:
        while not self.stop.wait(HELLO_INTERVAL):
            for n in self.neighbors.values():
                try: send_bytes(n.ip,n.port,encode_line(json.dumps({"type":"HELLO","from":self.config.node_id}))); log.debug("[%s] HELLO -> %s",self.config.node_id,n.node_id)
                except (OSError, ConnectionError):
                    log.debug(
                        "[%s] HELLO falló hacia %s",
                        self.config.node_id,
                        n.node_id
                    )

    def _dead_loop(self) -> None:
        while not self.stop.wait(1):
            now=time.monotonic(); down=[]
            with self.lock:
                for nid,last in list(self.active.items()):
                    if now-last>DEAD_INTERVAL: del self.active[nid]; down.append(nid)
            if down:
                for nid in down: log.info("[%s] [NEIGHBOR] %s -> DOWN",self.config.node_id,nid)
                self._change_lsa()

    def _handle_data(self,frame:str) -> None:
        try: packet=deserialize_packet(frame)
        except SerializationError as exc: log.warning("[%s] DATA descartado: %s",self.config.node_id,exc); return
        self._handle_data_packet(packet)

    def _handle_data_packet(self,packet:dict) -> None:
        try:
            if packet.get("to") in {h.get("node_id") for h in self.config.attached_hosts}:
                self._deliver_host(packet); return
            gateway=(self.config.hosts or {}).get(packet.get("to"),{}).get("gateway",packet.get("to"))
            if gateway==self.config.node_id: self._deliver_host(packet); return
            with self.lock: route=self.routes.get(gateway)
            if not route: log.warning("[%s] destino inalcanzable: %s",self.config.node_id,gateway); return
            n=self.neighbors.get(route.next_hop)
            if n: send_bytes(n.ip,n.port,packet_to_frame({**packet,"hops":packet.get("hops",0)+1})); log.info("[%s] [DATA] %s via %s",self.config.node_id,packet.get("to"),route.next_hop)
        except (OSError,ConnectionError,TypeError,ValueError) as exc: log.warning("[%s] forwarding falló: %s",self.config.node_id,exc)

    def _deliver_host(self,packet:dict) -> None:
        target=next((h for h in self.config.attached_hosts if h.get("node_id")==packet.get("to")),None)
        if not target: log.warning("[%s] host local no configurado: %s",self.config.node_id,packet.get("to")); return
        try:
            send_bytes(
                target["ip"],
                target["port"],
                encode_line(
                    json.dumps(
                        packet,
                        ensure_ascii=False,
                        separators=(",", ":")
                    )
                )
            )
        except (ConnectionError, OSError) as exc:
            log.warning(
                "[%s] No se pudo entregar al host %s: %s",
                self.config.node_id,
                packet.get("to"),
                exc
            )
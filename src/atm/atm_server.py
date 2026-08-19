from __future__ import annotations

import json
import logging
import socket

from ..common.config import NodeConfig
from ..common.networking import send_bytes
from ..protocol.framing import LineBuffer
from ..error_control.serialization import packet_to_frame
from .bank import Bank
from .protocol import (
    ATM_REQUEST,
    AUTH,
    BALANCE,
    WITHDRAW,
    make_response,
    validate_request,
)


log = logging.getLogger(__name__)


class ATMServer:
    def __init__(self, config: NodeConfig) -> None:
        self.config = config
        self.bank = Bank()
        self.server: socket.socket | None = None

    def start(self) -> None:
        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        self.server.settimeout(1)

        self.server.bind(
            (
                self.config.listen_ip,
                self.config.listen_port,
            )
        )

        self.server.listen()

        log.info(
            "[BANK] Banco escuchando en %s:%s",
            self.config.listen_ip,
            self.config.listen_port,
        )

        try:
            while True:
                try:
                    conn, address = self.server.accept()
                except socket.timeout:
                    continue

                log.info(
                    "[BANK] conexión recibida desde %s",
                    address,
                )

                self._handle_connection(conn)

        except KeyboardInterrupt:
            log.info("[BANK] Servidor detenido por el usuario.")

        finally:
            if self.server is not None:
                try:
                    self.server.close()
                except OSError:
                    pass

            log.info("[BANK] Servidor bancario detenido.")

    def _handle_connection(self, conn: socket.socket) -> None:
        try:
            conn.settimeout(5)

            buffer = LineBuffer()

            while True:
                try:
                    data = conn.recv(65536)
                except socket.timeout:
                    log.warning("[BANK] Tiempo de espera agotado.")
                    return

                if not data:
                    return

                try:
                    lines = buffer.feed(data)
                except Exception as exc:
                    log.warning(
                        "[BANK] Frame inválido: %s",
                        exc,
                    )
                    return

                for line in lines:
                    self._process_packet(line)

        except ConnectionResetError:
            log.info("[BANK] El router cerró la conexión.")

        except OSError as exc:
            log.warning(
                "[BANK] Error de socket: %s",
                exc,
            )

        finally:
            conn.close()

    def _process_packet(self, line: bytes) -> None:
        try:
            packet = json.loads(
                line.decode("utf-8")
            )

        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            log.warning(
                "[BANK] Mensaje inválido: %s",
                exc,
            )
            return

        if not isinstance(packet, dict):
            log.warning("[BANK] El paquete no es un objeto JSON.")
            return

        if packet.get("type") != "MESSAGE":
            log.warning(
                "[BANK] Tipo de paquete inesperado: %s",
                packet.get("type"),
            )
            return

        source = packet.get("from")

        payload = packet.get("payload")

        if not isinstance(source, str):
            log.warning("[BANK] Origen inválido.")
            return

        if not validate_request(payload):
            log.warning(
                "[BANK] Solicitud ATM inválida."
            )
            return

        log.info(
            "[BANK] Solicitud %s recibida desde %s",
            payload.get("operation"),
            source,
        )

        response = self._process_request(payload)

        response_packet = {
            "type": "MESSAGE",
            "from": self.config.node_id,
            "to": source,
            "hops": 0,
            "payload": response,
        }

        self._send_response(source, response_packet)

    def _process_request(self, request: dict) -> dict:
        operation = request.get("operation")

        if operation == AUTH:
            return self._authenticate(request)

        if operation == BALANCE:
            return self._balance(request)

        if operation == WITHDRAW:
            return self._withdraw(request)

        return make_response(
            operation="UNKNOWN",
            success=False,
            message="Operación no soportada.",
        )

    def _authenticate(self, request: dict) -> dict:
        card = request["card"]
        pin = request["pin"]

        if self.bank.verify_credentials(card, pin):
            return make_response(
                AUTH,
                True,
                "Autenticación exitosa.",
            )

        return make_response(
            AUTH,
            False,
            "Tarjeta o PIN incorrectos.",
        )

    def _balance(self, request: dict) -> dict:
        card = request["card"]

        balance = self.bank.get_balance(card)

        if balance is None:
            return make_response(
                BALANCE,
                False,
                "Tarjeta no encontrada.",
            )

        return make_response(
            BALANCE,
            True,
            "Consulta realizada correctamente.",
            balance=balance,
        )

    def _withdraw(self, request: dict) -> dict:
        card = request["card"]
        amount = float(request["amount"])

        success, message, balance = self.bank.withdraw(
            card,
            amount,
        )

        response = make_response(
            WITHDRAW,
            success,
            message,
        )

        if balance is not None:
            response["balance"] = balance

        return response

    def _send_response(
        self,
        destination: str,
        packet: dict,
    ) -> None:

        gateway = self.config.gateway

        if not isinstance(gateway, dict):
            log.error(
                "[BANK] No existe gateway configurado."
            )
            return

        ip = gateway.get("ip")
        port = gateway.get("port")

        if not isinstance(ip, str) or not isinstance(port, int):
            log.error(
                "[BANK] Gateway inválido."
            )
            return

        try:
            data = packet_to_frame(packet)

            send_bytes(
                ip,
                port,
                data,
            )

            log.info(
                "[BANK] Respuesta enviada hacia %s",
                destination,
            )

        except (ConnectionError, OSError, TimeoutError) as exc:
            log.error(
                "[BANK] No se pudo enviar respuesta: %s",
                exc,
            )
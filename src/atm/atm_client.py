from __future__ import annotations

import json
import logging
import socket
import threading
from typing import Any

from ..common.config import NodeConfig
from ..common.networking import send_bytes
from ..protocol.framing import LineBuffer, encode_line
from .protocol import (
    AUTH,
    BALANCE,
    WITHDRAW,
    make_auth_request,
    make_balance_request,
    make_withdraw_request,
)


log = logging.getLogger(__name__)


class ATMClient:
    def __init__(
        self,
        config: NodeConfig,
        bank_node: str,
    ) -> None:

        self.config = config
        self.bank_node = bank_node

        self.response_queue: list[dict[str, Any]] = []
        self.response_event = threading.Event()

        self.server: socket.socket | None = None
        self.stop = threading.Event()

    def start(self) -> None:
        listener = threading.Thread(
            target=self._listen_for_responses,
            daemon=True,
            name="atm-response-listener",
        )

        listener.start()

        try:
            self._run_menu()

        except KeyboardInterrupt:
            print("\nATM detenido por el usuario.")

        finally:
            self.stop.set()

            if self.server is not None:
                try:
                    self.server.close()
                except OSError:
                    pass

    def _listen_for_responses(self) -> None:
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

        try:
            self.server.bind(
                (
                    self.config.listen_ip,
                    self.config.listen_port,
                )
            )

            self.server.listen()

            log.info(
                "[ATM] escuchando respuestas en %s:%s",
                self.config.listen_ip,
                self.config.listen_port,
            )

            while not self.stop.is_set():

                try:
                    conn, _ = self.server.accept()

                except socket.timeout:
                    continue

                except OSError:
                    if self.stop.is_set():
                        break

                    continue

                threading.Thread(
                    target=self._handle_response_connection,
                    args=(conn,),
                    daemon=True,
                ).start()

        except OSError as exc:
            log.error(
                "[ATM] No se pudo iniciar listener: %s",
                exc,
            )

    def _handle_response_connection(
        self,
        conn: socket.socket,
    ) -> None:

        try:
            conn.settimeout(5)

            buffer = LineBuffer()

            data = conn.recv(65536)

            if not data:
                return

            for line in buffer.feed(data):
                self._process_response(line)

        except (OSError, ValueError) as exc:
            log.warning(
                "[ATM] Error recibiendo respuesta: %s",
                exc,
            )

        finally:
            conn.close()

    def _process_response(self, line: bytes) -> None:
        try:
            packet = json.loads(
                line.decode("utf-8")
            )

        except (UnicodeDecodeError, json.JSONDecodeError):
            log.warning(
                "[ATM] Respuesta inválida."
            )
            return

        if not isinstance(packet, dict):
            return

        if packet.get("type") != "MESSAGE":
            return

        payload = packet.get("payload")

        if not isinstance(payload, dict):
            return

        self.response_queue.append(payload)

        self.response_event.set()

    def _send_request(self, payload: dict) -> dict | None:
        packet = {
            "type": "MESSAGE",
            "from": self.config.node_id,
            "to": self.bank_node,
            "hops": 0,
            "payload": payload,
        }

        gateway = self.config.gateway

        if not isinstance(gateway, dict):
            print("ERROR: el ATM no tiene gateway configurado.")
            return None

        ip = gateway.get("ip")
        port = gateway.get("port")

        if not isinstance(ip, str) or not isinstance(port, int):
            print("ERROR: configuración del gateway inválida.")
            return None

        self.response_event.clear()

        try:
            data = encode_line(
                json.dumps(
                    packet,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )

            send_bytes(
                ip,
                port,
                data,
            )

        except (ConnectionError, TimeoutError, OSError) as exc:
            print(f"No fue posible comunicarse con el banco: {exc}")
            return None

        if not self.response_event.wait(timeout=10):
            print("No se recibió respuesta del banco.")
            return None

        if not self.response_queue:
            return None

        return self.response_queue.pop(0)

    def _run_menu(self) -> None:
        print()
        print("=" * 40)
        print("              ATM")
        print("=" * 40)
        print()

        card = input("Ingrese número de tarjeta: ").strip()
        pin = input("Ingrese PIN: ").strip()

        if not card or not pin:
            print("Tarjeta y PIN son obligatorios.")
            return

        response = self._send_request(
            make_auth_request(card, pin)
        )

        if response is None:
            return

        if not response.get("success"):
            print()
            print(response.get("message"))
            return

        print()
        print(response.get("message"))

        while True:
            print()
            print("1. Consultar saldo")
            print("2. Retirar dinero")
            print("3. Salir")
            print()

            option = input(
                "Seleccione una opción: "
            ).strip()

            if option == "1":
                self._show_balance(card)

            elif option == "2":
                self._withdraw(card)

            elif option == "3":
                print()
                print("Gracias por utilizar el ATM.")
                break

            else:
                print("Opción inválida.")

    def _show_balance(self, card: str) -> None:
        response = self._send_request(
            make_balance_request(card)
        )

        if response is None:
            return

        print()

        if response.get("success"):
            balance = response.get("balance", 0)
            print(
                f"Saldo disponible: Q{float(balance):.2f}"
            )

        else:
            print(
                response.get(
                    "message",
                    "No se pudo consultar el saldo.",
                )
            )

    def _withdraw(self, card: str) -> None:
        raw_amount = input(
            "Ingrese monto a retirar: Q"
        ).strip()

        try:
            amount = float(raw_amount)

        except ValueError:
            print("Monto inválido.")
            return

        if amount <= 0:
            print("El monto debe ser mayor que cero.")
            return

        response = self._send_request(
            make_withdraw_request(
                card,
                amount,
            )
        )

        if response is None:
            return

        print()

        if response.get("success"):
            balance = response.get("balance")

            print(
                "Retiro realizado correctamente."
            )

            if balance is not None:
                print(
                    f"Saldo restante: Q{float(balance):.2f}"
                )

        else:
            print(
                response.get(
                    "message",
                    "No se pudo realizar el retiro.",
                )
            )
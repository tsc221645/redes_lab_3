from __future__ import annotations
import argparse, logging
from .common.config import load_config
from .common.logging_utils import configure_logging
from .router import Router
from .client import send_message
from .server import run_server
from .atm.atm_client import ATMClient
from .atm.atm_server import ATMServer

def main() -> None:
    parser=argparse.ArgumentParser(
        description="Laboratorio 3 - Link State"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG","INFO","WARNING","ERROR"],
    )
    
    sub=parser.add_subparsers(
        dest="role",
        required=True,
    )
    
    #Router
    router_parser = sub.add_parser("router")
    router_parser.add_argument(
        "--config",
        required=True,
    )
    
    #Cliente genérico
    client_parser = sub.add_parser("client")
    client_parser.add_argument(
        "--config",
        required=True,
    )
    client_parser.add_argument("--to")
    client_parser.add_argument("--message")

    # Servidor genérico
    server_parser = sub.add_parser("server")
    server_parser.add_argument(
        "--config",
        required=True,
    )
    
    # ATM cliente
    atm_client_parser = sub.add_parser(
        "atm-client"
    )

    atm_client_parser.add_argument(
        "--config",
        required=True,
    )

    atm_client_parser.add_argument(
        "--bank",
        default="bank1",
    )

    # ATM servidor
    atm_server_parser = sub.add_parser(
        "atm-server"
    )

    atm_server_parser.add_argument(
        "--config",
        required=True,
    )
        
    args=parser.parse_args()
    configure_logging(args.log_level)
    config=load_config(args.config)
    
    if args.role == "router":
        Router(config).start()

    elif args.role == "client":

        if args.to and args.message is not None:
            send_message(
                config,
                args.to,
                args.message,
            )
        else:
            raise SystemExit(
                "client requiere --to y --message"
            )

    elif args.role == "server":
        run_server(config)

    elif args.role == "atm-client":
        ATMClient(
            config,
            args.bank,
        ).start()
        
    elif args.role == "atm-server":
        ATMServer(config).start()

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        logging.info(
            "Programa detenido por el usuario."
        )

    except Exception as exc:
        logging.exception(
            "Error inesperado: %s",
            exc,
        )

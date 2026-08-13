from __future__ import annotations
import argparse, logging
from .common.config import load_config
from .common.logging_utils import configure_logging
from .router import Router
from .client import send_message
from .server import run_server

def main() -> None:
    parser=argparse.ArgumentParser(description="Laboratorio 3 - Link State")
    parser.add_argument("--log-level",default="INFO",choices=["DEBUG","INFO","WARNING","ERROR"])
    sub=parser.add_subparsers(dest="role",required=True)
    for role in ("router","client","server"):
        p=sub.add_parser(role); p.add_argument("--config",required=True)
        if role=="client": p.add_argument("--to"); p.add_argument("--message")
    args=parser.parse_args(); configure_logging(args.log_level); config=load_config(args.config)
    if args.role=="router": Router(config).start()
    elif args.role=="server": run_server(config)
    elif args.to and args.message is not None: send_message(config,args.to,args.message)
    else: raise SystemExit("client requiere --to y --message")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Programa detenido por el usuario.")
    except Exception as e:
        logging.exception("Error inesperado: %s", e)

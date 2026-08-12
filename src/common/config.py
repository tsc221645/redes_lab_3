"""Carga y validación estricta de configuraciones JSON."""
from __future__ import annotations
import ipaddress, json, os, re
from dataclasses import dataclass
from pathlib import Path

class ConfigError(ValueError): pass

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def _read_dotenv(path: Path) -> dict[str, str]:
    """Lee un .env sencillo sin depender de python-dotenv."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigError(f"línea inválida en {path}:{line_number}")
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                raise ConfigError(f"nombre inválido en {path}:{line_number}")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            values[key] = value
    except OSError as exc:
        raise ConfigError(f"no se pudo leer {path}: {exc}") from exc
    return values

def _config_variables(config_path: Path) -> dict[str, str]:
    """Combina .env del proyecto con variables reales del proceso."""
    candidates = [Path.cwd() / ".env", config_path.parent / ".env"]
    for parent in config_path.parents:
        candidates.append(parent / ".env")
    values: dict[str, str] = {}
    for candidate in dict.fromkeys(candidates):
        values.update(_read_dotenv(candidate))
    values.update(os.environ)  # el entorno del sistema tiene prioridad
    return values

def _expand(value: object, variables: dict[str, str]) -> object:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in variables:
                raise ConfigError(f"variable de entorno no definida: {name}")
            return variables[name]
        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [_expand(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: _expand(item, variables) for key, item in value.items()}
    return value

@dataclass(frozen=True)
class NeighborConfig:
    node_id: str; ip: str; port: int; cost: int

@dataclass(frozen=True)
class NodeConfig:
    node_id: str; listen_ip: str; listen_port: int; role: str
    neighbors: tuple[NeighborConfig, ...] = ()
    hosts: dict = None; attached_hosts: tuple[dict, ...] = (); gateway: dict | None = None

def load_config(path: str | Path) -> NodeConfig:
    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"no se pudo cargar configuración: {exc}") from exc
    raw = _expand(raw, _config_variables(config_path))
    if not isinstance(raw, dict): raise ConfigError("configuración debe ser objeto JSON")
    node_id, role = raw.get("node_id"), raw.get("role")
    if not isinstance(node_id, str) or not node_id or node_id.isspace(): raise ConfigError("node_id inválido")
    if role not in {"router", "client", "server"}: raise ConfigError("role inválido")
    ip = raw.get("listen_ip", "127.0.0.1")
    try: ipaddress.ip_address(ip)
    except ValueError as exc: raise ConfigError("listen_ip inválida") from exc
    port = raw.get("listen_port")
    if not isinstance(port, int) or not 1 <= port <= 65535: raise ConfigError("listen_port inválido")
    neighbors=[]; seen=set()
    for item in raw.get("neighbors", []):
        if not isinstance(item, dict): raise ConfigError("vecino inválido")
        nid=item.get("node_id")
        if not isinstance(nid, str) or not nid or nid == node_id or nid in seen: raise ConfigError("node_id de vecino inválido/repetido")
        seen.add(nid)
        try: ipaddress.ip_address(item["ip"])
        except (KeyError, ValueError) as exc: raise ConfigError("IP de vecino inválida") from exc
        p,c=item.get("port"),item.get("cost")
        if not isinstance(p,int) or not 1<=p<=65535 or not isinstance(c,int) or c<=0: raise ConfigError("puerto/costo de vecino inválido")
        neighbors.append(NeighborConfig(nid,item["ip"],p,c))
    return NodeConfig(node_id,ip,port,role,tuple(neighbors),raw.get("hosts",{}),tuple(raw.get("attached_hosts",[])),raw.get("gateway"))

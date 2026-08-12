# Laboratorio 3 — Link State sobre TCP

Implementación educativa modular en Python 3.11+ de descubrimiento de vecinos, flooding de LSA, LSDB, Dijkstra, forwarding y Hamming(7,4). Solo usa la biblioteca estándar en producción.

## Instalación y estructura

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

`src/protocol` define framing y mensajes; `src/routing` contiene LSDB, Dijkstra y CSV; `src/error_control` implementa Hamming y DATA; `src/router.py` coordina workers; `configs/examples` contiene una topología reproducible.

Las IP se pueden parametrizar con `.env`: copia `.env.example` como `.env` y reemplaza `ROUTER_A_IP`, `ROUTER_B_IP` y `ROUTER_C_IP` por las salidas reales de `tailscale ip -4`. Los JSON usan referencias `${ROUTER_A_IP}`; el cargador las expande sin dependencias externas. El archivo `.env` no debe subirse al repositorio.

## Protocolo

Los mensajes de control son JSON UTF-8 con LF final. DATA es una línea ASCII de bits Hamming. HELLO mantiene vecinos activos; cada cambio genera un LSA versionado y se inunda solo una vez por secuencia. Dijkstra usa los costos anunciados y desempata por el next-hop lexicográficamente menor. El detalle formal está en [docs/protocol.md](docs/protocol.md).

El campo `to` siempre es el host final. `hosts` resuelve host → gateway de router; los routers solo calculan rutas hacia gateways. El enlace router-host usa JSON plano LF, mientras los saltos router-router usan Hamming.

## Ejecución local

Abra tres terminales:

```powershell
python -m src.main router --config configs/examples/router_A.json
python -m src.main router --config configs/examples/router_B.json
python -m src.main router --config configs/examples/router_C.json
```

El grafo A–B–C tiene costo 2 de A a C, frente al enlace directo de costo 5. Se generan `output/A_tabla_enrutamiento.csv`, `output/B_tabla_enrutamiento.csv` y `output/C_tabla_enrutamiento.csv`.

En otra terminal ejecute el servidor y el cliente:

```powershell
python -m src.main server --config configs/examples/server1.json
python -m src.main client --config configs/examples/client1.json --to server1 --message "Hola servidor"
```

## Pruebas distribuidas con Tailscale

Tailscale solo aporta conectividad privada; el programa sigue usando sockets TCP normales y no contiene APIs de Tailscale. Instale y autorice una tailnet, confirme que todos los equipos están Online, obtenga las IP con `tailscale ip -4`, pruebe `ping <tailscale-ip>` o `tailscale ping <device>`, y sustituya en cada JSON `listen_ip` y las IP de `neighbors` por las direcciones 100.x reales. Acuerden los puertos, permita Python en el firewall, arranque los routers, espere convergencia, revise los CSV y pruebe cliente-servidor.

Ejemplo: A `100.101.10.1:5000`, B `100.101.10.2:5000`, C `100.101.10.3:5000`; estos son valores ilustrativos y no deben hardcodearse. No use `127.0.0.1` en una prueba distribuida. Revise Online, firewall, puerto escuchando, IP/puerto de cada vecino y que todas las parejas compartan el mismo formato.

## Tests y límites

```powershell
python -m unittest discover -s tests -v
```

También puede usarse pytest. No se implementan OSPF, autenticación, TLS ni detección fiable de dobles errores de Hamming; Hamming(7,4) corrige errores individuales por bloque.

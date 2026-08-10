# Decisiones de diseño

- TCP + LF evita asumir que `send()` corresponde a `recv()`.
- JSON UTF-8 mantiene mensajes legibles e interoperables.
- LSAs versionados por `seq` evitan flooding duplicado.
- Hamming par se aplica en cada salto router-router.
- `hosts` separa destinos de aplicación de vértices del grafo.
- Dijkstra desempata determinísticamente por next hop.
- CSV se reemplaza atómicamente con `os.replace`.
- Locks protegen LSDB, vecinos y rutas; el socket usa timeout para shutdown.
- Tailscale es únicamente una red IP privada; no es una dependencia.

El formato compartido no usa prefijos CONTROL/DATA para conservar compatibilidad; un prefijo explícito queda como mejora futura.

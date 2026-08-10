# Especificación del protocolo

## Transporte

TCP se interpreta como stream. Cada mensaje termina en LF. Control es una línea JSON UTF-8; DATA es una línea exclusivamente ASCII `0`/`1`. El receptor conserva bytes incompletos y procesa varias líneas por lectura.

## Control

`HELLO {type,from}` y `HELLO_ACK {type,from,to}` verifican vecinos configurados. `LSA {type,origin,seq,links,from}` anuncia únicamente enlaces activos. `seq` aumenta cuando cambia el conjunto local. Se acepta solo un `seq` mayor al almacenado; al reenviar se cambia `from` y se excluye el vecino entrante.

## Rutas y datos

La LSDB forma un grafo dirigido con los costos de los LSA. Dijkstra calcula costo y next hop; los empates eligen el identificador menor. DATA contiene `type=MESSAGE`, `from`, `to`, `hops` y `payload`. Cada router decodifica, incrementa hops, resuelve host a gateway, vuelve a serializar y aplica Hamming antes del siguiente salto. `MAX_HOPS=16`.

## Hosts

`hosts` es el mapping compartido host → gateway. Un gateway entrega a `attached_hosts` mediante JSON plano LF.

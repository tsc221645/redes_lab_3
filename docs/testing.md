# Plan de pruebas

Las pruebas unitarias cubren todos los nibbles y posiciones de error Hamming, Unicode, framing fragmentado y múltiple, LSDB por versión, Dijkstra con rutas indirectas e inalcanzables y CSV con IP/puerto del next hop. La prueba manual local arranca A, B y C, espera HELLO/LSA, revisa los tres CSV, ejecuta servidor y cliente, y detiene un router para observar convergencia.

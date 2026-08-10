# Pruebas distribuidas con Tailscale

1. Cree una tailnet e invite al equipo.
2. Instale/inicie sesión en Tailscale y confirme dispositivos Online.
3. Use `tailscale ip -4` para obtener la IP 100.x de cada máquina.
4. Compruebe `ping` o `tailscale ping` y abra el puerto TCP en el firewall.
5. Cambie únicamente los JSON: `listen_ip` y las IP/puertos de `neighbors`.
6. Arranque routers, espere convergencia, valide CSV y ejecute cliente/servidor.

Ejemplo de enlace: A `100.101.10.1:5000` → B `100.101.10.2:5000` → C `100.101.10.3:5000`. Son direcciones de ejemplo. Si falla, revise Online, `127.0.0.1` accidental, puerto escuchando, firewall y que los vecinos apunten al puerto correcto. El código no hardcodea ni consume APIs de Tailscale.

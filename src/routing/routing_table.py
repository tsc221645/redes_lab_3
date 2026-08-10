from __future__ import annotations
import csv, os
from pathlib import Path
from .dijkstra import Route
from ..common.config import NeighborConfig

def write_csv(node_id: str, routes: dict[str,Route], neighbors: dict[str,NeighborConfig], output_dir: str|Path="output") -> Path:
    directory=Path(output_dir); directory.mkdir(parents=True,exist_ok=True)
    target=directory/f"{node_id}_tabla_enrutamiento.csv"; temp=target.with_suffix(".tmp")
    with temp.open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f); writer.writerow(["destino","siguiente_salto","ip","puerto","costo"])
        for dest,route in sorted(routes.items()):
            n=neighbors.get(route.next_hop)
            if n: writer.writerow([dest,route.next_hop,n.ip,n.port,route.cost])
        f.flush(); os.fsync(f.fileno())
    os.replace(temp,target); return target

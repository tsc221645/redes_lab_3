from __future__ import annotations
import heapq
from dataclasses import dataclass
from .lsdb import LSARecord

@dataclass(frozen=True)
class Route:
    next_hop: str; cost: int

def shortest_routes(local: str, records: dict[str,LSARecord]) -> dict[str,Route]:
    graph={origin:list(rec.links) for origin,rec in records.items()}
    dist={local:0}; first={}; heap=[(0,local,local)]
    while heap:
        cost, _, node = heapq.heappop(heap)
        if cost != dist.get(node): continue
        for target, edge in graph.get(node,[]):
            new=cost+edge; hop=target if node==local else first[node]
            old=dist.get(target); oldhop=first.get(target)
            if old is None or new<old or (new==old and hop<oldhop):
                dist[target]=new; first[target]=hop; heapq.heappush(heap,(new,hop,target))
    return {dest:Route(first[dest],dist[dest]) for dest in dist if dest != local}

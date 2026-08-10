from __future__ import annotations
from dataclasses import dataclass
from threading import RLock

@dataclass(frozen=True)
class LSARecord:
    origin: str; seq: int; links: tuple[tuple[str,int], ...]

class LSDB:
    def __init__(self, self_id: str): self.self_id, self._records, self._lock = self_id, {}, RLock()
    def accept(self, lsa: dict) -> bool:
        origin, seq, links = lsa.get("origin"), lsa.get("seq"), lsa.get("links")
        if not isinstance(origin,str) or origin == self.self_id or not isinstance(seq,int) or seq < 0 or not isinstance(links,list): return False
        normalized=[]
        for link in links:
            if not isinstance(link,dict) or not isinstance(link.get("to"),str) or not isinstance(link.get("cost"),int) or link["cost"]<=0: return False
            normalized.append((link["to"],link["cost"]))
        with self._lock:
            if seq <= self._records.get(origin, LSARecord(origin,-1,())).seq: return False
            self._records[origin]=LSARecord(origin,seq,tuple(normalized)); return True
    def set_local(self, seq: int, links: list[dict]) -> None:
        with self._lock: self._records[self.self_id]=LSARecord(self.self_id,seq,tuple((x["to"],x["cost"]) for x in links))
    def snapshot(self) -> dict[str, LSARecord]:
        with self._lock: return dict(self._records)

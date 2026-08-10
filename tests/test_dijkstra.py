import unittest
from src.routing.dijkstra import shortest_routes
from src.routing.lsdb import LSARecord

class DijkstraTests(unittest.TestCase):
    def test_indirect_and_tie(self):
        records={"A":LSARecord("A",1,(("B",1),("C",5))),"B":LSARecord("B",1,(("A",1),("C",1))),"C":LSARecord("C",1,(("A",5),("B",1)))}
        r=shortest_routes("A",records); self.assertEqual((r["C"].next_hop,r["C"].cost),("B",2))
    def test_unreachable(self): self.assertNotIn("Z",shortest_routes("A",{"A":LSARecord("A",1,())}))

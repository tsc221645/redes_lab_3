import tempfile, unittest
from pathlib import Path
from src.routing.dijkstra import Route
from src.routing.routing_table import write_csv
from src.common.config import NeighborConfig

class TableTests(unittest.TestCase):
    def test_next_hop_csv(self):
        with tempfile.TemporaryDirectory() as d:
            path=write_csv("A",{"C":Route("B",2)},{"B":NeighborConfig("B","127.0.0.1",5001,1)},d)
            self.assertIn("C,B,127.0.0.1,5001,2",Path(path).read_text())

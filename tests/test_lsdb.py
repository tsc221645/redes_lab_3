import unittest
from src.routing.lsdb import LSDB

class LSDBTests(unittest.TestCase):
    def test_versions_and_self(self):
        db=LSDB("A"); l={"origin":"B","seq":1,"links":[]}; self.assertTrue(db.accept(l)); self.assertFalse(db.accept(l)); self.assertFalse(db.accept({**l,"seq":0})); self.assertFalse(db.accept({**l,"origin":"A","seq":2}))

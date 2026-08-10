import unittest
from src.error_control.serialization import *

class SerializationTests(unittest.TestCase):
    def test_roundtrip(self):
        for payload in ("ASCII", "áé🚀", ""):
            p={"type":"MESSAGE","from":"c","to":"s","hops":0,"payload":payload}
            self.assertEqual(deserialize_packet(serialize_packet(p)),p)

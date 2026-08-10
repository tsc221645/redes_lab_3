import unittest
from src.protocol.framing import LineBuffer, classify_line

class FramingTests(unittest.TestCase):
    def test_split_and_multiple(self):
        b=LineBuffer(); self.assertEqual(b.feed(b'{"a"'),[]); self.assertEqual(b.feed(b":1}\n01\n"),[b'{"a":1}',b'01']); self.assertEqual(classify_line(b'01'),"data")

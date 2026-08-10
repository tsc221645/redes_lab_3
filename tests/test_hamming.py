import unittest
from src.error_control.hamming import *

class HammingTests(unittest.TestCase):
    def test_all_nibbles(self):
        for n in range(16):
            bits=f"{n:04b}"; self.assertEqual(decode_codeword(encode_nibble(bits)).data_bits,bits)
    def test_single_bit_errors(self):
        for n in range(16):
            word=encode_nibble(f"{n:04b}")
            for pos in range(7):
                bad=word[:pos]+("1" if word[pos]=="0" else "0")+word[pos+1:]
                self.assertEqual(decode_codeword(bad).data_bits,f"{n:04b}")
    def test_invalid(self):
        with self.assertRaises(HammingError): encode_nibble("000")
        with self.assertRaises(HammingError): decode_bits("010")

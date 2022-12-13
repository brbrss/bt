import unittest
from writer import Writer


class WriterTest(unittest.TestCase):

    def test_keepalive(self):
        self.assertEqual(Writer().keep_alive(), b'\x00\x00\x00\x00')

    def test_chock(self):
        self.assertEqual(Writer().chock(), b'\x00\x00\x00\x01\x00')
    def test_unchock(self):
        self.assertEqual(Writer().unchock(), b'\x00\x00\x00\x01\x01')

    def test_bitfield(self):
        a = [False,True,True,True,False,False,False,True]
        s = '01110001'
        res = Writer().bitfield(a)
        self.assertEqual(res[:5], b'\x00\x00\x00\x02\x05')
        self.assertEqual(res[5], 113)
            
    def test_bitfield_13(self):
        s = '01110001' + '10011'
        a = [c=='1' for c in s]
        res = Writer().bitfield(a)
        self.assertEqual(res[:5], b'\x00\x00\x00\x03\x05')
        self.assertEqual(res[5], 113)
        self.assertEqual(res[6], 152)


        
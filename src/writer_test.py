import unittest
from writer import Writer
import random


class WriterTest(unittest.TestCase):

    def test_handshake(self):
        info_hash = b'1234512345abcdeabcde'
        peerid = b'abcde12345abcde12345'
        res = Writer().handshake(info_hash, peerid)
        target = b'\x13BitTorrent protocol\x00\x00\x00\x00\x00\x00\x00\x00' \
            + info_hash + peerid
        self.assertEqual(res, target)

    def test_keepalive(self):
        self.assertEqual(Writer().keep_alive(), b'\x00\x00\x00\x00')

    def test_choke(self):
        self.assertEqual(Writer().choke(), b'\x00\x00\x00\x01\x00')

    def test_unchoke(self):
        self.assertEqual(Writer().unchoke(), b'\x00\x00\x00\x01\x01')

    def test_bitfield(self):
        a = [False, True, True, True, False, False, False, True]
        s = '01110001'
        res = Writer().bitfield(a)
        self.assertEqual(res[:5], b'\x00\x00\x00\x02\x05')
        self.assertEqual(res[5], 113)

    def test_bitfield_13(self):
        s = '01110001' + '10011'
        a = [c == '1' for c in s]
        res = Writer().bitfield(a)
        self.assertEqual(res[:5], b'\x00\x00\x00\x03\x05')
        self.assertEqual(res[5], 113)
        self.assertEqual(res[6], 152)

    def test_block(self):
        N = 1024*57+107
        data = bytes([random.randint(0, 255) for i in range(N)])
        res = Writer().piece(77, 13, data)
        self.assertEqual(int.from_bytes(res[0:4], 'big'), 9+N)
        self.assertEqual(res[4], 7)
        self.assertEqual(int.from_bytes(res[5:9], 'big'), 77)
        self.assertEqual(int.from_bytes(res[9:13], 'big'), 13)
        self.assertEqual(res[13:], data)


if __name__ == '__main__':
    unittest.main()

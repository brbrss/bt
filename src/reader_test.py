import unittest
from writer import Writer
import random
from reader import Reader


class MockReader(Reader):
    def __init__(self):
        super().__init__()
        self.output = []

    def on_handshake(self, info_hash, peerid):
        self.output.append(['handshake', info_hash, peerid])

    def on_choke(self):
        self.output.append(['choke'])
    def on_unchoke(self):
        self.output.append(['unchoke'])
    def on_bitfield(self, field):
        self.output.append(['bitfield', field])

    def on_piece(self, index, begin, data):
        self.output.append(['piece', index, begin, data])

    def on_badtype(self):
        self.output.append(['badtype'])


class ReaderTest(unittest.TestCase):

    def test_handshake(self):
        info_hash = b'1234512345abcdeabcde'
        peerid = b'abcde12345abcde12345'
        data = b'\x13BitTorrent protocol\x00\x00\x00\x00\x00\x00\x00\x00' \
            + info_hash + peerid
        reader = MockReader()
        reader.read(data)
        self.assertEqual(reader.output, [['handshake', info_hash, peerid]])

    def test_keepalive(self):
        b = b'\x00\x00\x00\x00' * 3
        reader = MockReader()
        reader.handshake_flag = True
        reader.read(b[0:1])
        reader.read(b[1:3])
        reader.read(b[3:])
        self.assertEqual(reader.output, [])

    def test_many(self):

        info_hash = b'1234512345abcdeabcde'
        peerid = b'abcde12345abcde12345'
        data = b'\x13BitTorrent protocol\x00\x00\x00\x00\x00\x00\x00\x00' \
            + info_hash + peerid
        # handshake 49
        data += b'\x00\x00\x00\x00'  # keepalive  4
        data += b'\x00\x00\x00\x01\x01'  # unchoke  5
        data += b'\x00\x00\x00\x03\x05' + bytes([113, 152])  # bitfield  7

        N = 1024*57+107
        block = bytes([i % 256 for i in range(N)])
        data += int.to_bytes(9+N, 4, 'big') + b'\x07' \
            + int.to_bytes(77, 4, 'big') + int.to_bytes(13, 4, 'big')\
            + block
        # piece / 9+N+4
        reader = MockReader()
        for i in range(len(data)):
            reader.read(data[i:i+1])
            bf = [c=='1' for c in '01110001'+'10011000']
        self.assertEqual(reader.output[0][0], 'handshake')
        self.assertEqual(reader.output[1][0], 'unchoke')
        self.assertEqual(reader.output[2], ['bitfield',bf])
        self.assertEqual(reader.output[3], ['piece',77,13,block])

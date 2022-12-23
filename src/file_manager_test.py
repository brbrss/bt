
import unittest
from file_manager import FileManager
import ben


class MockChain(object):
    def __init__(self):
        self.d = {}

    def write(self, offset, s):
        self.d[offset] = s
        pass


class FileManagerTest(unittest.TestCase):

    def test_init(self):
        fp = './resource/gatsby.torrent'
        folder = './resource'
        d = ben.parse_file(fp)
        FileManager(d['info'], folder)

    def test_create(self):
        d = {'files': [{'length': 13, 'path': ['haha', 'a.txt']}, {
            'length': 29, 'path': ['b.txt']}]}
        d['piece length'] = 256*1024
        d['pieces'] = '\x00'*20
        d['name'] = 'fmtest'
        folder = './resource'
        FileManager(d, folder)

    def test_verify(self):
        BLOCK_LEN = 16*1024
        d = ben.parse_file('./resource/gatsby2.torrent')
        fm = FileManager(d['info'], './resource')
        fm.cf.close()
        fm.cf = MockChain()
        piece_length = d['info']['piece length']
        f = open('./resource/gatsby.txt', 'rb')
        for i in range(piece_length//BLOCK_LEN):
            s = f.read(BLOCK_LEN)
            fm.buffer[0][i*BLOCK_LEN] = s
        f.close()
        fm.varify_piece(0)

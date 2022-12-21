
import unittest
from file_manager import FileManager
import ben


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
        d['pieces'] = b'\x00'*20
        d['name'] = 'fmtest'
        folder = './resource'
        FileManager(d, folder)

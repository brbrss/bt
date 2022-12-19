
import unittest
from file_manager import FileManager
import ben


class FileManagerTest(unittest.TestCase):

    def test_init(self):
        fp = './resource/gatsby.torrent'
        folder = './resource'
        d = ben.parse_file(fp)
        FileManager(d['info'], folder)

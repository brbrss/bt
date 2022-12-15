
import unittest
from torrent import Torrent, parse_peer


class TorrentTest(unittest.TestCase):

    def test_init(self):
        fp = './resource/gatsby.torrent'
        t = Torrent(fp)
        self.assertEqual(t.announce, 'http://127.0.0.1:6969/announce')

    def test_parse(self):
        s = '\x87\x00\x92¹\x1aá'
        res = parse_peer(s)
        self.assertEqual(res,  [((135, 0, 146, 185), 6881)])

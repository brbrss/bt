
import unittest
from torrent import Torrent


#LEVITTOWN = './resource/levittown.torrent'
TMULTI = './resource/hasthree.torrent'

def NOFUN(): return None


class MockPeer(object):
    def __init__(self):
        self.interested = False
        self.choke = True
        self.remote_pieces = set()
        self.local_request = set()
        self.d = 0

    def set_interest(self, x):
        self.interested = x

    def set_choke(self, x):
        self.choke = x

    def d_rate(self):
        return self.d

    def add_request(self, res):
        self.local_request.add(res)


class TorrentTest(unittest.TestCase):

    def test_init(self):
        fp = './resource/gatsby.torrent'
        t = Torrent(fp, '')
        self.assertEqual(t.announce, 'http://127.0.0.1:6969/announce')
        self.assertEqual(t._default_piece_length, 262144)

    def test_interested(self):
        fp = './resource/gatsby.torrent'
        t = Torrent(fp, './resource')
        t.start(lambda: None)
        p1 = MockPeer()
        p2 = MockPeer()
        p1.remote_pieces.add(2)
        t.peer_map[((1, 2, 3, 4), 7890)] = p1
        t.peer_map[((2, 2, 3, 4), 7890)] = p2
        t.decide_interest()
        self.assertEqual(p1.interested, True)
        self.assertEqual(p2.interested, False)
        t.close()

    def test_choke(self):
        fp = './resource/gatsby.torrent'
        t = Torrent(fp, '')
        plist = []
        for i in range(30):
            p = MockPeer()
            p.d = 30.0-i
            plist.append(p)
            t.peer_map[((i, 2, 3, 4), 7890)] = p

        t.decide_choke()
        self.assertEqual(plist[0].choke, False)
        n_unchoke = len([0 for p in plist if not p.choke])
        self.assertEqual(n_unchoke, 5)

    def test_choke_0(self):
        fp = './resource/gatsby.torrent'
        t = Torrent(fp, '')

        t.decide_choke()

    def test_choke_1(self):
        fp = './resource/gatsby.torrent'
        t = Torrent(fp, '')
        plist = []
        for i in range(1):
            p = MockPeer()
            p.d = 30.0-i
            plist.append(p)
            t.peer_map[((i, 2, 3, 4), 7890)] = p
        t.decide_choke()
        self.assertEqual(plist[0].choke, False)

    def test_request_1(self):
        t = Torrent(TMULTI, './resource/test/torrent_test')
        t.start(lambda: None)
        plist = []
        for i in range(10):
            p = MockPeer()
            p.d = 30.0-i
            plist.append(p)
            t.peer_map[((i, 2, 3, 4), 7890)] = p
        plist[0].remote_pieces.add(6)
        t.decide_request(plist[0])
        self.assertEqual(plist[0].local_request.pop(), (6, 0, 16384))
        t.close()

    def test_request_queue(self):
        t = Torrent(TMULTI, './resource/test/torrent_test')
        t.start(NOFUN)
        # t.content_buffer[41][0] = b'0'*16384
        # t.content_buffer[41][1] = b'0'*16384
        # t.content_buffer[41][2] = b'0'*16384
        s = b'0'*16384
        t.add_data(6, 0, s)
        t.add_data(6, 1, s)
        t.add_data(6, 2, s)
        plist = []
        for i in range(5):
            p = MockPeer()
            p.remote_pieces.add(6)
            p.local_request.add((6, i+3, 16384))
            p.d = 30.0-i
            plist.append(p)
            t.peer_map[((i, 2, 3, 4), 7890)] = p
        plist[0].remote_pieces.add(6)
        res = t.decide_request(plist[0])
        self.assertEqual(plist[0].local_request.pop(), (6, 8, 16384))

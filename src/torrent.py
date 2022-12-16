import ben
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import random

BLOCK_SIZE = 16384


def rand_id():
    '''random 20 byte id'''
    s = b'-000000-'
    s += bytes([random.randint(b'0'[0], b'9'[0]) for i in range(20-len(s))])
    return s


def parse_peer(s):
    if type(s) is not bytes:
        s = bytes(s, 'latin1')
    len_s = len(s)
    if len_s % 6 != 0:
        raise RuntimeError('length of peer str not multiple of 6')
    res = []
    for n in range(len_s//6):
        k = n * 6
        ip = tuple(s[k:k+4])
        port = s[k+4]*256+s[k+5]
        res.append((ip, port))
    return res


class Torrent(object):
    def _read_meta(self, fp):
        data = ben.parse_file(fp)
        self.announce = data['announce']
        self.info = data['info']
        self.piece_length = data['info']['piece length']
        if len(self.info['pieces']) % 20 != 0:
            raise RuntimeError('length of pieces not multiple of 20')
        self.pieces_hash = [data['info']['pieces'][i*20:1*20+20]
                            for i in range(len(self.info['pieces']) // 20)]
        infostr = bytes(ben.encode(self.info), 'latin1')
        sha1 = hashlib.sha1()
        sha1.update(infostr)
        self.info_hash = sha1.digest()  # bytes
        if 'length' in self.info:
            self.length = self.info['length']
        elif 'files' in self.info:
            self.length = sum([fl['length'] for fl in self.info['files']])

    def __init__(self, fp):
        self.announce = None
        self.info = None
        self.info_hash = None
        self.pieces_hash = None
        self.length = None
        self.peerid = rand_id()
        self._read_meta(fp)
        self.content_buffer = [{} for i in self.pieces_hash]
        self.content = [{} for i in self.pieces_hash]
        self.peer_map = {}
        self.tracker_map = {}

    def req_data(self):
        data = {
            'info_hash': self.info_hash,
            'peer_id': 'ab123456781234567890',
            'port': 6881,
            'uploaded': '0',
            'downloaded': '0',
            'left': str(self.length)
        }
        return data

    def tracker_get(self, url):
        data = urllib.parse.urlencode(self.req_data())
        req = urllib.request.Request(url+'?'+data, method='GET')
        res = None
        try:
            res = urllib.request.urlopen(req)
            s = res.read()
            s = str(s, 'latin1')
            self.tracker_map[url] = ben.parse(s)
        except urllib.error.HTTPError as err:
            self.tracker_map[url] = {'err': err.read()}

    def add_peer(self, ip, port):
        self.peer_map[(ip, port)] = None

    def add_data(self, piece_index, begin, data):
        if len(data) == BLOCK_SIZE:
            self.content_buffer[piece_index][begin] = data

    def varify_piece(self, piece_index):
        d = self.content_buffer[piece_index]
        gap = []
        next_pos = 0
        s = b''
        for k in d.keys():
            kk = k
            if k > next_pos:
                gap.append(next_pos, k-next_pos)
            elif k < next_pos:
                kk = next_pos
                s += d[k][kk-k:]
            else:  # equal
                s += d[k][kk-k:]
            next_pos = k + len(d[k])
        if gap == []:
            sha1 = hashlib.sha1()
            sha1.update(s)
            hash = sha1.digest()
            self.content_buffer[piece_index] = {}
            if hash == self.pieces_hash[piece_index]:
                self.content[piece_index] = s
                return True
            else:
                return False
        else:
            return gap

    def has_piece(self, piece_index):
        return piece_index in self.content

    def get_data(self, piece_index, begin, length):
        return self.conent[piece_index][begin:begin+length]

    def decide_interest(self):
        for k in self.peer_map:
            peer = self.peer_map[k]
            possible_pieces = [
                i for i in peer.remote_pieces if not self.has_piece(i)]
            res = len(possible_pieces) > 0
            peer.set_interest(res)
        return

    def decide_choke(self):
        '''choking and interest on peers'''
        def f(k): return self.peer_map[k].d_rate()
        rate_ranking = sorted(self.peer_map.keys(), f, reverse=True)
        for k in self.peer_map:
            p = self.peer_map[k]
            p.d_rate()
        i = 0
        num_peers = len(rate_ranking)
        while i < num_peers:
            k = rate_ranking[i]
            if i < 4:
                self.peer_map[k].set_choke(True)
            else:
                self.peer_map[k].set_choke(False)
        if num_peers > 4:
            optim = random.randint(4, num_peers-1)
            k = rate_ranking[optim]
            self.peer_map[k].set_choke(True)
        return

    def decide_request(self, peer):
        '''which peer to request'''
        total = set()
        for k in self.peer_map:
            total = total.union(self.peer_map[k].local_request)
        pending = [i for i in self.content_buffer if self.content_buffer[i]]
        num_block = self.piece_length / BLOCK_SIZE
        priority_pieces = peer.remote_pieces.intersection(set(pending))
        for i in priority_pieces:
            for k in range(num_block):
                b1 = k in self.content_buffer[i]
                b2 = (i, k, BLOCK_SIZE) in total
                if not b1 and not b2:
                    return (i, k, BLOCK_SIZE)
        # no available pending piece
        possible_pieces = [
            i for i in peer.remote_pieces if not self.has_piece(i)]
        if not possible_pieces:
            return None
        i = random.choice(possible_pieces)
        return (i, 0, BLOCK_SIZE)

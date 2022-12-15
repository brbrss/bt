from . import ben
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import random


def rand_id():
    '''random 20 byte id'''
    s = b'-000000-'
    s += bytes([random.randint(b'0'[0], b'9'[0]) for i in range(20-len(s))])
    return s


class Torrent(object):
    def _read_meta(self, fp):
        data = ben.parse_file(fp)
        self.announce = data['announce']
        self.info = data['info']
        if len(self.info['pieces']) % 20 != 0:
            raise RuntimeError('length of pieces not multiple of 20')
        self.pieces_hash = [data['info']['pieces'][i*20:1*20+20]
                            for i in range(len(self.info['pieces'] // 20))]
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

import time
import ben
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import random
import math
import tracker
import threading
from file_manager import FileManager
from server import Server


BLOCK_SIZE = 16384


def rand_id():
    '''random 20 byte id'''
    s = b'-000000-'
    s += bytes([random.randint(b'0'[0], b'9'[0]) for i in range(20-len(s))])
    return s


class Torrent(object):
    def _read_meta(self, fp):
        '''read data from torrent file'''
        data = ben.parse_file(fp)
        self.announce = data['announce']
        self.info = data['info']
        self._default_piece_length = data['info']['piece length']
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

    def __init__(self, fp, folder):
        self.savefolder = folder
        # meta data
        self.announce: str = None
        self.info = None
        self.info_hash = None
        self.pieces_hash = None
        self.length = None
        self.peerid = rand_id()
        self._read_meta(fp)
        # data
        #self.content_buffer = [{} for i in self.pieces_hash]
        #self.content = [{} for i in self.pieces_hash]
        # remote data
        self.peer_map = {}
        self.tracker_map: dict[str, tracker.Tracker] = {}
        self.tracker_map[self.announce] = tracker.Tracker(
            {'err': 'not initialized'})
        self.lock_tracker = threading.Lock()
        # strategy data
        self.last_choke_time = 0  # last time changing choke
        self.last_interest_time = 0  # last time changing interest
        self.fm = None

    def start(self, server_cb):
        '''server_cb callback for registering server socket'''
        # tool
        self.fm = FileManager(self.info, self.savefolder)
        self.server = Server(0)  # let os select port
        def f(): return self.server.start(server_cb)
        self.thread = threading.Thread(target=f)
        self.tracker_get(self.announce, 'started')

    def close(self):
        self.tracker_get(self.announce, 'stopped')
        self.fm.close()
        self.server.stop()

    def req_query(self):
        data = {
            'info_hash': self.info_hash,
            'peer_id': self.peerid,
            'port': self.server.port,
            'uploaded': '0',
            'downloaded': '0',
            'left': str(self.length)
        }
        return data

    def tracker_get(self, url, event=''):
        '''Send http request to tracker and store parsed response
        in self.tracker_map'''
        if event not in ['started', 'completed', 'stopped', '']:
            raise RuntimeError('invalid event: ' + str(event))
        query = self.req_query()
        if event:
            query['event'] = event
        data = urllib.parse.urlencode(query)
        req = urllib.request.Request(url+'?'+data, method='GET')
        res = None
        try:
            res = urllib.request.urlopen(req)
            s = res.read()
            s = str(s, 'latin1')
            res = ben.parse(s)
        except urllib.error.HTTPError as err:
            res = {'err': err.read()}
        except Exception as err:
            res = {'err': err.__repr__()}
        self.lock_tracker.acquire()
        self.tracker_map[url] = tracker.Tracker(res)  # should not throw
        self.lock_tracker.release()

    def add_peer(self, ip, port, peer):
        ''' xxx '''
        self.peer_map[(ip, port)] = peer

    def add_data(self, piece_index, begin, data):
        return self.fm.add_block(piece_index, begin, data)

    def has_piece(self, piece_index):
        return self.fm.has_piece(piece_index)

    def get_data(self, piece_index, begin, length):
        return self.fm.get_block(piece_index, begin, length)

    def decide_interest(self):
        self.last_interest_time = time.time()
        for k in self.peer_map:
            peer = self.peer_map[k]
            possible_pieces = [
                i for i in peer.remote_pieces if not self.has_piece(i)]
            res = len(possible_pieces) > 0
            peer.set_interest(res)
        return

    def decide_choke(self):
        '''choking on peers'''
        self.last_choke_time = time.time()
        def f(k): return self.peer_map[k].d_rate()
        rate_ranking = sorted(self.peer_map.keys(), key=f, reverse=True)
        for k in self.peer_map:
            p = self.peer_map[k]
            p.d_rate()
        i = 0
        num_peers = len(rate_ranking)
        while i < num_peers:
            k = rate_ranking[i]
            if i < 4:
                self.peer_map[k].set_choke(False)
            else:
                self.peer_map[k].set_choke(True)
            i += 1
        if num_peers > 4:
            optim = random.randint(4, num_peers-1)
            k = rate_ranking[optim]
            self.peer_map[k].set_choke(False)
        return

    def decide_request(self, peer):
        res = self._decide_request(peer)
        if res:
            peer.add_request(res)
        return

    def _decide_request(self, peer):
        '''what to request from peer'''
        total = set()
        for k in self.peer_map:
            total = total.union(self.peer_map[k].local_request)
        # pending = [i for i in range(
        #     len(self.content_buffer)) if self.content_buffer[i]]
        pending = self.fm.get_partial()
        priority_pieces = peer.remote_pieces.intersection(set(pending))
        for i in priority_pieces:
            num_block = self._num_block(i)
            for k in range(num_block):
                #b1 = k in self.content_buffer[i]
                block_len = self._block_length(i, k)
                b1 = k in self.fm.buffer[i]
                b2 = (i, k, block_len) in total
                if not b1 and not b2:
                    return (i, k, block_len)
        # no available pending piece
        possible_pieces = [
            i for i in peer.remote_pieces if not self.has_piece(i)]
        if not possible_pieces:
            return None
        i = random.choice(possible_pieces)
        return (i, 0, self._block_length(i, 0))

    def _block_length(self, piece_id, block_id):
        x = self._piece_length(piece_id)
        t = x - block_id * BLOCK_SIZE
        return min(t, BLOCK_SIZE)

    def _num_block(self, piece_id):
        return math.ceil(self._piece_length(piece_id) / BLOCK_SIZE)

    def _piece_length(self, piece_id):
        tail = self.length - piece_id * self._default_piece_length
        return min(tail, self._default_piece_length)

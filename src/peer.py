from conn_pool import ConnOperator
from writer import Writer
import socket
import time
from torrent import Torrent
from reader import Reader
from ratecounter import RateCounter


class MyReader(Reader):
    def __init__(self, peer):
        super().__init__()
        self.peer = peer

    def on_handshake(self, info_hash, peerid):
        self.peer.on_handshake(info_hash, peerid)

    def on_keepalive(self):
        self.peer.on_keepalive()

    def on_choke(self):
        self.peer.on_choke()

    def on_unchoke(self):
        self.peer.on_unchoke()

    def on_interested(self):
        self.peer.on_interested()

    def on_notinterested(self):
        self.peer.on_notinterested()

    def on_have(self, index):
        self.peer.on_have(index)

    def on_bitfield(self, field):
        self.peer.on_bitfield(field)

    def on_request(self, index, begin, length):
        self.peer.on_request(index, begin, length)

    def on_piece(self, index, begin, data):
        self.peer.on_piece(index, begin, data)

    def on_cancel(self, index, begin, length):
        self.peer.on_cancel(index, begin, length)

    def on_port(self, listen_port):
        self.peer.on_port(listen_port)

    def on_badtype(self):
        '''Called when incoming data is not valid'''
        self.peer.on_badtype()


class Peer(ConnOperator):
    def __init__(self, conn: socket.socket, torrent: Torrent, is_initiating):
        super().__init__(conn)
        # ref
        self.torrent = torrent
        self.conn = conn
        self.info_hash = torrent.info_hash
        self.local_id = torrent.peerid
        # status
        self.remote_choke = True
        self.remote_interested = False
        self.remote_id = None
        self.local_choke = True
        self.local_interested = False
        self.remote_last_active_time = time.time()
        self.local_last_active_time = time.time()
        # stat
        self.d_total = 0
        self.u_total = 0
        self.rate_counter = RateCounter(10)  # use 10 second average
        # data
        self.write_buf = b''
        # which pieces local has notified remote
        self.local_pieces: set[int] = set()
        self.remote_pieces: set[int] = set()  # which pieces remote has
        self.remote_request = set()
        self.local_request = set()
        # tools
        self.reader = MyReader(self)
        self.writer = Writer()
        # init
        if is_initiating:
            pass
        self.write_buf += self.writer.handshake(self.info_hash, self.local_id)

    def parse(self, buf):
        self.remote_last_active_time = time.time()
        self.reader.read(buf)

    def _check_have(self):
        num_pieces = len(self.torrent.pieces_hash)
        for i in range(num_pieces):
            if self.torrent.has_piece(i) and i not in self.local_pieces:
                self.write_buf += self.writer.have(i)
                self.local_pieces.add(i)

    def _check_keepalive(self):
        if time.time() - self.last_send_time > 60 and len(self.write_buf) == 0:
            self.write_buf += self.writer.keep_alive()

    def _check_send_block(self):
        MAX_BUFFER_SIZE = 128*1024
        if len(self.remote_request) == 0:
            return
        while len(self.write_buf) < MAX_BUFFER_SIZE and len(self.remote_request) > 0:
            index, begin, length = self.remote_request.pop()
            if self.torrent.has_piece(index):
                block = self.torrent.get_data(index, begin, length)
                self.write_buf += self.writer.piece(index, begin, block)
                self.u_total += length

    def add_to_write(self):
        if self.write_buf:
            return
        self._check_send_block()
        self._check_have()
        self._check_keepalive()
        return

    ### for use from Torrent class ###

    def d_rate(self):
        return self.rate_counter.rate

    # no safety issue for commands
    # should only be called after select

    def set_choke(self, x):
        if self.local_choke == x:
            return
        self.local_choke = x
        if x:
            msg = self.writer.choke()
        else:
            msg = self.writer.unchoke()
        self.write_buf += msg

    def set_interest(self, x):
        if self.local_interested == x:
            return
        self.local_interested = x
        if x:
            msg = self.writer.interested()
        else:
            msg = self.writer.uninterested()
        self.write_buf += msg

    def add_request(self, req_data):
        self.local_request.add(req_data)
        msg = self.writer.request(req_data[0], req_data[1], req_data[2])
        self.write_buf += msg
    ### callbacks ###

    def on_handshake(self, info_hash, peerid):
        if (info_hash != self.info_hash):
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        self.remote_id = peerid

    def on_keepalive(self):
        return

    def on_choke(self):
        self.remote_choke = True
        self.local_request.clear()  # cancel my more requests

    def on_unchoke(self):
        self.remote_choke = False

    def on_interested(self):
        self.remote_interested = True

    def on_notinterested(self):
        self.remote_interested = False

    def on_have(self, index):
        self.remote_pieces.add(index)

    def on_bitfield(self, field):
        for i in range(len(field)):
            if field[i]:
                self.remote_pieces.add(i)

    def on_request(self, index, begin, length):
        '''According to bep_0003:

        'request' messages contain an index, begin, and length. The last two 
        are byte offsets. Length is generally a power of two unless it gets 
        truncated by the end of the file. All current implementations use
        2^14 (16 kiB), and close connections which request an amount greater
        than that.'''

        if length > 16384:
            self.on_badtype()
            return
        self.remote_request.add((index, begin, length))

    def on_piece(self, index, begin, data):
        length = len(data)
        k = (index, begin, length)
        if not k in self.local_request:
            return
        else:
            # pass to Torrent obj
            self.torrent.add_data(index, begin, data)
            self.local_request.remove(k)
            self.rate_counter.add(length)
            self.torrent.decide_request(self)

    def on_cancel(self, index, begin, length):
        self.remote_request.remove((index, begin, length))

    def on_port(self, listen_port):
        # ignore
        return

    def on_badtype(self, msg=''):
        '''Called when incoming data is not valid'''
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()

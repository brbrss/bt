from conn_pool import ConnOperator
from writer import Writer
import socket
import time
from torrent import Torrent
from reader import Reader


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
        super().__init__()
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
        self.last_active_time = time.time()
        # data
        self.remote_pieces = set()  # which pieces remote has
        self.remote_request = set()
        self.local_request = set()
        # tools
        self.reader = MyReader(self)
        self.writer = Writer()
        # init
        if is_initiating:
            self.write_buf = self.writer.handshake(self.info_hash, self.peerid)

    def parse(self, buf):
        self.last_active_time = time.time()
        self.reader.read(buf)

    def add_to_write(self):
        # xxx what to write?
        pass

    def on_handshake(self, info_hash, peerid):
        if (info_hash != self.info_hash):
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        self.remote_id = peerid

    def on_keepalive(self):
        return

    def on_choke(self):
        self.remote_choke = True

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
        # pass to Torrent obj
        self.torrent.add_data(index, begin, data)

    def on_cancel(self, index, begin, length):
        self.remote_request.remove((index, begin, length))

    def on_port(self, listen_port):
        # ignore
        return

    def on_badtype(self):
        '''Called when incoming data is not valid'''
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()
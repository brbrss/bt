import struct


# 0 - choke
# 1 - unchoke
# 2 - interested
# 3 - not interested
# 4 - have
# 5 - bitfield
# 6 - request
# 7 - piece
# 8 - cancel

CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOTINTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
CANCEL = 8
PORT = 9


def bytes_to_bool(b):
    res = []
    for c in b:
        for i in range(8):
            mask = 1 << 7-i
            res.append(c & mask != 0)
    return res


class Reader(object):
    '''This class reads bytes and call on_* methods when
    it finishes reading a message.

    Must subclass this class and provie on_* callback to use.'''

    def __init__(self):
        self.handshake_data = b''
        self.handshake_len = None
        self.handshake_flag = False  # whether handshake finished
        self.reset_msg()

    def reset_msg(self):
        self.msg_data = b''
        self.prefix = b''
        self.msg_len = None
        self.msg_complete = False

    def _read(self, data, start):
        end = len(data)
        prefix_len = min(4 - len(self.prefix), end-start)
        self.prefix += data[:prefix_len]
        if prefix_len >= end - start:
            return end
        start += prefix_len
        if self.msg_len is None:
            self.msg_len = struct.unpack('!i', self.prefix)[0]
        data_len = self.msg_len - len(self.msg_data)
        data_len = min(data_len, end-start)
        self.msg_data += data[start:start+data_len]
        return start + data_len

    def _read_handshake(self, data, start):
        if start >= len(data):
            return start
        if self.handshake_len is None:
            self.handshake_data += data[start:start+1]  # pstrlen byte
            start += 1
            pstrlen = self.handshake_data[0]
            self.handshake_len = 49 + pstrlen
        toread = min(self.handshake_len-len(self.handshake_data), len(data))
        end = start + toread
        self.handshake_data += data[start:end]
        return end

    def read(self, data):
        i = 0
        while i < len(data):
            if not self.handshake_flag:
                i = self._read_handshake(data, i)
                if len(self.handshake_data) == self.handshake_len:
                    self.process_handshake()
            else:
                i = self._read(data, i)
                if len(self.msg_data) == self.msg_len:
                    self.process_data()
                    self.reset_msg()
        return

    def process_handshake(self):
        pstrlen = self.handshake_data[0]
        data_len = 49 + pstrlen
        if (len(self.handshake_data) == data_len):
            self.handshake_flag = True
        pstrlen = self.handshake_data[0]
        pstr = self.handshake_data[1:1+pstrlen]
        if pstr != b"BitTorrent protocol":
            self.on_badtype()
        offset = 1+pstrlen
        reserve_bit = self.handshake_data[offset:offset+8]
        if reserve_bit != b"\x00" * 8:
            #self.on_badtype()
            pass
        offset += 8
        info_hash = self.handshake_data[offset:offset+20]
        peerid = self.handshake_data[offset+20:offset+40]
        self.on_handshake(info_hash, peerid)
        return

    def process_data(self):
        if len(self.msg_data) == 0:
            self.on_keepalive()
            return
        msg_type = self.msg_data[0]
        if msg_type == CHOKE:
            self.on_choke()

        elif msg_type == UNCHOKE:
            self.on_unchoke()

        elif msg_type == INTERESTED:
            self.on_interested()

        elif msg_type == NOTINTERESTED:
            self.on_notinterested()

        elif msg_type == HAVE:
            index = struct.unpack('!i', self.msg_data[1:5])[0]
            self.on_have(index)

        elif msg_type == BITFIELD:
            raw_field = self.msg_data[1:]
            field = bytes_to_bool(raw_field)
            self.on_bitfield(field)

        elif msg_type == REQUEST:
            index = struct.unpack('!i', self.msg_data[1:5])[0]
            begin = struct.unpack('!i', self.msg_data[5:9])[0]
            length = struct.unpack('!i', self.msg_data[9:13])[0]
            self.on_request(index, begin, length)

        elif msg_type == PIECE:
            index = struct.unpack('!i', self.msg_data[1:5])[0]
            begin = struct.unpack('!i', self.msg_data[5:9])[0]
            block = self.msg_data[9:]
            self.on_piece(index, begin, block)

        elif msg_type == CANCEL:
            index = struct.unpack('!i', self.msg_data[1:5])[0]
            begin = struct.unpack('!i', self.msg_data[5:9])[0]
            length = struct.unpack('!i', self.msg_data[9:13])[0]
            self.on_cancel(index, begin, length)
        elif msg_type == PORT:
            listen_port = struct.unpack('!i', self.msg_data[1:5])[0]
            self.on_port(listen_port)
        else:
            self.on_badtype()
        return

    # following functions are to be overridden

    def on_handshake(self, info_hash, peerid):
        pass

    def on_keepalive(self):
        pass

    def on_choke(self):
        pass

    def on_unchoke(self):
        pass

    def on_interested(self):
        pass

    def on_notinterested(self):
        pass

    def on_have(self, index):
        pass

    def on_bitfield(self, field):
        pass

    def on_request(self, index, begin, length):
        pass

    def on_piece(self, index, begin, data):
        pass

    def on_cancel(self, index, begin, data):
        pass

    def on_port(self, listen_port):
        pass

    def on_badtype(self):
        '''Called when incoming data is not valid'''
        pass

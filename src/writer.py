import struct


def _sendint(x):
    '''returns four bytes from unsigned int, in network endianness'''
    return struct.pack('!i', x)


def _b01(b):
    if b:
        return '1'
    else:
        return '0'


def _bitbytes(arr):
    ar2 = [_b01(b) for b in arr]
    n = (8-len(ar2) % 8) % 8
    ar2.extend([_b01(False) for i in range(n)])
    s = ''.join(ar2)
    res = b''
    for i in range(len(s)//8):
        ss = s[i*8:i*8+8]
        res += int(ss, 2).to_bytes(1, byteorder='big')
    return res


class Writer(object):
    def handshake(self, info_hash, peerid):
        return b'\x13' + b"BitTorrent protocol" + b'\x00'*8 + info_hash + peerid

    def keep_alive(self):
        return _sendint(0)

    def choke(self):
        return _sendint(1) + b'\x00'

    def unchoke(self):
        return _sendint(1) + b'\x01'

    def interested(self):
        return _sendint(1) + b'\x02'

    def uninterested(self):
        return _sendint(1) + b'\x03'

    def have(self, piece_id):
        return _sendint(5) + b'\x04' + _sendint(piece_id)

    def bitfield(self, field):
        '''field: array of bool indicating available pieces'''
        payload = _bitbytes(field)
        return _sendint(1+len(payload)) + b'\x05' +payload

    def request(self, index, begin, length):
        return _sendint(13) + b'\x06' + _sendint(index)+ _sendint(begin)+ _sendint(length)

    def piece(self, index, begin, data):
        n = len(data)
        return _sendint(9 + n) + b'\x07' + _sendint(index)+ _sendint(begin)+ data

    def cancel(self, index, begin, length):
        return _sendint(13) + b'\x08' + _sendint(index)+ _sendint(begin)+ _sendint(length)

    def port(self, listen_port):
        return _sendint(3) + b'\x09' + _sendint(listen_port)


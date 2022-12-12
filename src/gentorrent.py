
import ben
import hashlib
import time
import os


def gen_pieces_one(src, piece_length):
    hash = b''
    f = open(src, 'rb')
    while True:
        sha1 = hashlib.sha1()
        s = f.read(piece_length)
        if s == b'':
            break
        sha1.update(s)
        hash += sha1.digest()
    f.close()
    return str(hash,'latin1')


def gen_info_single(src, piece_length):
    '''returns info section in torrent file
    single file mode'''
    if not os.path.exists(src):
        raise RuntimeError('src does not exist')
    d = {}
    d['piece length'] = piece_length
    d['pieces'] = gen_pieces_one(src, piece_length)
    d['name'] = os.path.basename(src)
    fsize = os.path.getsize(src)
    d['length'] = fsize
    return d


def gen_from_file(srcfp, dstfp, piece_length):
    '''Single file'''
    if not os.path.exists(srcfp):
        raise RuntimeError('src does not exist')

    d = {}
    d['announce'] = 'http://127.0.0.1:6969/announce' # must contain announce
    d['creation date'] = int(time.time())
    d['created by'] = 'gentorrent.py'
    d['info'] = gen_info_single(srcfp,piece_length)
    s = ben.encode(d)
    s = bytes(s,'latin1')
    g = open(dstfp,'wb')
    g.write(s)
    g.close()

if __name__ == '__main__':
    print(os.getcwd())
    gen_from_file('./resource/gatsby.txt','./resource/gatsby.torrent',256*1024)
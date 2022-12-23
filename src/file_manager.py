import os.path
import os
import hashlib

from chain_file import ChainFile


def resolve_path(folder, name, ls):
    return os.path.join(folder, name, *ls)


def create_file(fp, length):
    folder = os.path.dirname(fp)
    os.makedirs(folder, exist_ok=True)
    f = open(fp, 'wb')
    while length:
        n = min(length, 1024)
        s = b'\x00' * n
        f.write(s)
        length -= n
    f.close()
    return


def prepare_file(fp, length):
    if os.path.exists(fp):
        if os.path.getsize(fp) == length:
            return
    # elif os.path.exists(fp+'.part'):
    #     if os.path.getsize(fp+'.part') == length:
    #         return
    else:
        create_file(fp, length)


class FileManager(object):
    def read_info(self, torrent_info: dict, folder):
        fl = []
        nl = []
        name = torrent_info['name']
        if 'files' in torrent_info:
            # multi file mode
            for item in torrent_info['files']:
                nl.append(item['length'])
                fp = resolve_path(folder, name, item['path'])
                fl.append(fp)
        elif 'length' in torrent_info:
            # single file mode
            nl.append(torrent_info['length'])
            fp = os.path.join(folder, name)
            fl.append(fp)
        else:
            raise RuntimeError('Invalid torrent info')
        return (fl, nl)

    def __init__(self, torrent_info: dict, folder):
        # data
        self.piece_length = torrent_info['piece length']
        self.pieces_hash = [bytes(torrent_info['pieces'][i*20:i*20+20], 'latin1')
                            for i in range(len(torrent_info['pieces']) // 20)]
        self.complete_pieces: set[int] = set()
        self.buffer: list[dict[int, bytes]] = [{} for i in self.pieces_hash]
        # init
        fl, nl = self.read_info(torrent_info, folder)
        for i in range(len(fl)):
            prepare_file(fl[i], nl[i])
        # tool
        self.cf = ChainFile(fl)
        # init
        self.verify_hash()

    def verify_hash(self):
        '''verify hash of existing files'''
        offset = 0
        total_len = self.cf.length()
        i = 0
        while offset < total_len:
            s = self.cf.read(offset, self.piece_length)
            sha1 = hashlib.sha1()
            sha1.update(s)
            hash = sha1.digest()
            if hash == self.pieces_hash[i]:
                self.complete_pieces.add(i)
                pass
            # inc
            offset += self.piece_length
            i += 1
        return

    def is_complete(self):
        return len(self.pieces_hash) == len(self.complete_pieces)

    def close(self):
        self.cf.close()

    def has_piece(self, i):
        return i in self.complete_pieces

    def add_block(self, piece_index, begin, data):
        self.buffer[piece_index][begin] = data
        self.varify_piece(piece_index)

    def get_block(self, piece_index, begin, length):
        if piece_index in self.complete_pieces:
            return self.cf.read(piece_index*self.piece_length+begin, length)
        else:
            raise RuntimeError('requested block is unavailable')

    def get_partial(self):
        '''list of partial pieces'''
        return [i for i in range(len(self.buffer)) if self.buffer[i]]

    def cur_piece_length(self, piece_index):
        start = piece_index * self.piece_length
        end = min(self.cf.length(), start + self.piece_length)
        return end - start

    def varify_piece(self, piece_index):
        '''returns True if good, False if hash does not match, list if not enough data

        writes data to file if piece is complete'''
        d = self.buffer[piece_index]
        gap = []
        next_pos = 0
        s = b''
        key_list = list(d.keys())
        key_list.sort()
        for k in key_list:
            kk = k
            if k > next_pos:
                gap.append((next_pos, k-next_pos))
            elif k < next_pos:
                kk = next_pos
                s += d[k][kk-k:]
            else:  # equal
                s += d[k][kk-k:]
            next_pos = k + len(d[k])
        pos_end = self.cur_piece_length(piece_index)
        if gap == [] and next_pos == pos_end:
            sha1 = hashlib.sha1()
            sha1.update(s)
            hash = sha1.digest()
            self.buffer[piece_index] = {}
            if hash == self.pieces_hash[piece_index]:
                self.cf.write(piece_index*self.piece_length, s)
                self.complete_pieces.add(piece_index)
                return True
            else:
                return False
        else:
            return gap

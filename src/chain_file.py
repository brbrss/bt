import os.path


class ChainFile(object):
    def __init__(self, ls: list):
        mode = 'r+b'
        self.file_list: list = []
        self.n_list: list[int] = []
        for fp in ls:
            self.n_list.append(os.path.getsize(fp))
            f = open(fp, mode)
            self.file_list.append(f)

    def seek(self, offset):
        i = 0
        begin = offset
        while True:
            if i == len(self.n_list):
                raise RuntimeError('offset exceeds file length')
            x = self.n_list[i]
            if begin < x:
                break
            else:
                begin -= x
                i += 1
        return i, begin

    def read(self, offset, length):
        i, offset = self.seek(offset)
        self.file_list[i].seek(offset)
        res = self.file_list[i].read(length)
        while len(res) < length:
            i += 1
            if i == len(self.n_list):
                return res
            self.file_list[i].seek(0)
            res += self.file_list[i].read(length-len(res))
        return res

    def write(self, offset, data: bytes):
        i, offset = self.seek(offset)
        n = len(data)
        src_pos = 0
        self.file_list[i].seek(offset)
        length = min(n, self.n_list[i]-offset)
        self.file_list[i].write(data[src_pos:src_pos+length])
        src_pos += length
        n -= length
        while n > 0:
            i += 1
            if i == len(self.n_list):
                raise RuntimeError('writing exceeds file length')
            length = min(n, self.n_list[i])
            self.file_list[i].seek(0)
            self.file_list[i].write(data[src_pos:src_pos+length])
            src_pos += length
            n -= length

    def length(self):
        return sum(self.n_list)

    def close(self):
        for f in self.file_list:
            f.close()

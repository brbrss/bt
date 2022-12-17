import time


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


class Tracker(object):
    def __init__(self, d):
        '''d parsed dict from tracker response'''
        self.d = d
        self.last_time = time.time()
        self.interval = 0
        self.min_interval = 0
        self.complete = 0
        self.incomplete = 0
        self.downloaded = 0
        self.peers = []
        self.err = None
        try:
            self.set_data(d)
        except Exception as err:
            self.has_err(d, err)

    def set_data(self, d):
        self.interval = d['interval']
        self.min_interval = d['min interval']
        self.complete = d['complete']
        self.incomplete = d['incomplete']
        self.downloaded = d['downloaded']
        self.peers = parse_peer(d['peers'])

    def has_err(self, d, err:Exception):
        if 'err' in d:
            self.err = d['err']
        elif 'failure reason' in d:
            self.err = d['failure reason']
        else:
            self.err = err.__repr__()
        pass

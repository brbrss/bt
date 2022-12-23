import time


class RateCounter(object):
    '''calculate speed'''

    def __init__(self, interval_size):
        ''' interval_size in seconds'''
        self.interval_size = interval_size
        self.timestamp = time.time()
        self.total = 0
        self.rate = 0.0

    def add(self, x):
        self.total += x

    def check(self):
        newt = time.time()
        duration = newt - self.timestamp
        rate = 0
        if duration != 0:
            rate = self.total / duration
        if duration > self.interval_size:
            self.total = 0
            self.timestamp = newt
            self.rate = rate
        return self.rate

    def avg(self):
        self.check()
        return self.rate

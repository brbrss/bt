import socket
import time


class ConnOperator(object):
    '''Class for handling a single connection

    Decides when to recv/send and what to do with data.
    '''

    def __init__(self, conn: socket.socket):
        self.conn = conn
        # data for use in socket.send
        self.write_buf = b''
        # continue buffering from here
        self.write_pos = 0
        # check again in how many seconds
        self.timeout = 1
        # SelectorKey returned from selector
        self.key = None
        self.timestamp = 0  # force refresh check on first time
        self.count = 0
        self.last_send_time = 0
        # event mask for selector
        self.evmask = 0

    def parse(self, buf):
        '''Parses and process data received from connection, should also do any
        side effect(e.g. set write flag).

        Should handle incomplete data properly.'''
        return

    def write(self, conn):
        if not self.write_buf:
            return
        new_pos = conn.send(self.write_buf[self.write_pos:])
        self.last_send_time = time.time()
        self.write_buf = self.write_buf[new_pos:]
        self.write_pos = 0
        return

    def add_to_write(self):
        '''Automatically add things to write buffer.

        Should be called every a while. The exact wait time is set in timer'''
        return

    def check(self, newtime):
        '''Caller is responsible for providing timestamp from time.time()'''
        if newtime > self.timestamp+self.timeout:
            self.add_to_write()
            self.timestamp = newtime
        return

    def want_recv(self):
        '''returns whether should try to recv from connection at next nearest opportunity

        This function can be overridden.'''
        return True

    def want_send(self):
        '''returns whether should try to send from connection at next nearest opportunity

        This function can be overridden.'''

        return self.write_buf != b''

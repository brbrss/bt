
import selectors
import socket
import time
import queue


class ConnOperator(object):
    '''Class for handling a single connection

    Decides when to recv/send and what to do with data.
    '''

    def __init__(self):
        # data for use in socket.send
        self.write_buf = b''
        # continue buffering from here
        self.write_pos = 0
        # check again in how many seconds
        self.timeout = 0.1
        # SelectorKey returned from selector
        self.key = None
        self.timestamp = 0  # force refresh check on first time
        self.count = 0

    def parse(self, buf):
        '''Parses and process data received from connection, should also do any
        side effect(e.g. set write flag).

        Should handle incomplete data properly.'''
        return

    def write(self, conn):
        try:
            new_pos = conn.send(self.write_buf[self.write_pos:])
        except Exception:
            if self.key.fileobj.fileno() != -1:
                self.key.fileobj.shutdown(socket.SHUT_RDWR)
                self.key.fileobj.close()
            return
        if new_pos == len(self.write_buf):
            self.write_buf = b''
            self.write_pos = 0
        else:
            self.write_pos = new_pos
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


def mask(user):
    '''Generates event mask for selector'''
    flag = 0
    if user.want_recv():
        flag |= selectors.EVENT_READ
    if user.want_send():
        flag |= selectors.EVENT_WRITE
    return flag


class ConnPool(object):
    '''Class for working with multiple socket connections.
    Takes in sockets and handles using/closing sockets. 
    Outside code should not touch these sockets after registering.'''

    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.conn_list = {}
        self.timeout = 1
        self.queue = queue.Queue()
        self.flag_run = True
        #self.handlerClass = handlerClass

    def _register(self, connOperator):
        ''' 
        Add socket to selector list

        Will set socket to non-blocking
        '''
        connOperator.conn.setblocking(False)
        name = connOperator.conn.fileno()
        #user = self.handlerClass()
        evmask = mask(connOperator)
        soc_key = self.sel.register(connOperator.conn, evmask)
        connOperator.key = soc_key
        self.conn_list[name] = connOperator

    def register(self, connOperator):
        '''Takes in a ConnOperator, which should contain a connection.

        Pool may wait for current select to finish before handling 
        the new connection.'''
        self.queue.put(connOperator)
        return

    def refresh_status(self):
        '''Refreshes read/write event mask for selector'''
        for k in self.conn_list:
            conn = self.conn_list[k].key.fileobj
            if conn.fileno() == -1:
                self.sel.unregister(conn)
        self.conn_list = {
            k: self.conn_list[k] for k in self.conn_list if self.conn_list[k].key.fileobj.fileno() != -1}

        for k in self.conn_list:
            user = self.conn_list[k]
            newmask = mask(user)
            if newmask != user.key.events:
                newkey = self.sel.modify(
                    user.key.fileobj, newmask, user.key.data)
                user.key = newkey
        return

    def refresh_timeout(self):
        if len(self.conn_list) == 0:
            self.timeout = 10
            return
        self.timeout = min(
            [self.conn_list[key].timeout for key in self.conn_list])
        self.timeout = min(10, self.timeout)

    def push_pending(self):
        while not self.queue.empty():
            conn = self.queue.get()
            self._register(conn)
        return

    def onestep(self):
        '''blocking'''

        res_list = self.sel.select(self.timeout)
        for key, ev in res_list:
            conn = key.fileobj
            if ev & selectors.EVENT_READ:
                data = conn.recv(1024)
                self.conn_list[key.fd].parse(data)
            if ev & selectors.EVENT_WRITE:
                self.conn_list[key.fd].write(conn)
        self.refresh_status()
        newtime = time.time()
        for key in self.conn_list:
            user = self.conn_list[key]
            user.check(newtime)
        self.refresh_timeout()

    def run(self):
        '''Call this method to start processing sockets'''
        try:
            while self.flag_run:
                self.push_pending()
                if len(self.conn_list) == 0:
                    time.sleep(1)
                else:
                    self.onestep()
        except Exception as err:
            print('pool error ', err)

    def close(self):
        self.flag_run = False
        for k in self.conn_list:
            conn = self.conn_list[k].key.fileobj
            fileno = conn.fileno()
            print('stop ', fileno)
            if fileno != -1:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
        self.sel.close()

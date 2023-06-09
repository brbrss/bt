import traceback
import selectors
import socket
import time
import queue
from conn_operator import ConnOperator


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

    def __init__(self, refresh_cb):
        self.sel = selectors.DefaultSelector()
        self.conn_list: dict[int, ConnOperator] = {}
        self.timeout = 1
        self.queue = queue.Queue()
        self.flag_run = True
        #self.handlerClass = handlerClass
        self.refresh_cb = refresh_cb

    def _register(self, connOperator: ConnOperator):
        ''' 
        Add socket to selector list

        Will set socket to non-blocking
        '''
        connOperator.conn.setblocking(False)
        name = connOperator.conn.fileno()
        #user = self.handlerClass()
        evmask = mask(connOperator)
        self.conn_list[name] = connOperator
        if evmask:
            soc_key = self.sel.register(connOperator.conn, evmask)

    def register(self, connOperator):
        '''Takes in a ConnOperator, which should contain a connection.

        Pool may wait for current select to finish before handling 
        the new connection.'''
        self.queue.put(connOperator)
        return

    def purge_socket(self):
        '''Remove closed sockets'''
        for k in self.conn_list:
            conn = self.conn_list[k].conn
            if conn.fileno() == -1:  # only if socket is closed
                self.sel.unregister(conn)
        self.conn_list = {
            k: self.conn_list[k] for k in self.conn_list if self.conn_list[k].conn.fileno() != -1}

    def refresh_status(self):
        '''Refreshes read/write event mask for selector'''
        for k in self.conn_list:
            user = self.conn_list[k]
            newmask = mask(user)
            if newmask != user.evmask:
                if user.conn.fileno() in self.sel.get_map():
                    self.sel.unregister(user.conn)
                if newmask != 0:
                    newkey = self.sel.register(user.conn, newmask, None)
                    user.evmask = newkey.events
        return

    def refresh_timeout(self):
        if len(self.conn_list) == 0:
            self.timeout = 1
            return
        self.timeout = min(
            [self.conn_list[key].timeout for key in self.conn_list])
        self.timeout = min(1, self.timeout)

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
                try:
                    data = conn.recv(32*1024)
                    if data == b'':
                        print('socket', conn.fileno(),
                              'is closing because recv returns empty')
                        conn.close()
                    self.conn_list[key.fd].parse(data)
                except Exception as err:
                    print('err on reading', err)
                    print(traceback.format_exc())
                    print('socket closed')
                    conn.close()
            if ev & selectors.EVENT_WRITE:
                try:
                    self.conn_list[key.fd].write(conn)
                except Exception as err:
                    print('err on writing', err)
                    print(traceback.format_exc())
                    print('socket closed')
                    conn.close()

    def check(self):
        self.purge_socket()
        newtime = time.time()
        for key in self.conn_list:
            user = self.conn_list[key]
            user.check(newtime)
        self.refresh_status()
        self.refresh_timeout()
        self.refresh_cb()

    def run(self):
        '''Call this method to start processing sockets'''
        try:
            while self.flag_run:
                self.push_pending()
                m = self.sel.get_map()
                if len(m) == 0:
                    time.sleep(1)
                else:
                    self.onestep()
                self.check()
        except Exception as err:
            #print('pool error ', err)
            #print(traceback.format_exc())
            pass
        print('pool closed')

    def close(self):
        '''Closes any registered socket and end loop in self.run()'''
        self.flag_run = False
        for k in self.conn_list:
            conn = self.conn_list[k].conn
            fileno = conn.fileno()
            print('stop ', fileno)
            self.sel.unregister(conn)
            if fileno != -1:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
        self.sel.close()


import selectors
import socket
import time
import queue


class ConnOperator(object):
    '''Handles a single connection
    '''

    def __init__(self):
        #data for use in socket.send 
        self.write_buf = b'' 
        #continue buffering from here
        self.write_pos = 0
        #check again in how many seconds
        self.timeout = 100
        #SelectorKey returned from selector
        self.key = None
        self.timestamp = 0 # force refresh check on first time
    
    def parse(self,buf):
        '''Parses and process data received from connection, should also do any
        side effect(e.g. set write flag).
        
        Should handle incomplete data properly.'''

        pass

    def write(self,conn):
        new_pos = conn.send(self.write_buf[self.write_pos:])
        if new_pos == len(self.write_buf):
            self.write_buf = b''
            self.write_pos = 0
        else:
            self.write_pos = new_pos
        return

    def check_add_to_write(self):
        '''Automatically add things to write buffer.
        
        Should be called every a while. The exact wait time is set in timer'''
        pass
    
    def check(self,newtime):
        '''Caller is responsible for providing timestamp from time.time()'''
        if newtime>self.timestamp+self.timeout:
            self.check_add_to_write()
            self.timestamp = newtime
        return

    def want_recv(self):
        '''Should try to recv from connection at next nearest opportunity?
        
        This function can be overridden.'''
        return True
    
    def want_send(self):
        '''Should try to recv from connection at next nearest opportunity?
        
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

    def _register(self,conn):
        ''' 
        Will set socket to non-blocking
        '''
        conn.setblocking(False)
        name = conn.fileno()
        user = ConnOperator()
        evmask = mask(user)
        soc_key = self.sel.register(conn, evmask)
        user.key = soc_key
        self.conn_list[name] = user
    
    def register(self,conn):
        '''Takes in a connection.
        
        Pool may wait for current select to finish before handling 
        the new connection.'''
        self.queue.put(conn)
        return

    def refresh_status(self):
        '''Refreshes read/write event mask for selector'''
        self.conn_list = {k:self.conn_list[k] for k in self.conn_list if self.conn_list[k].key.fileobj.fileno()!=-1}
        for key in self.conn_list:
            user = self.conn_list[key]
            newmask = mask(user)
            if newmask != user.key.events:
                newkey = self.sel.modify(key.fileobj,newmask,key.data)
                user.key = newkey
        return
    
    def refresh_timeout(self):
        self.timeout = min([self.conn_list[key].timeout for key in self.conn_list])
        self.timeout = min(10,self.timeout)

    def push_pending(self):
        while not self.queue.empty():
            conn = self.queue.get()
            self._register(conn)
        return

    def onestep(self):
        '''blocking'''
        
        res_list = self.sel.select(self.timeout)
        for key,ev in res_list:
            conn = key.fileobj
            if ev& selectors.EVENT_READ:
                data = conn.recv(1024)
                self.conn_list[key.fd].parse(data)
            if ev& selectors.EVENT_WRITE:
                self.conn_list[key].write(conn)
        self.refresh_status()
        newtime = time.time()
        for key in self.conn_list:
            user = self.conn_list[key]
            user.check(newtime)
        self.refresh_timeout()
        

    def run(self):
        try:
            while self.flag_run:
                self.push_pending()
                if len(self.conn_list)==0:
                    time.sleep(1)
                else:
                    self.onestep()
        except Exception as err:
            print('pool error ',err)

    def close(self):
        self.flag_run = False
        for k in self.conn_list:
            conn = self.conn_list[k].key.fileobj
            fileno = conn.fileno()
            print('stop ',fileno)
            if fileno != -1:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
        self.sel.close()
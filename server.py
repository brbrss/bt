import socket
import time
import concurrent.futures
import threading


def exec_conn(conn):
    try:
        print('connect at ',conn.getpeername())
        print('from',conn.getsockname())
        print('fileno: ', conn.fileno())
        conn.settimeout(3)
        while True:
            data = None
            data = conn.recv(1024)
            print('received ',data)
            if data == b'':
                print('socket closing: ',conn.getpeername())
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                return
    except Exception as err:
        print("error: ", err)
        return

class Server(object):
    '''
        Multithreaded socket server

        How to use:
        create server in main thread,
        call start in new thread,
        call stop in main thread
        '''

    def __init__(self, port):
        self.soc = socket.socket()
        #address = (socket.gethostname(), port)
        address = ("127.0.0.1", port)
        
        self.soc.bind(address)
        self.soc.listen(5)

        self.port = self.soc.getsockname()[1]
        
        self.flag_run = True
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.conn_list = []
        self.lock = threading.Lock()
    
    def start(self):
        '''start server

            this function is blocking, should start in a separate thread'''
        #print("server starting at: ", self.soc.getsockname())
        while self.flag_run:
            conn,addr = self.soc.accept()
            self.lock.acquire()
            self.conn_list = [c for c in self.conn_list if c.fileno()!=-1]
            self.conn_list.append(conn)
            self.executor.submit(exec_conn,conn)
            self.lock.release()
        pass

    def stop(self):
        self.lock.acquire()
        self.flag_run = False
        for conn in self.conn_list:
            fileno = conn.fileno()
            print('stop ',fileno)
            if fileno != -1:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
        print('stopped connections: ',len(self.conn_list))
        self.executor.shutdown()
        self.soc.close()

def t():
    time.sleep(9999)

if __name__ == '__main__':
    server = Server(9999)
    f = lambda : server.start()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    executor.submit(f)
    input('')
    server.stop()
    #executor.shutdown()
    
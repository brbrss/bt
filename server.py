import socket
import time
import concurrent.futures
import threading
import conn_pool

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
        self.conn_list = []
        self.lock = threading.Lock()
    
    def start(self, pool):
        '''start server

            this function is blocking, should start in a separate thread'''
        #print("server starting at: ", self.soc.getsockname())
        try:
            while self.flag_run:
                conn,addr = self.soc.accept()
                print('received conn: ',addr)
                self.lock.acquire()
                pool.register(conn)

                self.lock.release()
        except Exception as err:
            #print(err)
            pass
        print('server stopped')
        pass

    def stop(self):
        self.lock.acquire()
        self.flag_run = False
        self.soc.close()

def t():
    time.sleep(9999)

if __name__ == '__main__':
    server = Server(9999)
    pool = conn_pool.ConnPool()
    g = lambda: pool.run()
    f = lambda : server.start(pool)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    executor.submit(f)
    executor.submit(g)
    input('')
    pool.close()
    server.stop()
    #executor.shutdown()
    
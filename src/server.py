import socket
import time
import concurrent.futures
import threading
import conn_pool


class Server(object):
    '''
        Socket for listening

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
    
    def start(self, conn_cb):
        '''start server

            this function is blocking, should start in a separate thread'''
        try:
            while self.flag_run:
                conn,addr = self.soc.accept()
                print('received conn: ',addr)
                self.lock.acquire()
                conn_cb(conn)

                self.lock.release()
        except Exception as err:
            #print(err)
            pass
        print('server stopped')

    def stop(self):
        self.lock.acquire()
        self.flag_run = False
        self.soc.close()



if __name__ == '__main__':
    server = Server(9999)
    pool = conn_pool.ConnPool(conn_pool.ConnOperator)
    g = lambda: pool.run()
    f = lambda : server.start(pool)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    executor.submit(f)
    executor.submit(g)
    input('')
    pool.close()
    server.stop()
    executor.shutdown()
    
# import unittest
# import conn_pool
# import socket
# import concurrent.futures
# import time


# NCON = 4


# def fixbytes(n):
#     L = [i % 256 for i in range(n)]
#     return bytes(L)


# def exec_conn(server, cb):
#     server.listen(1)
#     conn, addr = server.accept()

#     while True:
#         data = None
#         try:
#             data = conn.recv(1024)
#             cb(data)
#             conn.send(b'ahawowo')
#         except Exception as err:
#             return
#         if data == b'':
#             print('socket closing: ', conn.getpeername())
#             conn.shutdown(socket.SHUT_RDWR)
#             conn.close()
#             return


# class MockServer(object):
#     def __init__(self):
#         self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=NCON)
#         port_list = []
#         self.data = [b'' for i in range(NCON)]
#         for i in range(NCON):
#             soc = socket.socket()
#             soc.bind(("127.0.0.1", 0))
#             myport = soc.getsockname()[1]
#             port_list.append(myport)
#             ii = i
#             def cb(x):
#                 self.data[ii] += x
#             self.executor.submit(exec_conn, soc, cb)
#             self.port_list = port_list

#     def stop(self):
#         self.executor.shutdown()


# class MockHandler(conn_pool.ConnOperator):
#     def __init__(self):
#         super().__init__()
#         self.write_buf = b'abcde'
#         self.readnum = 0

#     def parse(self, data):
#         self.onread(data)
#         self.readnum += len(data)
#         if (self.readnum > 20):
#             self.key.fileobj.close()



# @unittest.skip
# class ConnPoolTest(unittest.TestCase):

#     def test_init(self):
#         server = MockServer()
#         pool = conn_pool.ConnPool(conn_pool.ConnOperator)
#         for port in server.port_list:
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 s.connect(('127.0.0.1', port))
#                 s.settimeout(1)
#                 pool.register(s)

#         def g(): return pool.run()
#         exe = concurrent.futures.ThreadPoolExecutor(max_workers=1)
#         exe.submit(g)
#         time.sleep(2)
#         pool.close()
#         exe.shutdown()

#     @unittest.skip("bug")
#     def test_mock(self):
#         server = MockServer()
#         pool = conn_pool.ConnPool(MockHandler)
#         for port in server.port_list:
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             s.connect(('127.0.0.1', port))
#             s.settimeout(50)
#             pool.register(s)

#         def g(): return pool.run()
#         exe = concurrent.futures.ThreadPoolExecutor(max_workers=1)
#         exe.submit(g)
#         time.sleep(2)
#         pool.close()
#         exe.shutdown()
#         self.assertEqual(server.data[2], b'abcde')


import socket

import time


import urllib.request


def fixbytes(n):
    L = [i % 256 for i in range(n)]
    return bytes(L)

def foo(data):
    for b in data:
        if b==13:
            return True
    return False

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 9999  # The port used by the server

# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     s.sendall(b"")
#     s.sendall(b"Hello, world")
#     for i in range(100):
#         data = s.recv(1024)
#         print('received: ',data)
#         if data == b'':
#             print('socked closed by server')
#             break
#         if foo(data):
#             break    
#     s.sendall(b"chocolate")

#     #data = s.recv(1024)



req = urllib.request.Request('http://localhost:6969/test', method='GET')
res = None

res = urllib.request.urlopen(req)
s = res.read()
s = str(s, 'latin1')
print(s)
print([ord(c) for c in s])
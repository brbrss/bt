
import socket

import time


HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 9999  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"")
    s.sendall(b"Hello, world")
    for i in range(2):
        time.sleep(0.1)
        s.sendall(b'')
    s.sendall(b"chocolate")

    #data = s.recv(1024)

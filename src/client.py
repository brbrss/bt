'''This is a throw-away script. 
Not used in production.'''

import socket

import time
from writer import Writer

import urllib.request




HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 6881  # The port used by the server



info_hash = b'\x94Q\xe0\xaf\xfc\xc8cx\xcb\x88\xe1/]\xe7y\xa8^\n\xd9\xf4'
peer_id = b'01234567890123456789'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.setblocking(False)

writer = Writer()
s.sendall(writer.handshake(info_hash,peer_id))

time.sleep(1)
data = s.recv(1024)




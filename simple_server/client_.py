from socket import *
from random import randint
import time
from errno import *
from util import log


class Client:
    def __init__(self, server_addr):
        self.sock = self.init_connect(server_addr)
        self.is_connected = True
        self.recv_bufsize = 65535
        # self.sock.sendall('aaaa'.encode())


    def init_connect(self, server_addr):
        addr = server_addr
        sock = create_connection(addr)
        # sock.setblocking(True)
        return sock

    def run(self):
        for i in range(2):
            self.sock.sendall('aaaa'.encode())
            print('sleep', flush=True)
            time.sleep(1)
        self.sock.shutdown(1)

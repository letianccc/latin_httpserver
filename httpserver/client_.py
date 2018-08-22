from socket import *
from random import randint
from time import sleep
from errno import *
from util import log


class Client:
    def __init__(self, server_addr):
        self.sock = self.init_connect(server_addr)
        self.is_connected = True
        self.recv_bufsize = 65535

    def init_connect(self, server_addr):
        addr = server_addr
        sock = create_connection(addr)
        # sock.setblocking(True)
        return sock

    def send_message(self, message):
        data = message.encode()
        self.sock.sendall(data)

    def recv_message(self):
        data = b''
        try:
            while True:
                buf = self.sock.recv(self.recv_bufsize)
                if self.is_EOF(buf):
                    self.is_connected = False
                    break
                data += buf
        except BlockingIOError:
            pass
        message = data.decode()
        return message

    def get_response(self, request):
        self.send_message(request)
        response = self.recv_message()
        self.disconnect()
        return response

    def is_EOF(self, data_byte):
        return data_byte == b''

    def disconnect(self):
        self.sock.close()

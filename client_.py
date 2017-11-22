from socket import *
from random import randint
from time import sleep
from errno import *

class Client:
    def __init__(self):
        self.sock = self.init_connect()
        self.is_connected = True
        self.recv_bufsize = 65535

    def init_connect(self):
        addr = ('127.0.0.1', 8888)
        sock = create_connection(addr)
        sock.setblocking(0)
        return sock

    def send_message(self, message):
        data = message.encode()
        length = len(data)
        size = 0
        try:
            while size < length:
                size += self.sock.send(data)
        except ConnectionError:
            print('ConnectionError')
            self.is_connected = False
        print("success send: ")

    def recv_message(self):
        data = b''
        try:
            while True:
                buf = self.sock.recv(self.recv_bufsize)
                if buf == b'':
                    self.is_connected = False
                    break
                data += buf
        except BlockingIOError:
            pass
        except ConnectionError:
            print("ConnectionError")
            self.is_connected = False
        message = data.decode()
        return message

    def handle_response(self, response):
        self.is_connected = False
        # self.send_message(response)

    def run(self):
        message = "GET code/python/latin_httpserver/index.html\r\n"
        # message = "ss"
        self.send_message(message)

        while True:
            response = self.recv_message()
            if response:
                self.count += 1
                print('recv: ', self.count)
                print("recv from serv: ", response)
                self.handle_response(response)
            if not self.is_connected:
                self.disconnect()
                return

    def disconnect(self):
        print("disconnect...")
        self.sock.close()



client = Client()
client.run()

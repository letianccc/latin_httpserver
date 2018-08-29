from socket import *
from random import randint
from time import sleep
from errno import *
from util import log
from select import epoll, EPOLLIN

class Client:
    def __init__(self, server_addr):
        self.is_connected = True
        self.recv_bufsize = 65535
        self.listen_sock = None
        self.data_sock = None
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.ctrl_sock = self.init_connect(server_addr)

    def init_connect(self, server_addr):
        addr = server_addr
        sock = create_connection(addr)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.setblocking(False)
        fd = sock.fileno()
        self.register(sock)
        return sock

    def send_request(self, message):
        data = message.encode()
        self.ctrl_sock.sendall(data)

    def store(self, message):
        data = message.encode()
        self.data_sock.sendall(data)
        self.data_sock.close()

    def recv_data(self):
        data = b''
        while True:
            buf = self.data_sock.recv(self.recv_bufsize)
            if buf == b'':
                return data.decode()
            data += buf



    def register(self, socket):
        fd = socket.fileno()
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)

    def unregister(self, fd):
        self.epoll_fd.unregister(fd)
        sock = self.sock_list.pop(fd)
        return sock

    def recv_response(self):
        data = b''
        while True:
            buf = b''
            try:
                buf = self.ctrl_sock.recv(self.recv_bufsize)
                data += buf
            except BlockingIOError:
                if self.recv_all(data, buf):
                    break
        message = data.decode()
        return message

    def recv_all(self, data, buf):
        return data != b'' and buf == b''

    def get_free_port(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.bind(('', 0))
        addr = sock.getsockname()[0]
        port = sock.getsockname()[1]
        sock.close()
        return addr, port

    def make_data_connect(self, address):
        sock = socket(AF_INET, SOCK_STREAM)
        self.listen_sock = sock
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.setblocking(True)
        sock.bind(address)
        sock.listen()
        self.register(sock)

    def get_response(self, request=None):
        if request:
            # self.before_request(request)
            self.send_request(request)
            while True:
                epoll_list = self.epoll_fd.poll()
                if self.is_listen_event(epoll_list):
                    self.data_sock, fd = self.listen_sock.accept()
                else:
                    response = self.recv_response()
                    return response
        else:
            epoll_list = self.epoll_fd.poll()
            response = self.recv_response()
            return response



    def is_listen_event(self, epoll_list):
        if self.listen_sock:
            fds = [fd for fd, event in epoll_list]
            fd = self.listen_sock.fileno()
            if fd in fds:
                return True
        return False



            # for fd, event in epoll_list:
            #     if self.listen_sock and fd == self.listen_sock.fileno():
            #         self.data_sock, data_fd = self.listen_sock.accept()
            #         print('data_sock', self.data_sock)
            #     else:
            #         response = self.recv_response()
            #         return response

    def before_request(self, request):
        pass

    def after_request(self, request):
        if 'PORT' in request or 'STOR' in request:
            if self.listen_sock:
                try:
                    self.data_sock, db = self.listen_sock.accept()
                except BlockingIOError:
                    pass

    def is_EOF(self, data_byte):
        return data_byte == b''

    def clear(self):
        self.ctrl_sock.close()
        if self.listen_sock:
            self.listen_sock.close()
        if self.data_sock:
            self.data_sock.close()
        # self.epoll_fd.close()


from select import *
from socket import *
from util import log
import re
from .entity.exception import CommandError
from .handler import ControlHandler

bufsize = 65536

class FTPServer:
    def __init__(self, server_addr):
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.ctrl_handler = ControlHandler(self)
        self.listen_sock, self.listen_fd = self.init_server(server_addr)
        self.is_runing = False


    def init_server(self, server_addr):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.bind(server_addr)
        sock.listen()
        fd = sock.fileno()
        self.register(sock)
        return sock, fd

    def create_data_sock(self, client_addr):
        sock = create_connection(client_addr)
        sock.setblocking(False)
        fd = sock.fileno()
        self.register(sock)
        return sock, fd


    def register(self, socket):
        fd = socket.fileno()
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)
        print(fd)

    def unregister(self, fd):
        self.epoll_fd.unregister(fd)
        sock = self.sock_list.pop(fd)
        return sock

    def run(self):
        self.is_runing = True
        while self.is_run():
            epoll_list = self.epoll_fd.poll()
            for fd, event in epoll_list:
                if fd == self.listen_fd:
                    self.handle_connection()
                else:
                    self.handle_control(fd)

    def handle_connection(self):
        ctrl_sock, addr = self.listen_sock.accept()
        ctrl_sock.setblocking(False)
        self.register(ctrl_sock)

    def handle_control(self, fd):
        self.init_handler(fd)
        self.ctrl_handler.handle()

    def init_handler(self, fd):
        sock = self.sock_list[fd]
        self.ctrl_handler.set_socket(sock, fd)

    def validate(self, path):
        # for test
        if path == '/500':
            raise ServerError
        if path == '/404':
            raise NotFound
        if path == '/403':
            raise Forbidden
        if path == '/400':
            raise BadRequest

        if not self.exist_file(path):
            raise NotFound
        if not self.have_read_permission(path):
            raise Forbidden

    def can_disconnect(self):
        return self.ctrl_handler.is_connected()

    def have_read_permission(self, path):
        if path == 'index.html':
            return True
        mode = stat(path).st_mode
        return mode & S_IRUSR or mode & S_IRGRP or mode & S_IROTH

    def exist_file(self, path):
        # if path == None or not isfile(path):
        #     return False
        # return True
        if path is not None:
            if path == 'index.html':
                return True
        return False

    def disconnect(self):
        fd = self.ctrl_handler.fd
        sock = self.unregister(fd)
        sock.close()

    def clear(self):
        self.listen_sock.close()

    def is_run(self):
        return self.is_runing

    def stop(self):
        self.clear()
        self.is_runing = False


from select import *
from socket import *
from util import log
import re
from time import sleep
bufsize = 65536

class Server:
    def __init__(self, server_addr):
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.listen_sock, self.listen_fd = self.init_server(server_addr)
        self.is_runing = False


    def init_server(self, server_addr):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.bind(server_addr)
        sock.listen()
        fd = sock.fileno()
        self.register(sock, fd)
        return sock, fd

    def register(self, socket, fd):
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)

    def unregister(self, fd):
        self.epoll_fd.unregister(fd)
        sock = self.sock_list.pop(fd)
        sock.close()

    def run(self):
        while True:
            epoll_list = self.epoll_fd.poll()
            for fd, event in epoll_list:
                if fd == self.listen_fd:
                    self.handle_connection()
                else:
                    self.handle_control(fd)
            sleep(1)

    def handle_connection(self):
        ctrl_sock, addr = self.listen_sock.accept()
        ctrl_sock.setblocking(False)
        fd = ctrl_sock.fileno()
        self.register(ctrl_sock, fd)

    def handle_control(self, fd):
        sock = self.sock_list[fd]
        bytes = sock.recv(4096)
        print(bytes, flush=True)

from socket import *
from random import randint
from time import sleep
from errno import *
from .util import log
from select import epoll, EPOLLIN
import re
from .config import BLOCK_PAYLOAD_CAPACITY

class Client:
    def __init__(self, server_addr):
        self.is_connected = True
        self.recv_bufsize = 65535
        self.listen_sock = None
        self.data_sock = None
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.ctrl_sock = self.init_connect(server_addr)
        self.mode = 'S'

    def init_connect(self, server_addr):
        addr = server_addr
        sock = create_connection(addr)
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.setblocking(False)
        fd = sock.fileno()
        self.register(sock)
        return sock

    def send_message(self, message):
        data = message.encode()
        self.ctrl_sock.sendall(data)

    def send_data(self, data):
        if self.mode == 'S':
            self.data_sock.sendall(data)
            self.disconnect_data()
        elif self.mode == 'B':
            self.store_in_block(data)

    def store_in_block(self, data):
        size = BLOCK_PAYLOAD_CAPACITY
        rest = data
        tell = 0
        while rest:
            for i in range(5):
                if rest:
                    data = rest[:size]
                    rest = rest[size:]
                    block = self.format_block(data)
                    # log(self.data_sock.fileno())
                    self.data_sock.sendall(block)
                    tell += len(data)
            block = self.restart_mark_block(tell, rest)
            self.data_sock.sendall(block)


    def format_block(self, payload, is_eof=False):
        eof_code = 64
        normal_code = 0
        eof_byte = (eof_code).to_bytes(1, 'big')
        normal_byte = (normal_code).to_bytes(1, 'big')
        size = len(payload)
        count_field = (size).to_bytes(2, 'big')
        if is_eof:
            desc_field = eof_byte
        else:
            desc_field = normal_byte
        block = desc_field + count_field + payload
        return block

    def restart_mark_block(self, position, rest):
        eof_code = 64
        restart_mark = 16
        # eof_byte = (eof_code).to_bytes(1, 'big')
        eof_mark = eof_code | restart_mark
        eof_mark_byte = (eof_mark).to_bytes(1, 'big')
        restart_mark_byte = (restart_mark).to_bytes(1, 'big')
        is_eof = rest == b''
        if position < 256:
            size = 1
        elif position < 65536:
            size = 2
        elif position < 16777216:
            size = 3
        elif position < 4294967296:
            size = 4
        payload = (position).to_bytes(size, 'big')
        count_field = (size).to_bytes(2, 'big')
        if is_eof:
            desc_field = eof_mark_byte
        else:
            desc_field = restart_mark_byte
        block = desc_field + count_field + payload
        return block


    def format_blocks(self, bytestream):
        blocks = b''
        block_capacity = 65536
        eof_code = 64
        eof_byte = (eof_code).to_bytes(1, 'big')
        normal_byte = (0).to_bytes(1, 'big')
        is_eof = False
        while not is_eof:
            payload = bytestream[:65536]
            bytestream = bytestream[65536:]
            size = len(payload)
            count_field = (size).to_bytes(2, 'big')
            if size < block_capacity or bytestream == '':
                is_eof = True
                desc_field = eof_byte
            else:
                desc_field = normal_byte
            block = desc_field + count_field + payload
            blocks += block
        return blocks

    def reinit(self):
        if self.data_sock:
            self.disconnect_data()
        if self.listen_sock:
            self.unregister(self.listen_sock.fileno())
            self.listen_sock.close()
            self.listen_sock = None
        self.mode = 'S'


    def recv_data(self):
        data = b''
        while True:
            buf = self.data_sock.recv(self.recv_bufsize)
            if self.is_EOF(buf):
                self.disconnect_data()
                return data
            data += buf

    def recv_block(self):
        sock = self.data_sock
        data = b''
        while True:
            header = sock.recv(3)
            desc = int.from_bytes(header[0:1], byteorder='big')
            count = int.from_bytes(header[1:3], byteorder='big')
            payload = sock.recv(count)
            data += payload
            if self.is_block_eof(desc):
                if len(payload) == count:
                    return data
                else:
                    return ''

    def is_block_eof(self, desc):
        return desc & 64 > 0

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
        if self.listen_sock:
            self.stop_listen()
        sock = socket(AF_INET, SOCK_STREAM)
        self.listen_sock = sock
        sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        sock.setblocking(True)
        sock.bind(address)
        sock.listen()
        self.register(sock)

    def stop_listen(self):
        self.unregister(self.listen_sock.fileno())
        self.listen_sock.close()
        self.listen_sock = None

    # def send_request(self, request):
    #     self.send_message(request)
    #     resp = self.get_response(request)
    #     return resp

    def send_request(self, request):
        self.send_message(request)

    def get_response(self, request):
        response = None
        while True:
            epoll_list = self.epoll_fd.poll()
            for fd, event in epoll_list:
                if self.listen_sock and fd == self.listen_sock.fileno():
                    if self.data_sock:
                        self.disconnect_data()
                    self.data_sock, addr = self.listen_sock.accept()
                else:
                    response = self.recv_response()
            if response:
                response = self.handle_response(request, response)
                if response:
                    return response


    def handle_response(self, request, response):
        if 'MODE' in request:
            if response == '200 Command okay':
                pattern = 'MODE (?P<mode>\S+)\r\n'
                rs = re.match(pattern, request)
                self.mode = rs.group('mode')[0]
        elif 'REIN' in request:
            if response == '220 Service ready for new user':
                self.reinit()
        elif 'STOR' in request or 'STOU' in request or \
                'APPE' in request or 'RETR' in request:
            resps = response.split('\r\n')
            pattern = '110 Restart marker reply MARK \w+ = (?P<server_marker>\w+)'
            for resp in resps:
                rs = re.match(pattern, resp)
                if rs is not None:
                    self.marker = rs.group('server_marker')
                else:
                    return resp
        return response

    def reinit(self):
        if self.data_sock:
            self.disconnect_data()
        if self.listen_sock:
            self.unregister(self.listen_sock.fileno())
            self.listen_sock.close()
            self.listen_sock = None
        self.mode = 'S'



    def before_request(self, request):
        pass

    # def after_request(self, request):
    #     if 'PORT' in request or 'STOR' in request:
    #         if self.listen_sock:
    #             try:
    #                 self.data_sock, addr = self.listen_sock.accept()
    #             except BlockingIOError:
    #                 pass
    #

    def disconnect_data(self):
        self.data_sock.close()
        self.data_sock = None

    def is_EOF(self, data_byte):
        return data_byte == b''

    def clear(self):
        self.ctrl_sock.close()
        if self.listen_sock:
            self.listen_sock.close()
        if self.data_sock:
            self.disconnect_data()
        # self.epoll_fd.close()

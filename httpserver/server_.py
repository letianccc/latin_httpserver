from os import stat
from os.path import isdir, isfile
from select import *
from socket import *
from stat import *
from time import sleep
import os
from util import log
from httpserver.entity.exception import Forbidden, NotFound, BadRequest, ServerError
bufsize = 65536

class HttpServer:
    def __init__(self, server_addr):
        self.epoll_fd = epoll()
        self.sock_list = {}
        # self.recv_bufsize = 65535
        self.client = Client()
        self.serv_sock, self.serv_fd = self.init_server(server_addr)
        self.register(self.serv_sock)

    def init_server(self, server_addr):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        fd = sock.fileno()
        sock.bind(server_addr)
        sock.listen()
        return sock, fd

    def register(self, socket):
        fd = socket.fileno()
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)

    def run(self):
        while True:
            epoll_list = self.epoll_fd.poll()
            for fd, event in epoll_list:
                if fd == self.serv_fd:
                    self.handle_connection()
                else:
                    self.handle_client(fd)

    def handle_connection(self):
        clnt_sock, addr = self.serv_sock.accept()
        clnt_sock.setblocking(0)
        # log("new connection: ", addr)
        self.register(clnt_sock)

    def handle_client(self, fd):
        self.init_client(fd)
        request = self.recv()
        if request:
            self.handle_request(request)
        else:
            raise Exception('no epoll')
        if self.can_disconnect():
            self.disconnect()

    # 接收数据时对方断开连接，会收到EOF
    def recv(self):
        data = self.client.recv()
        message = data.decode()
        return message

    def handle_request(self, request):
        response = self.make_response(request)
        self.send_message(response)

    def handle_post(request):
        response = ''
        return response

    def handle_get(self, url):
        path = self.extend_path(url)
        self.validate(path)
        return self.normal_response(path)

    def make_response(self, request):
        try:
            method, url = self.request_line(request)
            if method and url:
                if method == 'GET':
                    response = self.handle_get(url)
                elif method == 'POST':
                    response = self.handle_post(url)
                return response
            else:
                raise BadRequest
        except ServerError:
            return self.server_error_response()
        except Forbidden:
            return self.forbidden_response()
        except NotFound:
            return self.not_found_response()
        except BadRequest:
            return self.bad_request_response()

    def send_message(self, message):
        sock = self.client.sock
        data = message.encode()
        sock.sendall(data)

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
        return self.client.is_connected()

    def init_client(self, fd):
        sock = self.sock_list[fd]
        self.client.init(fd, sock)

    def request_line(self, request):
        request = request.lstrip()
        end = request.index(' ')
        method = request[:end]
        start = end + 1
        end = request.index(' ', end + 1)
        url = request[start:end]
        return method.upper(), url

    def extend_path(self, url):
        # url = url[1:]
        # path = "/home/latin/" + url
        # if isdir(path):
        #     path += 'index.html'
        path = None
        if url == '/':
            # dir = os.path.dirname(__file__)
            url = 'index.html'

        return url

    def have_read_permission(self, path):
        if path == 'index.html':
            return True
        mode = stat(path).st_mode
        return mode & S_IRUSR or mode & S_IRGRP or mode & S_IROTH

    def normal_response(self, path):
        version = 'HTTP/1.0'
        status = '200 OK'
        status_line = version + ' ' + status + '\r\n'
        headers = {
            'Server': gethostname(),
            'Connection': 'close',
            'Content-Type': 'text/html; charset=utf-8',
        }
        header = self.format_headers(headers)
        body = self.get_html(path) + '\r\n'
        response = status_line + header + '\r\n' + body
        return response

    def format_headers(self, headers):
        header = ''
        for name, value in headers.items():
            line = name + ':' + value + '\r\n'
            header += line
        return header

    def exist_file(self, path):
        # if path == None or not isfile(path):
        #     return False
        # return True
        if path is not None:
            if path == 'index.html':
                return True
        return False

    def disconnect(self):
        fd = self.client.fd
        self.epoll_fd.unregister(fd)
        self.sock_list.pop(fd)
        # 服务器断开后 客户端才break出recv
        self.client.disconnect()

    def not_found_response(self):
        # log('404 not found')
        version = 'HTTP/1.0'
        status = '404 Not Found'
        status_line = version + ' ' + status + '\r\n'
        header = 'Server: ' + gethostname() + '\r\n'
        filename = '404.html'
        body = self.get_html(filename) + '\r\n'
        response = status_line + header + '\r\n' + body
        return response

    def server_error_response(self):
        # log('500 server error')
        version = 'HTTP/1.0'
        status = '500 Server Error'
        status_line = version + ' ' + status + '\r\n'
        header = 'Server: ' + gethostname() + '\r\n'
        filename = '500.html'
        body = self.get_html(filename) + '\r\n'
        response = status_line + header + '\r\n' + body
        return response

    def bad_request_response(self):
        # log('400 bad request')
        version = 'HTTP/1.0'
        status = '400 Bad Request'
        status_line = version + ' ' + status + '\r\n'
        header = 'Server: ' + gethostname() + '\r\n'
        filename = '400.html'
        body = self.get_html(filename) + '\r\n'
        response = status_line + header + '\r\n' + body
        return response

    def forbidden_response(self):
        # log('403 forbidden_response')
        version = 'HTTP/1.0'
        status = '403 Forbidden'
        status_line = version + ' ' + status + '\r\n'
        header = 'Server: ' + gethostname() + '\r\n'
        filename = '403.html'
        body = self.get_html(filename) + '\r\n'
        response = status_line + header + '\r\n' + body
        return response

    def get_html(self, filename):
        dir = os.path.dirname(__file__)
        path = dir + '/' + filename
        with open(path, 'r') as f:
            html = f.read()
            return html

    def clear(self):
        self.serv_sock.close()

class Client:
    def __init__(self):
        self.sock = None
        self.fd = None
        self.conn_state = True
        self.bufsize = bufsize

    def recv(self):
        data = b''
        try:
            while True:
                buf = self.sock.recv(self.bufsize)
                if self.is_EOF(buf):
                    self.is_connected = False
                    break
                data += buf
        except BlockingIOError:
            pass
        # 不会出现connectionerror
        except ConnectionError:
            log("ConnectionError")
            self.is_connected = False
        return data

    def init(self, fd, sock):
        self.fd = fd
        self.sock = sock
        self.conn_state = True

    def is_connected(self):
        return self.conn_state

    def disconnect(self):
        self.sock.close()

    def is_EOF(self, data_byte):
        return data_byte == b''

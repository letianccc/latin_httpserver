from os import stat
from os.path import isdir, isfile
from select import *
from socket import *
from stat import *
from time import sleep
import os

class HttpServer:
    def __init__(self):
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.recv_bufsize = 65535
        self.client = Client()
        self.serv_sock, self.serv_fd = self.init_server()
        self.register(self.serv_sock)

    def init_server(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        fd = sock.fileno()

        port = 8888
        # print(port)
        sock.bind(('', port))
        sock.listen()
        return sock, fd

    def register(self, socket):
        fd = socket.fileno()
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)

    def run(self):
        while True:
            epoll_list = self.epoll_fd.poll()
            self.handle_epoll(epoll_list)

    def handle_epoll(self, epoll_list):
        for fd, event in epoll_list:
            if fd == self.serv_fd:
                self.handle_connection()
            else:
                self.set_client(fd)
                request = self.recv_message()
                if request:
                    print("recv from client: ")
                    self.handle_request(request)
                if not self.client.is_connected:
                    self.disconnect()
                # sleep(10)

    def handle_connection(self):
        clnt_sock, addr = self.serv_sock.accept()
        clnt_sock.setblocking(0)
        print("new connection: ", addr)
        self.register(clnt_sock)

    def set_client(self, fd):
        sock = self.sock_list[fd]
        self.client.fd = fd
        self.client.sock = sock

    # 接收数据时对方断开连接，会收到EOF
    def recv_message(self):
        sock = self.client.sock
        data = b''
        try:
            while True:
                buf = sock.recv(self.recv_bufsize)
                if self.is_EOF(buf):
                    self.client.is_connected = False
                    break
                data += buf
        except BlockingIOError:
            pass
        except ConnectionError:
            print("ConnectionError")
            self.client.is_connected = False
        message = data.decode()
        return message

    # 发送数据时对方断开连接，会产生ConnectionError
    def send_message(self, message):
        sock = self.client.sock
        data = message.encode()
        # length = len(data)
        # size = 0
        # try:
        #     while size < length:
        #         size += sock.send(data)
        # except ConnectionError:
        #     self.client.is_connected = False
        sock.sendall(data)
        print('success send: ')
        print(message)

    def skip_space(self, index, string):
        length = len(string)
        while index < length:
            c = string[index]
            if c.isspace():
                index += 1
            else:
                break
        return index

    def word(self, index, string):
        length = len(string)
        index = self.skip_space(index, string)
        if index == length:
            return None, index

        start = index
        end = start + 1
        while end < length:
            c = string[end]
            if c.isspace():
                break
            end += 1
        w = string[start:end]
        return w, end

    def request_line(self, request):
        index = 0
        method, index = self.word(index, request)
        url, index = self.word(index, request)
        return method, url

    def extend_path(self, url):
        # url = url[1:]
        # path = "/home/latin/" + url
        # if isdir(path):
        #     path += 'index.html'
        cwd = os.getcwd()
        path = cwd + '/index.html'
        return path

    def have_read_permission(self, path):
        mode = stat(path).st_mode
        return mode & S_IRUSR or mode & S_IRGRP or mode & S_IROTH

    def send_response(self, path):
        version = 'HTTP/1.0'
        status = '200 OK'
        line = version + ' ' + status + '\n'
        header = 'Server: ' + gethostname() + '\n'\
        + 'Content-Type: text/html,application/xhtml+xml,application/xml;\n'
        try:
            with open(path, 'r') as f:
                body = f.read() + '\n'
        except IOError:
            self.send_server_error()
        response = line + header + '\n' + body
        self.send_message(response)

    def handle_post(request):
        pass

    def handle_get(self, url):
        path = self.extend_path(url)
        if not isfile(path):
            self.send_not_found()
            return
        if not self.have_read_permission(path):
            self.send_forbidden()
            return
        self.send_response(path)

    def handle_request(self, request):
        method, url = self.request_line(request)
        if method and url:
            method = method.upper()
            if method == 'GET':
                self.handle_get(url)
                return
            elif method == 'POST':
                self.handle_post(url)
                return
        self.send_bad_request()

    def is_EOF(self, data_byte):
        return data_byte == b''

    def disconnect(self):
        print("disconnect...")
        fd = self.client.fd
        sock = self.client.sock
        self.epoll_fd.unregister(fd)
        self.sock_list.pop(fd)
        # sock.close()
        # sock.shutdown(SHUT_WR)
        # 将下一个套接字的连接状态设置为True
        self.client.is_connected = True

    def send_not_found(self):
        print('not found')
        version = 'HTTP/1.0'
        status = '404 Not Found'
        response = version + ' ' + status + '\n'
        header = 'Server: ' + gethostname() + '\n'
        body = '<html>' \
               '<head>404 Not Found</head>' \
               '<body>' \
               '<h1>Not Found</h1>' \
               '<p>The requested URL /404/ was not found on this server.</p>' \
               '</body>' \
               '</html>\n'
        message = response + header + body
        self.send_message(message)

    def send_server_error(self):
        print('server error')
        version = 'HTTP/1.0'
        status = '500 Server Error'
        response = version + ' ' + status + '\n'
        header = 'Server: ' + gethostname() + '\n'
        body = '<html>' \
               '<head>500 Server Error</head>' \
               '<body>' \
               '<h1>Server Error</h1>' \
               '<p>The request failed with HTTP status 500: Server Error</p>' \
               '</body>' \
               '</html>\n'
        message = response + header + body
        self.send_message(message)

    def send_bad_request(self):
        print('bad request')
        version = 'HTTP/1.0'
        status = '400 Bad Request'
        response = version + ' ' + status + '\n'
        header = 'Server: ' + gethostname() + '\n'
        body = '<html>' \
               '<head>400 Bad Request</head>' \
               '<body>' \
               '<h1>Bad Request</h1>' \
               '<p>The request failed with HTTP status 400: Bad Request</p>' \
               '</body>' \
               '</html>\n'
        message = response + header + body
        self.send_message(message)

    def send_forbidden(self):
        print('forbidden')
        version = 'HTTP/1.0'
        status = '403 Forbidden'
        response = version + ' ' + status + '\n'
        header = 'Server: ' + gethostname() + '\n'
        body = '<html>' \
               '<head>403 Forbidden</head>' \
               '<body>' \
               '<h1>Forbidden</h1>' \
               '<p>This website declined to show this webpage</p>' \
               '</body>' \
               '</html>\n'
        message = response + header + body
        self.send_message(message)


class Client:
    def __init__(self):
        self.sock = None
        self.fd = None
        self.is_connected = True

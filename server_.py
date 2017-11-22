from os import stat
from os.path import isdir, isfile
from select import *
from socket import *
from stat import *
from time import sleep


class HttpServer:
    def __init__(self):
        self.epoll_fd = epoll()
        self.sock_list = {}
        self.serv_sock = self.init_server()
        self.serv_fd = self.serv_sock.fileno()
        self.register(self.serv_sock)
        self.clnt_sock = None
        self.clnt_fd = None
        self.is_connected = True
        self.recv_bufsize = 65535

    def init_server(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        port = 8888
        print(port)
        sock.bind(('', port))
        sock.listen()
        return sock

    def register(self, socket):
        fd = socket.fileno()
        self.sock_list[fd] = socket
        self.epoll_fd.register(fd, EPOLLIN)

    def run_epoll(self):
        while True:
            epoll_list = self.epoll_fd.poll()
            self.handle_epoll(epoll_list)

    def handle_epoll(self, epoll_list):
        for fd, event in epoll_list:
            if fd == self.serv_fd:
                clnt_sock, addr = self.serv_sock.accept()
                clnt_sock.setblocking(0)
                print("new connection: ", addr)
                self.register(clnt_sock)

            elif event & EPOLLIN:
                self.count += 1
                print('epoll: ', self.count)

                sock = self.sock_list[fd]
                self.clnt_fd = fd
                self.clnt_sock = sock
                request = self.recv_message()
                if request:
                    print("recv from client: ")
                    self.handle_request(request)
                else:
                    self.is_connected = False
                if not self.is_connected:
                    self.disconnect()
                    self.is_connected = True

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
        index += 1
        while index < length:
            c = string[index]
            if c.isspace():
                break
            index += 1
        w = string[start:index]
        return w, index

    def request_line(self, request):
        index = 0
        method, index = self.word(index, request)
        url, index = self.word(index, request)
        return method, url

    def extend_path(self, url):
        path = "/home/latin/" + url
        if isdir(path):
            path += '/index.html'
        return path

    def have_read_permission(self, path):
        mode = stat(path).st_mode
        return mode & S_IRUSR or mode & S_IRGRP or mode & S_IROTH

    def send_file(self, path):
        try:
            with open(path, 'r') as f:
                version = 'HTTP/1.0'
                status = '200 OK'
                response = version + ' ' + status + '\n'
                header = 'Server: ' + gethostname() + '\n'
                text = f.read() + '\n'
                message = response + header + text
                self.send_message(message)
        except IOError:
            self.send_server_error()

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
        self.send_file(path)

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

    def recv_message(self):
        data = b''
        try:
            while True:
                buf = self.clnt_sock.recv(self.recv_bufsize)
                if buf == b'':
                    self.is_connected = True
                    break
                data += buf

        except BlockingIOError:
            pass
        except ConnectionError:
            print("ConnectionError")
            self.is_connected = False


        message = data.decode()
        return message

    def send_message(self, message):
        data = message.encode()
        length = len(data)
        size = 0
        try:
            while size < length:
                size += self.clnt_sock.send(data)
        except ConnectionError:
            self.is_connected = False
        print('success send: ')

    def disconnect(self):
        print("disconnect...")
        fd = self.clnt_fd
        sock = self.clnt_sock
        self.epoll_fd.unregister(fd)
        self.sock_list.pop(fd)
        sock.close()

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

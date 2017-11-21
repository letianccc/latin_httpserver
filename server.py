from socket import *
from select import *
from os.path import isdir
from os import stat
from stat import *

def get_port():
    return 8888


def init_server():
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    addr = ''
    port = get_port()
    print(port)
    sock.bind((addr, port))
    sock.listen()
    return sock

def register(epoll_fd, sock_list, socket):
    fd = socket.fileno()
    sock_list[fd] = socket
    epoll_fd.register(fd, EPOLLIN)


def disconnect(epoll_fd, sock_list, fd):
    print("disconnect...")
    epoll_fd.unregister(fd)
    sock = sock_list[fd]
    sock_list.pop(fd)
    sock.close()


def skip_space(index, string):
    length = len(string)
    while index < length:
        c = string[index]
        if c == ' ' or c == '\r' or c == '\n':
            index += 1
        else:
            break
    return index


# def next_line(index, string):
#     length = len(string)
#     while index < length:
#         c = string[index]
#         if c == '\n':
#             return index + 1
#         if c == '\r':
#             if string[index+1] == '\n':
#                 return index + 2
#         index += 1
#     return index


def word(index, string):
    length = len(string)
    index = skip_space(index, string)
    if index == length:
        return None

    start = index
    index += 1
    while index < length:
        c = string[index]
        if c == ' ' or c == '\r' or c == '\n':
            break
        index += 1
    w = string[start:index]
    return w, index


def request_line(request):
    index = 0
    method, index = word(index, request)
    url, index = word(index, request)
    return method, url


def not_found():
    pass


def bad_request():
    pass


def forbidden():
    pass


def extend_path(url):
    path = "/home/latin/" + url
    if isdir(path):
        path += '/index.html'
    return path


def have_read_permission(path):
    mode = stat(path).st_mode
    return mode & S_IRUSR or mode & S_IRGRP or mode & S_IROTH


def send_data(sock, path):
    try:
        with open(path, 'r') as f:
            sock.send("HTTP/1.0 202 OK\n".encode())
            sock.send(("Server: " + gethostname() + "\n").encode())
            text = f.read()
            sock.send(text.encode())
    except OSError:
        not_found()


def handle_get(sock, url):
    path = extend_path(url)
    if not have_read_permission(path):
        forbidden()
        return
    send_data(sock, path)


def handle_post(sock, request):
    pass


def handle_request(sock, request):
    method, url = request_line(request)
    method = method.upper()
    if method == 'GET':
        handle_get(sock, url)
    elif method == 'POST':
        handle_post(sock, request)


def recv_request(sock):
    buf_size = 1024
    try:
        buf = sock.recv(buf_size)
    except Exception:
        print("recv error")
        buf = None
    return buf


def handle_epoll(epoll_list, sock_list, serv_fd):
    for fd, event in epoll_list:
        if fd == serv_fd:
            clnt_sock, addr = serv_sock.accept()
            print("new connection: ", addr)
            register(epoll_fd, sock_list, clnt_sock)

        elif event & EPOLLIN:
            sock = sock_list[fd]
            request = recv_request(sock)
            if request:
                request = request.decode()
                print("recv from client: ", request)
                handle_request(sock, request)
            else:
                disconnect(epoll_fd, sock_list, fd)


epoll_fd = epoll()
sock_list = {}
serv_sock = init_server()
register(epoll_fd, sock_list, serv_sock)

serv_fd = serv_sock.fileno()
while True:
    epoll_list = epoll_fd.poll()
    handle_epoll(epoll_list, sock_list, serv_fd)

serv_sock.close()





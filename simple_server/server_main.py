from socket import *
from simple_server.server_ import Server
addr = ('127.0.0.1', 8888)
sock = socket(AF_INET, SOCK_STREAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
sock.bind(addr)
sock.listen(6)
ctrl_sock, addr = sock.accept()
print(ctrl_sock.getsockname(), addr)
while True:
    ctrl_sock.recv(65536)
# server = Server(addr)
# server.run()

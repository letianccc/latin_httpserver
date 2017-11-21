from socket import *
from random import randint
from time import sleep


def handle_message(socket, message):
    print("recv from serv: ", message)


def disconnect(socket):
    print("disconnect...")
    socket.close()


addr = ('127.0.0.1', 8888)
sock = create_connection(addr)
buf_size = 1024
message = "GET code/python/latin_httpserver/index.html\r\n"
buf = bytes(message, encoding="utf8")
sock.send(buf)
while True:
    try:
        data = sock.recv(buf_size)
    except Exception:
        print("recv error")
        data = None

    if data:
        message = data.decode()
        handle_message(sock, message)
    else:
        disconnect(sock)
        break








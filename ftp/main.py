
from ftp.server_ import FTPServer
from .config import *


def main():
    server_addr = (SERVER_ADDR, SERVER_PORT)
    server = FTPServer(server_addr)
    server.run()

if __name__ == '__main__':
    main()

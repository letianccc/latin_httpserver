
import threading
from ftp.server_ import FTPServer
import os

class ServerThread(threading.Thread):
    def __init__(self, server_addr):
        super(ServerThread, self).__init__()
        self.server_addr = server_addr
        self.server = None

    def run(self):
        self.server = FTPServer(self.server_addr)
        self.server.run()

    def is_run(self):
        if self.server:
            return self.server.is_run()
        return False

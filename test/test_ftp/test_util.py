
import threading
from ftp.server_ import FTPServer
import os
import subprocess
from ftp.config import *
import unittest
from ftp.client_ import Client


username = 'latin'
pswd = '123'


class BaseTest(unittest.TestCase):
    def setUp(self):
        setup_clear()
        self.init_file()
        self.init_end()
        self.init_login()
        self.init_data_connect()

    def init_end(self):
        server_addr = (SERVER_ADDR, SERVER_PORT)
        thread = self.run_server(server_addr)
        self.server = thread.server
        self.client = Client(server_addr)

    def init_login(self):
        request = 'USER %s\r\n' % username
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'PASS %s\r\n' % pswd
        self.client.send_request(request)
        resp = self.client.get_response(request)

    def init_data_connect(self):
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)


    def tearDown(self):
        self.clear_file()
        self.client.clear()
        self.server.stop()
        # thread.join()
        # kill_python_process()
        # kill_port()
        # kill_python_process()

    def init_file(self):
        self.target_filename = 'p'
        self.server_path = 'server_fs/%s' % self.target_filename

    def run_server(self, server_addr):
        thread = ServerThread(server_addr)
        thread.daemon = True
        thread.start()
        while not thread.is_run():
            pass
        return thread

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

def log(*vargs, **kargs):
    print(*vargs, **kargs)




def kill_port():
    ports = ['20', '21']
    for port in ports:
        command = ["netstat -tlnp |grep :%s" % port]
        a = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

        # print(a.stdout.decode())

        result = a.stdout.decode()
        rows = result.split('\n')
        # print(result)
        target = []
        rows = rows[:-1]
        for r in rows:
            cols = r.split()
            pid_col = cols[-1]
            trailing = '/python3'
            if pid_col.endswith(trailing):
                pid = pid_col[:-len(trailing)]
                target.append(pid)
            else:
                raise Exception

        for pid in target:
            command = ['kill', '-9', pid]
            subprocess.run(command, stdout=subprocess.PIPE)

def kill_python_process():
    command = ["ps -C python3"]
    a = subprocess.run(command, shell=True, stdout=subprocess.PIPE)

    result = a.stdout.decode()
    rows = result.split('\n')
    target = []
    rows = rows[1:-1]
    cur_pid = str(os.getpid())
    for r in rows:
        cols = r.split()
        pid = cols[0]
        if pid != cur_pid:
            target.append(pid)

    for pid in target:
        command = ['kill', '-9', pid]
        subprocess.run(command, stdout=subprocess.PIPE)

def setup_clear():
    pass
    kill_port()
    kill_python_process()

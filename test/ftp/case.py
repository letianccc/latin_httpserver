
import unittest
from ftp.client_ import Client
from ftp.config import *
from util import kill_port, kill_python_process, log
from test.ftp.test_util import ServerThread
import os

username = 'latin'
pswd = '123'

class TestServer(unittest.TestCase):

    def setUp(self):
        # kill_port()
        # kill_python_process()
        self.server_addr = (SERVER_ADDR, SERVER_PORT)
        self.thread = self.run_server(self.server_addr)
        self.server = self.thread.server
        self.client = Client(self.server_addr)
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)

    def tearDown(self):
        self.clear_file()
        self.client.clear()
        self.server.stop()
        # self.thread.join()
        # kill_python_process()


    def test_PORT(self):
        self.login()
        addr = self.client.get_free_port()
        self.client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        resp = self.client.send_request(request)
        assert resp == '200 Command okay'
        assert self.client.data_sock.fileno() != -1

        addr = self.client.get_free_port()
        self.client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        resp = self.client.send_request(request)
        assert resp == '200 Command okay'
        assert self.client.data_sock.fileno() != -1

        self.tearDown()
        self.setUp()

        addr = self.client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        resp = self.client.send_request(request)
        assert resp == '530 Not logged in'

        self.tearDown()
        self.setUp()

        self.login()
        addr = self.client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        resp = self.client.send_request(request)
        assert resp == '501 Syntax error in parameters or arguments'





    def login(self):
        command = 'USER %s\r\n' % username
        self.client.send_request(command)

        command = 'PASS %s\r\n' % pswd
        self.client.send_request(command)

    def run_server(self, server_addr):
        thread = ServerThread(server_addr)
        thread.daemon = True
        thread.start()
        while not thread.is_run():
            pass
        return thread

    def clear_file(self):
        dir = 'server_fs'
        names = os.listdir(dir)
        names.remove('index')
        paths = [dir+'/'+name for name in names]
        for path in paths:
            os.remove(path)
        dir = 'client_fs'
        names = os.listdir(dir)
        names.remove('index')
        paths = [dir+'/'+name for name in names]
        for path in paths:
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

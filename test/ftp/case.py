
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


    def test_APPE(self):
        self.login()
        pathname = 'p'
        request = 'APPE %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            data = f.read()
            quarter = len(data) // 4
            self.client.send_data(data[:quarter])
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open('client_fs/index', 'rb') as source:
            with open(server_path, 'rb') as target:
                data = source.read()
                quarter = len(data) // 4
                self.assertEqual(data[:quarter], target.read())
        self.assertEqual(-1, self.client.data_sock.fileno())

        request = 'APPE %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            data = f.read()
            quarter = len(data) // 4
            self.client.send_data(data[:quarter])
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open('client_fs/index', 'rb') as source:
            with open(server_path, 'rb') as target:
                data = source.read()
                quarter = len(data) // 4
                self.assertEqual(data[:quarter]*2, target.read())
        self.assertEqual(-1, self.client.data_sock.fileno())



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

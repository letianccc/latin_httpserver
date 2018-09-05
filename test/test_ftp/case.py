
import unittest

from ftp.client_ import Client
from ftp.config import *
from util import kill_port, kill_python_process, log
from test.test_ftp.test_util import ServerThread
import os
import re

username = 'latin'
pswd = '123'

class TestServer(unittest.TestCase):

    def setUp(self):
        kill_port()
        kill_python_process()
        self.server_addr = (SERVER_ADDR, SERVER_PORT)
        thread = self.run_server(self.server_addr)
        self.server = thread.server
        self.client = Client(self.server_addr)
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)

    def tearDown(self):
        self.clear_file()
        self.client.clear()
        self.server.stop()
        # thread.join()
        # kill_python_process()

    def test_REST(self):
        self.login()
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)

        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            data = f.read()
            half = data[:len(data)//2]
            self.client.send_data(half)
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertIsNotNone(self.server.get_handler().data_sock)
        self.assertIsNotNone(self.client.data_sock)
        path = 'server_fs/%s' % pathname
        with open(path, 'rb') as target:
            with open('client_fs/index', 'rb') as source:
                data = source.read()
                quarter = data[:len(data)//2]
                self.assertEqual(target.read(), quarter)

        self.client.data_sock.close()
        size = os.path.getsize('client_fs/index') // 4
        request = 'REST %s\r\n' % size
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('350 Requested file action pending further information', resp)
        request = 'STOR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertIsNotNone(self.server.get_handler().data_sock)
        self.assertIsNotNone(self.client.data_sock)
        path = 'server_fs/%s' % pathname
        with open(path, 'rb') as target:
            with open('client_fs/index', 'rb') as source:
                data = source.read()
                data = data[:size] + data
                self.assertEqual(target.read(), data)



    def login(self):
        request = 'USER %s\r\n' % username
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'PASS %s\r\n' % pswd
        self.client.send_request(request)
        resp = self.client.get_response(request)

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

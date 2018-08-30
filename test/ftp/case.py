
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
        kill_port()
        kill_python_process()
        self.server_addr = (SERVER_ADDR, SERVER_PORT)
        self.thread = self.run_server(self.server_addr)
        self.client = Client(self.server_addr)


    def tearDown(self):
        self.client.clear()
        self.thread.stop()
        self.clear_file()
        # kill_python_process()



    def test_STOR(self):
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        with open('client_fs/index') as f:
            target_data = f.read()
            self.client.store(target_data)
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open(server_path) as f:
            self.assertEqual(target_data, f.read())
        self.assertNotEqual(-1, self.client.data_sock.fileno())
        self.tearDown()
        self.setUp()

        # 数据连接失败
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.send_request(request)
        self.assertIsNone(self.client.data_sock)
        self.assertEqual('425 Can\'t open data connection', resp)

        self.tearDown()
        self.setUp()

        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.send_request(request)
        self.client.data_sock.close()
        resp = self.client.get_response()
        self.assertEqual('426 Connection closed; transfer aborted', resp)


    def login(self):
        command = 'USER %s\r\n' % username
        self.send_request(command)

        command = 'PASS %s\r\n' % pswd
        self.send_request(command)

    def send_request(self, message):
        response = self.client.get_response(message)
        return response

    def run_server(self, server_addr):
        thread = ServerThread(server_addr)
        thread.daemon = True
        thread.start()
        while not thread.is_run():
            pass
        return thread

    def clear_file(self):
        path = 'server_fs/p'
        if os.path.exists(path):
            os.remove(path)
        path = 'client_fs/p'
        if os.path.exists(path):
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

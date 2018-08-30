
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
        self.client = Client(self.server_addr)

    def tearDown(self):
        self.client.clear()
        self.clear_file()
        self.thread.stop()
        # self.thread.join()
        # kill_python_process()

    def test_bad_sequence(self):
        command = 'PASS %s\r\n' % pswd
        response = self.client.send_request(command)
        assert '503 Bad sequence of commands' == response

    def test_bad_command(self):
        command = 'GET username\r\n'
        response = self.client.send_request(command)
        assert '502 Command not implemented' == response

    def test_login(self):
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertEqual(resp, '530 Not logged in')

    def test_USER(self):
        wrong_user = 'wrong_user'
        command = 'USER %s\r\n' % wrong_user
        response = self.client.send_request(command)
        assert '530 Not logged in' == response

        command = 'USER %s\r\n' % username
        response = self.client.send_request(command)
        assert '331 User name okay, need password' == response

    def test_PASS(self):
        command = 'USER %s\r\n' % username
        response = self.client.send_request(command)

        wrong_pswd = '1234'
        command = 'PASS %s\r\n' % wrong_pswd
        response = self.client.send_request(command)
        assert '530 Not logged in' == response

        command = 'PASS %s\r\n' % pswd
        response = self.client.send_request(command)
        assert '230 User logged in, proceed' == response

    def test_PORT(self):
        self.login()
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

    def test_MODE(self):
        self.login()
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        resp = self.client.send_request(request)
        self.assertEqual('200 Command okay', resp)
        self.assertEqual(self.client.mode, 'B')

        self.tearDown()
        self.setUp()

        self.login()
        request = 'MODE ABCDEF\r\n'
        resp = self.client.send_request(request)
        self.assertEqual('501 Syntax error in parameters or arguments', resp)
        self.assertEqual(self.client.mode, 'S')

    def test_STOR(self):
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open('client_fs/index') as source:
            with open(server_path) as target:
                self.assertEqual(source.read(), target.read())
        self.assertEqual(-1, self.client.data_sock.fileno())

        self.tearDown()
        self.setUp()

        # 数据连接失败
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertIsNone(self.client.data_sock)
        self.assertEqual('425 Can\'t open data connection', resp)

        self.tearDown()
        self.setUp()

        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.client.data_sock.close()
        resp = self.client.get_response()
        self.assertEqual('426 Connection closed; transfer aborted', resp)

    def test_RETR(self):
        with open('client_fs/index', 'rb') as source:
            with open('server_fs/p', 'wb') as target:
                target.write(source.read())
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'RETR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        data = self.client.recv_data()
        with open('server_fs/p', 'rb') as f:
            self.assertEqual(data, f.read())
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assertEqual(-1, self.client.data_sock.fileno())

    def test_BLOCK_STOR(self):
        self.login()
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        with open('client_fs/index', 'rb') as f:
            target_data = f.read()
            self.client.store_in_block(target_data)
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open(server_path, 'rb') as f:
            self.assertEqual(target_data, f.read())
        self.assertNotEqual(-1, self.client.data_sock.fileno())

    def test_BLOCK_RETR(self):
        with open('client_fs/index', 'rb') as source:
            with open('server_fs/p', 'wb') as target:
                target.write(source.read())
        self.login()
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'RETR %s\r\n' % pathname
        resp = self.client.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        data = self.client.recv_block()
        with open('server_fs/p', 'rb') as f1:
                self.assertEqual(f1.read(), data)
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assertNotEqual(-1, self.client.data_sock.fileno())





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
        path = 'server_fs/p'
        if os.path.exists(path):
            os.remove(path)
        path = 'client_fs/p'
        if os.path.exists(path):
            os.remove(path)


if __name__ == '__main__':
    unittest.main()

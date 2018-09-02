
import unittest

from ftp.client_ import Client
from ftp.config import *
from util import kill_port, kill_python_process, log
from test.ftp.util import ServerThread
import os
import re

username = 'latin'
pswd = '123'

class TestServer(unittest.TestCase):

    def setUp(self):
        kill_port()
        kill_python_process()
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

    def test_bad_sequence(self):
        request = 'PASS %s\r\n' % pswd
        response = self.client.send_request(request)
        resp = self.client.get_response(request)
        assert '503 Bad sequence of commands' == resp

    def test_bad_command(self):
        request = 'GET username\r\n'
        response = self.client.send_request(request)
        resp = self.client.get_response(request)
        assert '502 Command not implemented' == resp

    def test_login(self):
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual(resp, '530 Not logged in')

        self.tearDown()
        self.setUp()

        addr = self.client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)
        assert resp == '530 Not logged in'

    def test_USER(self):
        wrong_user = 'wrong_user'
        request = 'USER %s\r\n' % wrong_user
        response = self.client.send_request(request)
        resp = self.client.get_response(request)
        assert '530 Not logged in' == resp

        request = 'USER %s\r\n' % username
        response = self.client.send_request(request)
        resp = self.client.get_response(request)
        assert '331 User name okay, need password' == resp

    def test_PASS(self):
        request = 'USER %s\r\n' % username
        response = self.client.send_request(request)
        resp = self.client.get_response(request)

        wrong_pswd = '1234'
        request = 'PASS %s\r\n' % wrong_pswd
        response = self.client.send_request(request)
        resp = self.client.get_response(request)
        assert '530 Not logged in' == resp

        request = 'PASS %s\r\n' % pswd
        response = self.client.send_request(request)
        resp = self.client.get_response(request)
        assert '230 User logged in, proceed' == resp

    def test_PORT(self):
        self.login()
        addr = self.client.get_free_port()
        self.client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)
        assert resp == '200 Command okay'
        assert self.client.data_sock.fileno() != -1

        addr = self.client.get_free_port()
        self.client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)
        assert resp == '200 Command okay'
        assert self.client.data_sock.fileno() != -1

        self.tearDown()
        self.setUp()

        self.login()
        addr = self.client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)
        assert resp == '501 Syntax error in parameters or arguments'

    def test_MODE(self):
        self.login()
        handler = list(self.server.handlers.values())[0]
        self.assertEqual(handler.mode, 'S')
        self.assertEqual(self.client.mode, 'S')
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('200 Command okay', resp)
        handler = list(self.server.handlers.values())[0]
        self.assertEqual(handler.mode, 'B')
        self.assertEqual(self.client.mode, 'B')

        self.tearDown()
        self.setUp()

        self.login()
        handler = list(self.server.handlers.values())[0]
        self.assertEqual(handler.mode, 'S')
        self.assertEqual(self.client.mode, 'S')
        request = 'MODE ABCDEF\r\n'
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('501 Syntax error in parameters or arguments', resp)
        handler = list(self.server.handlers.values())[0]
        self.assertEqual(handler.mode, 'S')
        self.assertEqual(self.client.mode, 'S')

    def test_STOR(self):
        self.login()


        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open('client_fs/index') as source:
            with open(server_path) as target:
                self.assertEqual(source.read(), target.read())
        self.assertIsNone(self.client.data_sock)
        # self.assertIsNone(self.client.data_sock)

        self.tearDown()
        self.setUp()

        # 数据连接失败
        self.login()

        self.client.stop_listen()
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertIsNone(self.client.data_sock)
        self.assertEqual('425 Can\'t open data connection', resp)

        self.tearDown()
        self.setUp()

        self.login()


        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.client.data_sock.close()
        resp = self.client.get_response(request)
        self.assertEqual('426 Connection closed; transfer aborted', resp)

    def test_STOU(self):
        self.login()


        request = 'STOU\r\n'
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        pattern = '(?P<response>.*) (?P<path>\w+)'
        rs = re.match(pattern, resp)
        resp = rs.group('response')
        path = rs.group('path')
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % path
        with open('client_fs/index') as source:
            with open(server_path) as target:
                self.assertEqual(source.read(), target.read())
        self.assertIsNone(self.client.data_sock)

        self.tearDown()
        self.setUp()

        self.login()


        pathname = 'p'
        request = 'STOU %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        pattern = '(?P<response>.*) (?P<path>\w+)'
        rs = re.match(pattern, resp)
        resp = rs.group('response')
        path = rs.group('path')
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assertEqual(path, 'p')
        server_path = 'server_fs/%s' % path
        with open('client_fs/index') as source:
            with open(server_path) as target:
                self.assertEqual(source.read(), target.read())
        self.assertIsNone(self.client.data_sock)

        pathname = 'p'
        request = 'STOU %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        pattern = '(?P<response>.*) (?P<path>\w+)'
        rs = re.match(pattern, resp)
        resp = rs.group('response')
        path = rs.group('path')
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assertNotEqual(path, 'p')
        server_path = 'server_fs/%s' % path
        with open('client_fs/index') as source:
            with open(server_path) as target:
                self.assertEqual(source.read(), target.read())
        self.assertIsNone(self.client.data_sock)

    def test_APPE(self):
        self.login()
        pathname = 'p'
        request = 'APPE %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            data = f.read()
            quarter = len(data) // 4
            self.client.send_data(data[:quarter])
        resp = self.client.get_response(request)
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open('client_fs/index', 'rb') as source:
            with open(server_path, 'rb') as target:
                data = source.read()
                quarter = len(data) // 4
                self.assertEqual(data[:quarter], target.read())
        self.assertIsNone(self.client.data_sock)

        request = 'APPE %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            data = f.read()
            quarter = len(data) // 4
            self.client.send_data(data[:quarter])
        resp = self.client.get_response(request)
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open('client_fs/index', 'rb') as source:
            with open(server_path, 'rb') as target:
                data = source.read()
                quarter = len(data) // 4
                self.assertEqual(data[:quarter]*2, target.read())
        self.assertIsNone(self.client.data_sock)

    def test_RETR(self):
        with open('client_fs/index', 'rb') as source:
            with open('server_fs/p', 'wb') as target:
                target.write(source.read())
        self.login()


        pathname = 'p'
        request = 'RETR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        data = self.client.recv_data()
        with open('server_fs/p', 'rb') as f:
            self.assertEqual(data, f.read())
        resp = self.client.get_response(request)
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assertIsNone(self.client.data_sock)

    def test_BLOCK_STOR(self):
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
            self.client.send_data(data)
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertIsNotNone(self.server.get_handler().data_sock)
        self.assertIsNotNone(self.client.data_sock)
        path = 'server_fs/%s' % pathname
        with open(path, 'rb') as target:
            with open('client_fs/index', 'rb') as source:
                self.assertEqual(target.read(), source.read())

        self.client.send_request(request)
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
                self.assertEqual(target.read(), source.read())

        self.client.data_sock.close()
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
                self.assertEqual(target.read(), source.read())

    def test_BLOCK_RETR(self):
        with open('client_fs/index', 'rb') as source:
            with open('server_fs/p', 'wb') as target:
                target.write(source.read())
        self.login()
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)


        pathname = 'p'
        request = 'RETR %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        data = self.client.recv_block()
        with open('server_fs/p', 'rb') as f1:
                self.assertEqual(f1.read(), data)
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertNotEqual(-1, self.client.data_sock.fileno())

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

    def test_DELE(self):
        self.login()
        with open('client_fs/index', 'rb') as source:
            with open('server_fs/p', 'wb') as target:
                target.write(source.read())
        pathname = 'p1'
        request = 'DELE %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('550 Requested action not taken.File unavailable', resp)
        self.assertTrue(os.path.isfile('server_fs/p'))

        pathname = 'p'
        request = 'DELE %s\r\n' % pathname
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertFalse(os.path.isfile('server_fs/p'))

    def test_REIN(self):
        self.login()
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)

        addr = self.client.get_free_port()

        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'REIN\r\n'
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('220 Service ready for new user', resp)
        self.assertIsNone(self.client.data_sock)
        handler = list(self.server.handlers.values())[0]
        self.assertIsNotNone(handler.sock)
        self.assertEqual(handler.sock.getsockname(), self.client.ctrl_sock.getpeername())
        self.assertEqual(handler.sock.getpeername(), self.client.ctrl_sock.getsockname())
        self.assertDictEqual(handler.login_users, {})
        self.assertIsNone(handler.data_sock)
        self.assertIsNone(self.client.data_sock)
        self.assertEqual(handler.mode, 'S')
        self.assertEqual(self.client.mode, 'S')

        addr = self.client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)
        assert resp == '530 Not logged in'



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

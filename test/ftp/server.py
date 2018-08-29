
import unittest
from ftp.client_ import Client
from ftp.config import *
from util import kill_port, kill_python_process, log
from test.ftp.test_util import ServerThread

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
        self.thread.stop()
        # kill_python_process()

    def test_bad_sequence(self):
        command = 'PASS %s\r\n' % pswd
        response = self.send_request(command)
        assert '503 Bad sequence of commands' == response

    def test_bad_command(self):
        command = 'GET username\r\n'
        response = self.send_request(command)
        assert '502 Command not implemented' == response

    def test_USER(self):
        wrong_user = 'wrong_user'
        command = 'USER %s\r\n' % wrong_user
        response = self.send_request(command)
        assert '530 Not logged in' == response

        command = 'USER %s\r\n' % username
        response = self.send_request(command)
        assert '331 User name okay, need password' == response

    def test_PASS(self):
        command = 'USER %s\r\n' % username
        response = self.send_request(command)

        wrong_pswd = '1234'
        command = 'PASS %s\r\n' % wrong_pswd
        response = self.send_request(command)
        assert '530 Not logged in' == response

        command = 'PASS %s\r\n' % pswd
        response = self.send_request(command)
        assert '230 User logged in, proceed' == response

    # def test_PORT(self):
    #     self.login()
    #     addr = self.client.get_free_port()
    #     self.client.make_data_connect(addr)
    #     request = 'PORT %s,%s\r\n' % addr
    #     resp = self.send_request(request)
    #     assert resp == '200 Command okay'
    #     assert self.client.data_sock.fileno() != -1
    #
    #     self.tearDown()
    #     self.setUp()
    #
    #     addr = self.client.get_free_port()
    #     request = 'PORT %s,%s\r\n' % addr
    #     resp = self.send_request(request)
    #     assert resp == '530 Not logged in'
    #
    #     self.tearDown()
    #     self.setUp()
    #
    #     self.login()
    #     addr = self.client.get_free_port()
    #     request = 'PORT %s,%s\r\n' % addr
    #     resp = self.send_request(request)
    #     assert resp == '501 Syntax error in parameters or arguments'

    def test_STOR(self):
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        with open('test') as f:
            target_data = f.read()
            self.client.store(target_data)
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        server_path = 'server_fs/%s' % pathname
        with open(server_path) as f:
            self.assertEqual(target_data, f.read())

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

    def test_RETR(self):
        self.login()
        addr = self.client.ctrl_sock.getsockname()
        self.client.make_data_connect(addr)
        pathname = 'p'
        request = 'RETR %s\r\n' % pathname
        resp = self.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        data = self.client.recv_data()
        with open('server_fs/p') as f:
            self.assertEqual(data, f.read())
        resp = self.client.get_response()
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)

    def test_BLOCK(self):
        pass

    def test_login(self):
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.send_request(request)
        self.assertEqual(resp, '530 Not logged in')


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


if __name__ == '__main__':
    unittest.main()

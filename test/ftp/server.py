
import unittest
from ftp.client_ import Client
from ftp.config import *
from util import kill_pid, kill_python_process
from test.ftp.test_util import ServerThread

username = 'latin'
pswd = '123'

class TestServer(unittest.TestCase):

    def setUp(self):
        print('setup')
        kill_python_process()
        self.server_addr = (SERVER_ADDR, SERVER_PORT)
        self.thread = self.run_server(self.server_addr)
        self.client = Client(self.server_addr)


    def tearDown(self):
        print('tearDown')
        self.thread.stop()
        self.client.clear()
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
        print('pass')
        command = 'USER %s\r\n' % username
        response = self.send_request(command)

        wrong_pswd = '1234'
        command = 'PASS %s\r\n' % wrong_pswd
        response = self.send_request(command)
        assert '530 Not logged in' == response

        command = 'PASS %s\r\n' % pswd
        response = self.send_request(command)
        assert '230 User logged in, proceed' == response

    def test_PORT1(self):
        self.login()
        addr = self.client.get_free_port()
        self.client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        resp = self.send_request(request)
        assert resp == '200 Command okay'
        assert self.client.data_sock.fileno() != -1


    def test_POST(self):
        self.login()
        addr = self.client.get_free_port()
        self.client.make_data_connect(addr)
        request = 'PORT %s,%s\r\n' % addr
        resp = self.send_request(request)
        assert resp == '200 Command okay'
        assert self.client.data_sock.fileno() != -1

        # self.tearDown()
        # self.setUp()

        # addr = self.client.get_free_port()
        # request = 'PORT %s,%s\r\n' % addr
        # resp = self.send_request(request)
        # assert resp == '530 Not logged in'

        # self.tearDown()
        # self.setUp()
        #
        # self.login()
        # addr = self.client.get_free_port()
        # request = 'PORT %s,%s\r\n' % addr
        # resp = self.send_request(request)
        # assert resp == '501 Syntax error in parameters or arguments'

    def test_STOR(self):
        self.login()
        pathname = 'p'
        request = 'STOR %s\r\n' % pathname
        resp = self.send_request(request)
        assert resp == 'ok'


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

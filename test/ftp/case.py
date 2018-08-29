
import unittest
from ftp.client_ import Client
from ftp.config import *
from util import kill_port, kill_python_process, log
from test.ftp.test_util import ServerThread

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
        # kill_python_process()


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

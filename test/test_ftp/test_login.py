#coding=utf-8

import unittest
from test_util import BaseTest

username = 'latin'
pswd = '123'

class TestServer(BaseTest):
    def init_login(self):
        pass

    def init_data_connect(self):
        pass

    def init_file(self):
        pass

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

    def tearDown(self):
        self.client.clear()
        self.server.stop()


if __name__ == '__main__':
    unittest.main()

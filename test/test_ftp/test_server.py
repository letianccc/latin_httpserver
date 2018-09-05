#coding=utf-8

import unittest
from test_util import BaseTest
import os

class TestServer(BaseTest):

    def test_PORT(self):

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


        addr = self.client.get_free_port()
        request = 'PORT %s,%s\r\n' % addr
        self.client.send_request(request)
        resp = self.client.get_response(request)
        assert resp == '501 Syntax error in parameters or arguments'

    def test_MODE(self):

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

    def test_DELE(self):

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

    def tearDown(self):
        self.client.clear()
        self.server.stop()


if __name__ == '__main__':
    unittest.main()

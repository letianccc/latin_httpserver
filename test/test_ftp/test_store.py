#coding=utf-8

import unittest
from test_util import BaseTest
import os
import re

class TestServer(BaseTest):

    def test_STOR(self):
        request = 'STOR %s\r\n' % self.target_filename
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertEqual('125 Data connection already open; transfer starting', resp)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        self.assertEqual('226 Closing data connection.Requested file action successful', resp)
        self.assert_file()
        self.assertIsNone(self.client.data_sock)

        self.tearDown()
        self.setUp()

        # 数据连接失败
        self.client.stop_listen()

        request = 'STOR %s\r\n' % self.target_filename
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.assertIsNone(self.client.data_sock)
        self.assertEqual('425 Can\'t open data connection', resp)

        self.tearDown()
        self.setUp()

        request = 'STOR %s\r\n' % self.target_filename
        self.client.send_request(request)
        resp = self.client.get_response(request)
        self.client.data_sock.close()
        resp = self.client.get_response(request)
        self.assertEqual('426 Connection closed; transfer aborted', resp)

    def test_STOU(self):
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
        self.assert_file(server_path)
        self.assertIsNone(self.client.data_sock)

        self.tearDown()
        self.setUp()

        request = 'STOU %s\r\n' % self.target_filename
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
        self.assert_file(server_path)
        self.assertIsNone(self.client.data_sock)

        request = 'STOU %s\r\n' % self.target_filename
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
        self.assert_file(server_path)
        self.assertIsNone(self.client.data_sock)

    def test_APPE(self):
        request = 'APPE %s\r\n' % self.target_filename
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
        server_path = 'server_fs/%s' % self.target_filename
        with open('client_fs/index', 'rb') as source:
            with open(server_path, 'rb') as target:
                data = source.read()
                quarter = len(data) // 4
                self.assertEqual(data[:quarter], target.read())
        self.assertIsNone(self.client.data_sock)

        request = 'APPE %s\r\n' % self.target_filename
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
        server_path = 'server_fs/%s' % self.target_filename
        with open('client_fs/index', 'rb') as source:
            with open(server_path, 'rb') as target:
                data = source.read()
                quarter = len(data) // 4
                self.assertEqual(data[:quarter]*2, target.read())
        self.assertIsNone(self.client.data_sock)

    def test_BLOCK_STOR(self):
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'STOR %s\r\n' % self.target_filename
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
        self.assert_file()

        self.client.send_request(request)
        self.assertIsNotNone(self.client.data_sock)
        with open('client_fs/index', 'rb') as f:
            self.client.send_data(f.read())
        resp = self.client.get_response(request)
        self.assertEqual('250 Requested file action okay, completed', resp)
        self.assertIsNotNone(self.server.get_handler().data_sock)
        self.assertIsNotNone(self.client.data_sock)
        self.assert_file()

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
        self.assert_file()

    def test_REST(self):
        request = 'MODE %s-%s\r\n' % ('B', 'Block')
        self.client.send_request(request)
        resp = self.client.get_response(request)

        request = 'STOR %s\r\n' % self.target_filename
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
        path = 'server_fs/%s' % self.target_filename
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
        request = 'STOR %s\r\n' % self.target_filename
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
        path = 'server_fs/%s' % self.target_filename
        with open(path, 'rb') as target:
            with open('client_fs/index', 'rb') as source:
                data = source.read()
                data = data[:size] + data
                self.assertEqual(target.read(), data)

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

    def init_file(self):
        self.target_filename = 'p'
        self.server_path = 'server_fs/%s' % self.target_filename

    def assert_file(self, server_path=None):
        server_path = server_path if server_path else self.server_path
        with open('client_fs/index') as source:
            with open(server_path) as target:
                self.assertEqual(source.read(), target.read())

if __name__ == '__main__':
    unittest.main()

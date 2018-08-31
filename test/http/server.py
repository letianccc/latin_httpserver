
import unittest
from httpserver.client_ import Client
from httpserver.server_ import HttpServer
import threading
from httpserver.config import *

class ServerThread(threading.Thread):
    def __init__(self, server_addr):
        super(ServerThread, self).__init__()
        self.server_addr = server_addr
        self.server = None

    def run(self):
        self.server = HttpServer(self.server_addr)
        self.server.run()

    def clear(self):
        self.server.clear()

def run_server(server_addr):
    thread = ServerThread(server_addr)
    thread.daemon = True
    thread.start()
    return thread



class TestServer(unittest.TestCase):

    def setUp(self):
        self.server_addr = (SERVER_ADDR, SERVER_PORT)
        self.thread = run_server(self.server_addr)
        while not self.thread.server:
            pass

    def tearDown(self):
        self.thread.clear()

    def test_200(self):
        url = '/'
        response = self.send_request(url)
        assert 'HTTP/1.0 200 OK' in response

    def test_400(self):
        url = '/400'
        response = self.send_request(url)
        assert 'HTTP/1.0 400 Bad Request' in response

    def test_403(self):
        url = '/403'
        response = self.send_request(url)
        assert 'HTTP/1.0 403 Forbidden' in response

    def test_404(self):
        url = '/404'
        response = self.send_request(url)
        assert 'HTTP/1.0 404 Not Found' in response

    def test_500(self):
        url = '/500'
        response = self.send_request(url)
        assert 'HTTP/1.0 500 Server Error' in response

    def send_request(self, url):
        # server_addr = ('127.0.0.1', 8888)
        method = 'GET'
        version = 'HTTP/1.1'
        request_line = ' '.join([method, url, version]) + '\r\n'
        message = request_line  + '\r\n'
        c = Client(self.server_addr)
        response = c.get_response(message)
        return response

if __name__ == '__main__':
    unittest.main()

import re
from .entity.user import User, session
from util import log
import socket

bufsize = 65536

users = [
    {'user': 'latin',
    'password':'123'}
]

class ControlHandler:
    def __init__(self, server):
        self.sock = socket
        self.bufsize = bufsize
        self.user_wait = {}
        self.login_users = {}
        self.init()
        self.server = server

    def init(self):
        self.init_db()
        self.cmd_to_handler = self.get_map()

    def set_socket(self, socket, fd):
        self.sock = socket
        self.fd = fd
        self.conn_state = True

    def init_db(self):
        self.session = session

    def get_map(self):
        return {
            'USER': self.handle_USER,
            'PASS': self.handle_PASS,
            'PORT': self.handle_PORT,
            'STOR': self.handle_STOR,
        }

    def handle(self):
        req = self.recv_message()
        if req == '':
            self.server.disconnect()
        else:
            resp = self.make_response(req)
            self.send_message(resp)

    def recv_message(self):
        data = b''
        try:
            while True:
                buf = self.sock.recv(self.bufsize)
                if self.is_EOF(buf):
                    self.is_connected = False
                    break
                data += buf
        except BlockingIOError:
            pass
        message = data.decode()
        return message

    def make_response(self, request):
        self.request = request
        pattern = '(?P<cmd>\w+) (?P<arg>\S+)\r\n'
        rs = re.match(pattern, request)
        if rs is None:
            resp = '500 Syntax error, command unrecognized'
            return resp
        cmd = rs.group('cmd')
        arg = rs.group('arg')
        cmd = cmd.upper()

        handler = self.cmd_to_handler.get(cmd, None)
        if handler:
            resp = handler(arg)
        else:
            resp = '502 Command not implemented'
        return resp



    def handle_USER(self, username):
        user = session.query(User).filter(User.name==username).first()
        if user:
            self.user_wait[self.sock] = user
            resp = '331 User name okay, need password'
        else:
            resp = '530 Not logged in'
        return resp

    def handle_PASS(self, password):
        if self.sock not in self.user_wait:
            resp = '503 Bad sequence of commands'
        else:
            user = self.user_wait[self.sock]
            if password == user.password:
                self.login(user)
                resp = '230 User logged in, proceed'
            else:
                resp = '530 Not logged in'
        return resp

    def handle_PORT(self, addr):
        addr = addr.split(',')
        host = addr[0]
        port = addr[1]
        addr = (host, port)
        if not self.is_login():
            resp = '530 Not logged in'
        else:
            try:
                self.data_sock, self.data_fd = self.server.create_data_sock(addr)
                resp = '200 Command okay'
            except ConnectionRefusedError:
                resp = '501 Syntax error in parameters or arguments'
        return resp

    def handle_STOR(self, pathname):
        resp = 'ok'
        return resp

    def is_login(self):
        for sock in self.login_users.keys():
            if sock is self.sock:
                return True
        return False

    def login(self, user):
        self.login_users[self.sock] = user

    def send_message(self, message):
        data = message.encode()
        self.sock.sendall(data)

    def is_connected(self):
        return self.conn_state

    def disconnect(self):
        # self.sock.close()
        # self.data_sock.close()
        self.session.close()

    def is_EOF(self, data_byte):
        return data_byte == b''

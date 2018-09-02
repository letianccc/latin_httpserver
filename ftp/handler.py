import re
from .entity.user import User, session
from .entity.exception import HandleError

from util import log
import socket
import tempfile
import os.path
from .config import BLOCK_PAYLOAD_CAPACITY

bufsize = 65536

users = [
    {'user': 'latin',
    'password':'123'}
]
cur_dir = 'server_fs'



class ControlHandler:
    def __init__(self, socket, server):
        self.sock = socket
        self.bufsize = bufsize
        self.user_wait = {}
        self.login_users = {}
        self.init()
        self.server = server
        self.data_sock = None
        self.mode = 'S'
        self.marker = 0
        self.target_marker = 0

    def init(self):
        self.init_db()
        self.cmd_to_handler = self.get_map()

    def init_db(self):
        self.session = session

    def get_map(self):
        return {
            'USER': self.handle_USER,
            'PASS': self.handle_PASS,
            'PORT': self.handle_PORT,
            'STOR': self.handle_TRAN,
            'RETR': self.handle_TRAN,
            'MODE': self.handle_MODE,
            'REIN': self.handle_REIN,
            'STOU': self.handle_TRAN,
            'APPE': self.handle_TRAN,
            'DELE': self.handle_DELE,
            'REST': self.handle_REST,
        }

    def handle(self, fd):
        if fd != self.sock.fileno():
            if self.data_sock.recv(1) == b'':
                self.server.disconnect(self.data_sock)
                return
            else:
                raise Exception
        req = self.recv_request()
        if req == '':
            self.server.disconnect(self.sock)
        else:
            try:
                resp = self.handle_request(req)
                self.send_response(resp)
            except ConnectionAbortedError as e:
                resp = '426 Connection closed; transfer aborted'
                self.send_response(resp)
            except ConnectionRefusedError as e:
                resp = '425 Can\'t open data connection'
                self.send_response(resp)
            except HandleError as e:
                resp, = e.args
                self.send_response(resp)

    def handle_request(self, request):
        self.request = request
        pattern = '(?P<cmd>\w+)( (?P<arg>\S+))?\r\n'
        rs = re.match(pattern, request)
        if rs is None:
            raise HandleError('500 Syntax error, command unrecognized')
            return resp

        rs = rs.groupdict()
        cmd = rs.get('cmd')
        arg = rs.get('arg')
        cmd = cmd.upper()

        handler = self.cmd_to_handler.get(cmd, None)
        if handler:
            if handler.__name__ == 'handle_TRAN':
                resp = handler(cmd, arg)
            else:
                resp = handler(arg)
        else:
            raise HandleError('502 Command not implemented')
        return resp

    def handle_USER(self, username):
        user = session.query(User).filter(User.name==username).first()
        if user:
            self.user_wait[self.sock] = user
            resp = '331 User name okay, need password'
        else:
            raise HandleError('530 Not logged in')
        return resp

    def handle_PASS(self, password):
        if self.sock not in self.user_wait:
            raise HandleError('503 Bad sequence of commands')
        else:
            user = self.user_wait[self.sock]
            if password == user.password:
                self.login(user)
                resp = '230 User logged in, proceed'
            else:
                raise HandleError('530 Not logged in')
        return resp

    def handle_PORT(self, addr):
        addr = addr.split(',')
        host = addr[0]
        port = int(addr[1])
        addr = (host, port)
        if not self.is_login():
            raise HandleError('530 Not logged in')
        else:
            if self.data_sock:
                self.server.disconnect(self.data_sock)
            server_addr = self.sock.getsockname()[0], 20
            client_addr = addr
            try:
                self.data_sock = self.server.create_data_sock(client_addr, server_addr)
                resp = '200 Command okay'
            except ConnectionRefusedError:
                raise HandleError('501 Syntax error in parameters or arguments')

        return resp

    def handle_MODE(self, mode):
        if not self.is_login():
            raise HandleError('530 Not logged in')
        else:
            resp = '200 Command okay'
            if mode == 'B-Block':
                self.mode = 'B'
            elif mode == 'S-Stream':
                self.mode = 'S'
            elif mode == 'C-Compressed':
                self.mode = 'C'
            else:
                raise HandleError('501 Syntax error in parameters or arguments')
        return resp

    def handle_REIN(self, arg):
        self.reinit()
        resp = '220 Service ready for new user'
        return resp

    def handle_TRAN(self, command, filename):
        if not self.is_login():
            raise HandleError('530 Not logged in')
        if not self.is_connect_data():
            self.make_data_connect()
            if self.is_connect_data():
                resp = '125 Data connection already open; transfer starting'
                self.send_response(resp)
            else:
                raise HandleError('425 Can\'t open data connection')
        filename = self.get_filename(command, filename)
        if command == 'RETR':
            self.retrive_file(command, filename)
        else:
            self.store_file(command, filename)

        if self.mode == 'S':
            resp = '226 Closing data connection.Requested file action successful'
        elif self.mode == 'B':
            resp = '250 Requested file action okay, completed'
        else:
            raise Exception
        if command == 'STOU':
            resp = '%s %s' % (resp, filename)
        return resp

    def handle_DELE(self, filename):
        if not self.is_login():
            raise HandleError('530 Not logged in')
        path = '%s/%s' %(cur_dir, filename)
        if not os.path.isfile(path):
            raise HandleError('550 Requested action not taken.File unavailable')
        else:
            os.remove(path)
            return '250 Requested file action okay, completed'

    def handle_REST(self, marker):
        if not self.is_login():
            raise HandleError('530 Not logged in')
        if self.marker < int(marker):
            raise Exception(self.marker, marker)
        self.target_marker = int(marker)
        return '350 Requested file action pending further information'

    def store_file(self, command, filename):
        path = '%s/%s' %(cur_dir, filename)
        mode = self.get_mode(command)
        data = self.recv_data()
        with open(path, mode) as f:
            f.seek(self.target_marker)
            f.write(data)
        self.target_marker = 0

    def get_mode(self, command):
        if self.target_marker > 0:
            mode = 'rb+'
        else:
            if command == 'STOR' or command == 'STOU':
                mode = 'wb'
            elif command == 'APPE':
                mode = 'ab'
        return mode

    def retrive_file(self, command, filename):
        path = '%s/%s' %(cur_dir, filename)
        with open(path, 'rb') as f:
            data = f.read()
            self.send_data(data)

    def get_filename(self, command, filename):
        if command == 'STOU':
            if not self.is_usable(filename):
                tf = tempfile.NamedTemporaryFile()
                filename = tf.name[len('/temp/'):]
                tf.close()
        return filename

    def is_usable(self, filename):
        if not filename:
            return False
        path = '%s/%s' % (cur_dir, filename)
        return not os.path.isfile(path)

    def make_data_connect(self):
        server_addr = self.sock.getsockname()[0], 20
        client_addr = self.sock.getpeername()
        self.data_sock = self.server.create_data_sock(client_addr, server_addr)

    def is_login(self):
        for sock in self.login_users.keys():
            if sock is self.sock:
                return True
        return False

    def login(self, user):
        self.login_users[self.sock] = user

    def reinit(self):
        if self.data_sock:
            self.server.disconnect(self.data_sock)
        self.user_wait = {}
        self.login_users = {}
        self.mode = 'S'

    def send_response(self, message):
        data = message.encode()
        self.sock.sendall(data)

    def send_data(self, data):
        if self.mode == 'S':
            self.send_stream(data)
        elif self.mode == 'B':
            self.send_block(data)

    def send_stream(self, data):
        self.data_sock.sendall(data)
        self.server.disconnect(self.data_sock)

    def send_block(self, data):
        size = BLOCK_PAYLOAD_CAPACITY
        rest = data
        while rest:
            data = rest[:size]
            rest = rest[size:]
            block = self.format_block(data, rest)
            self.data_sock.sendall(block)

    def format_block(self, payload, rest):
        eof_code = 64
        normal_code = 0
        eof_byte = (eof_code).to_bytes(1, 'big')
        normal_byte = (normal_code).to_bytes(1, 'big')
        is_eof = rest == b''
        size = len(payload)
        count_field = (size).to_bytes(2, 'big')
        if is_eof:
            desc_field = eof_byte
        else:
            desc_field = normal_byte
        block = desc_field + count_field + payload
        return block

    def recv_request(self):
        data = b''
        try:
            while True:
                buf = self.sock.recv(self.bufsize)
                is_eof = buf == b''
                if is_eof:
                    break
                data += buf
        except BlockingIOError:
            pass
        message = data.decode()
        return message

    def recv_data(self):
        if self.mode == 'S':
            data = self.recv_stream()
        elif self.mode == 'B':
            data = self.recv_block()
        if data == b'':
            raise ConnectionAbortedError
        return data


    def recv_stream(self):
        data = b''
        while True:
            buf = self.data_sock.recv(self.bufsize)
            data += buf
            is_eof = buf == b''
            if is_eof:
                self.server.disconnect(self.data_sock)
                # self.disconnect_data()
                return data

    def recv_block(self):
        data = b''
        restart_code = 16
        while True:
            header = self.data_sock.recv(3)
            desc = int.from_bytes(header[0:1], byteorder='big')
            count = int.from_bytes(header[1:3], byteorder='big')
            payload = self.data_sock.recv(count)
            is_disconnect = len(header) != 3 or len(payload) != count
            if is_disconnect:
                return b''
            is_restart = desc & restart_code > 0
            if is_restart:
                self.marker = int.from_bytes(payload, byteorder='big')
                resp = '110 Restart marker reply MARK %s = %s\r\n' % (self.marker, self.marker)
                self.send_response(resp)
            else:
                data += payload
            is_eof = desc & 64 > 0
            if is_eof:
                return data

    def disconnect(self, sock):
        if sock == self.sock:
            self.disconnect_ctrl()
        else:
            self.disconnect_data()

    def disconnect_ctrl(self):
        self.session.close()
        self.sock.close()

    def disconnect_data(self):
        self.data_sock.close()
        self.data_sock = None

    def is_connect_data(self):
        return self.data_sock and self.data_sock.fileno() != -1

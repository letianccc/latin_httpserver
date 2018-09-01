import re
from .entity.user import User, session
from util import log
import socket
import tempfile
import os.path

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
        }

    def handle(self):
        req = self.recv_message()
        if req == '':
            self.server.disconnect()
        else:
            resp = self.make_response(req)
            self.send_message(resp)

    def make_response(self, request):
        self.request = request
        pattern = '(?P<cmd>\w+)( (?P<arg>\S+))?\r\n'
        rs = re.match(pattern, request)
        if rs is None:
            resp = '500 Syntax error, command unrecognized'
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
        port = int(addr[1])
        addr = (host, port)
        if not self.is_login():
            resp = '530 Not logged in'
        else:
            if self.data_sock:
                self.disconnect_data()
            server_addr = self.sock.getsockname()[0], 20
            client_addr = addr
            data_sock = self.server.create_data_sock(client_addr, server_addr)
            if data_sock:
                self.data_sock = data_sock
                resp = '200 Command okay'
            else:
                resp = '501 Syntax error in parameters or arguments'
        return resp

    def handle_MODE(self, mode):
        if not self.is_login():
            resp = '530 Not logged in'
        else:
            resp = '200 Command okay'
            if mode == 'B-Block':
                self.mode = 'B'
            elif mode == 'S-Stream':
                self.mode = 'S'
            elif mode == 'C-Compressed':
                self.mode = 'C'
            else:
                resp = '501 Syntax error in parameters or arguments'
        return resp

    def handle_REIN(self, arg):
        self.reinit()
        resp = '220 Service ready for new user'
        return resp

    def handle_TRAN(self, command, filename):
        if not self.is_login():
            return '530 Not logged in'
        self.make_data_connect()
        if not self.enable_data_connect():
            return '425 Can\'t open data connection'
        filename = self.get_filename(command, filename)
        try:
            if command == 'RETR':
                self.retrive_file(command, filename)
            else:
                self.store_file(command, filename)
        except ConnectionAbortedError:
            return '426 Connection closed; transfer aborted'
        except IOError:
            return '451 Requested action aborted: local error in processing'

        if self.mode == 'S':
            resp = '226 Closing data connection.Requested file action successful'
        elif self.mode == 'B':
            resp = '250 Requested file action okay, completed'
        if command == 'STOU':
            resp = '%s\r\n%s' % (resp, filename)
        return resp

    def store_file(self, command, filename):
        data = self.recv_data(self.data_sock)
        if data == b'':
            raise ConnectionAbortedError

        path = '%s/%s' %(cur_dir, filename)
        if command == 'STOR' or command == 'STOU':
            mode = 'wb'
        elif command == 'APPE':
            mode = 'ab'
        with open(path, mode) as f:
            f.write(data)

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

        if self.data_sock:
            resp = '125 Data connection already open; transfer starting'
            self.send_message(resp)



    def enable_data_connect(self):
        return self.data_sock is not None

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

    def send_data(self, data):
        if self.mode == 'S':
            self.data_sock.sendall(data)
            self.data_sock.close()
        elif self.mode == 'B':
            self.store_in_block(data)

    def store_in_block(self, data):
        payload_capacity = 65536
        rest = data
        while rest:
            data = rest[:payload_capacity]
            rest = rest[payload_capacity:]
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

    def recv_message(self, sock=None):
        if sock is None:
            sock = self.sock
        data = b''
        try:
            while True:
                buf = sock.recv(self.bufsize)
                if self.is_EOF(buf):
                    self.is_connected = False
                    break
                data += buf
        except BlockingIOError:
            pass
        message = data.decode()
        return message

    def recv_data(self, sock):
        data = b''
        if self.mode == 'S':
            return self.recv_stream(sock)
        elif self.mode == 'B':
            return self.recv_block(sock)

    def recv_stream(self, sock):
        data = b''
        while True:
            buf = sock.recv(self.bufsize)
            data += buf
            if self.is_EOF(buf):
                sock.close()
                return data

    def recv_block(self, sock):
        data = b''
        while True:
            header = sock.recv(3)
            desc = int.from_bytes(header[0:1], byteorder='big')
            count = int.from_bytes(header[1:3], byteorder='big')
            payload = sock.recv(count)
            disconnect = len(header) != 3 or len(payload) != count
            if disconnect:
                return ''
            data += payload
            if self.is_block_eof(desc):
                return data


    def is_connected(self):
        return self.conn_state

    def disconnect(self):
        self.session.close()
        self.sock.close()
        if self.data_sock:
            self.data_sock.close()

    def disconnect_data(self):
        self.data_sock.close()
        self.data_sock = None

    def reinit(self):
        if self.data_sock:
            self.data_sock.close()
        self.user_wait = {}
        self.login_users = {}
        self.data_sock = None
        self.mode = 'S'


    def is_block_eof(self, desc):
        return desc & 64 > 0


    def is_EOF(self, data_byte):
        return data_byte == b''

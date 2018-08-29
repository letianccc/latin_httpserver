
import unittest
from socket import *


sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('', 21))
sock.listen()
print(sock.fileno())
print(sock.fileno())

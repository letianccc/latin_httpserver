
import unittest
from socket import *


sock = socket(AF_INET, SOCK_STREAM)
sock.bind(('', 21))
sock.listen()

sock = socket(AF_INET, SOCK_STREAM)
sock.connect(('', 21))
sock.listen()

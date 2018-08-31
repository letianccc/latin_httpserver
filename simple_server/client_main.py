
from socket import  *
import  time
from simple_server.client_ import Client


addr = ('127.0.0.1', 8888)
# client_addr = ('127.0.0.1', 12345)


sock = create_connection(addr)
sock = socket(AF_INET, SOCK_STREAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
# sock.connect(addr)
time.sleep(2)
sock.close()
print(sock.fileno())
# sock1 = socket(AF_INET, SOCK_STREAM)
# sock1.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
# sock1.bind(client_addr)
# sock1.listen(5)


# sock = create_connection(addr)

# print(sock.getsockname(), sock.getpeername())
# for i in range(10):
#     sock.sendall('aaaa'.encode())
#     print('sleep', flush=True)
#     time.sleep(1)

# client = Client(addr)
# client.run()


from server_ import HttpServer



def main():
    server_addr = ('127.0.0.1', 8888)
    server = HttpServer(server_addr)
    server.run()

if __name__ == '__main__':
    main()

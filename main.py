from server_ import HttpServer


def main():
    server = HttpServer()
    server.run_epoll()


main()

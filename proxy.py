# Andre Dasalla
# CPSC 4510
# Project 1 : Web Proxy

import sys
from socket import *
from urllib.parse import urlparse
from pathlib import Path

# global HashMap which maps URI to file path (Cache)
# Is Cache Persistent?
# This could also be a set of URIs, if the URI is in the set that means it exists in the folder and can be accessed at
# ./cache/{URI}
cache = set()


def parse_port():
    """Parses CLI Argument for Port Number"""
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 proxy.py {port}")
    try:
        port = int(sys.argv[1])
        if port < 1024 or port > 65535:
            sys.exit("Port must be between 1024-65535")
    except ValueError:
        sys.exit("Invalid Port!")
    return port


def listen(port: int):
    """Listen for incoming TCP Connections

    :param port: Integer port number
    :return: None
    """
    BUFF_SIZE = 1024
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(1)
    print("The server is ready to receive...")

    while True:
        conn_socket, addr = server_socket.accept()
        message = conn_socket.recv(BUFF_SIZE).decode()
        print(message)
        method, uri, httpVers = parse_request(message)
        if is_cached(uri):
            # send(conn_socket, getCachedFile(uri))
            continue
        host, port, path = parse_uri(uri)
        # constructRequest()
        # resp = send(URL, reqMsg)
        # cache(resp)
        conn_socket.send("resp\n".encode())
        conn_socket.close()
    server_socket.close()


def send(conn_socket: socket, msg: str) -> None:
    conn_socket.send(msg.encode())
    print(msg)
    return


def construct_request(method, host, path):
    """Constructs a request message to the host server

    :param method: HTTP Verb (GET)
    :param host: Host Name
    :param path: Path
    :return: Request Message string
    """
    req = f"{method.upper()} {path} HTTP/1.0\r\n" \
          f"Host: {host}\r\n" \
          f"Connection: close\r\n"

    return req


def construct_response():
    return


def get_cached_file(uri):
    return


def parse_request(msg: str):
    """Parse HTTP message for method, uri, and HTTP Version

    :param msg:
    :return: Tuple containing the method, uri, and http version
    """
    method, uri, httpVers = msg.split(' ')

    return method, uri, httpVers


def parse_uri(uri: str):
    """Parse URI into host, port, and path

    :param uri:
    :return: Tuple containing the host, port, and path
    """
    parsedURL = urlparse(uri)
    host = parsedURL.hostname
    port = parsedURL.port if parsedURL.port else 80
    path = parsedURL.path

    return host, port, path


def is_cached(uri: str):
    return uri in cache


def init_cache():
    path = Path('./cache')
    if not path.exists():
        path.mkdir()


if __name__ == '__main__':
    init_cache()
    port = parse_port()
    listen(port)

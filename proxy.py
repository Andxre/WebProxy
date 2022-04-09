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
# ./cache/{URI} where URI is stripped of all invalid characters (. : / etc.)
cache = set()
# Size of message buffer
BUFF_SIZE = 2048


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
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(1)
    print("===== The server is ready to receive... =====")

    while True:
        conn_socket, addr = server_socket.accept()
        message = conn_socket.recv(BUFF_SIZE).decode()
        method, uri, httpVers = parse_request(message)
        if is_cached(uri):
            print("===== This file has been found in the cache! =====")
            body = get_cached_file(uri)
            conn_socket.send(construct_response(1, 200, body).encode())
            conn_socket.close()
            continue
        host, port, path = parse_uri(uri)
        response = request_from_web_server(method, host, path, port)
        print("===== Response received from server (Writing to cache): =====")
        print(response)

        status_code = parse_status_code(response)
        body = parse_response_body(response)
        if status_code == "200":
            add_to_cache(uri, body)
        conn_socket.send(construct_response(0, status_code, body).encode())
        conn_socket.close()
    server_socket.close()


def parse_status_code(response):
    status_code = response.split('\r\n')[0].split(' ')[1]
    return status_code


def uri_to_key(uri):
    """
    Strips URI of invalid characters in filesystem
    :param uri:
    :return:
    """
    uri = uri.split('://')[1]
    uri = uri.replace('/', '_')
    return uri


def request_from_web_server(method, host, path, port):
    """
    Opens a client socket to the web server and requests using relative URI
    :return:
    """
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((host, port))

    msg = construct_request(method, host, path)
    print("===== Sending the following message from proxy to server: ===== ")
    print(msg)
    client_socket.send(msg.encode())
    response = client_socket.recv(BUFF_SIZE).decode()
    client_socket.close()

    return response


def construct_request(method, host, path):
    """Constructs a request message to the host server

    :param method: HTTP Verb (GET)
    :param host: Host Name
    :param path: Path
    :return: Request Message string
    """
    req = f"{method.upper()} {path} HTTP/1.0\r\n" \
          f"Host: {host}\r\n" \
          f"Connection: close\r\n" \
          f"\r\n"

    return req


def construct_response(cache_hit, status_code, body):
    res = f"HTTP/1.0 {status_code} OK\r\n" \
          f"Cache-Hit: {cache_hit}\r\n" \
          f"{body}" \
          f"\r\n"

    return res


def get_cached_file(uri):
    path = Path(f'./cache/{uri_to_key(uri)}.html')
    return path.read_text()


def add_to_cache(uri, value):
    cache.add(uri)
    filename = uri_to_key(uri) + '.html'
    path = Path(f'./cache/{filename}')
    with path.open(mode='w') as f:
        f.write(value)
    f.close()


def parse_request(msg: str):
    """Parse HTTP message for method, uri, and HTTP Version
    Throws error if invalid data

    :param msg:
    :return: Tuple containing the method, uri, and http version
    """
    method, uri, httpVers = msg.split(' ')

    return method, uri, httpVers


def parse_response_body(msg: str):
    body = msg.split('\r\n\r\n')[1] + '\r\n'
    return body


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
    listen(parse_port())

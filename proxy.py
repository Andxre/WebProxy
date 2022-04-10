# Andre Dasalla
# CPSC 4510
# Project 1 : Web Proxy

import sys
from socket import *
from urllib.parse import urlparse
from pathlib import Path


# Size of message buffer
BUFF_SIZE = 2048


def listen(port: int):
    """Listen for and handle incoming TCP Connections
    """
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(1)
    print("===== The server is ready to receive... =====")

    while True:
        conn_socket, addr = server_socket.accept()
        print("Received a client connection from: ", addr)
        message = conn_socket.recv(BUFF_SIZE).decode()
        print("Client message is: ", message)

        try:
            method, uri = parse_request(message)
            host, port, path = parse_uri(uri)
        except ValueError:
            print("===== An Error has occurred while parsing the client's request... Closing socket! =====")
            conn_socket.send(construct_response(0, 500, "Internal Server Error").encode())
            conn_socket.close()
            continue

        if is_cached(uri):
            print("===== This file has been found in the cache! =====")
            body = get_cached_file(uri)
            conn_socket.send(construct_response(1, 200, body).encode())
        else:
            response = request_from_web_server(method, host, path, port)
            print("===== Response received from server: =====")
            print(response)
            status_code = parse_status_code(response)
            body = parse_response_body(response)

            if status_code == "200":
                print("===== Status Code is 200 (Writing to cache) =====")
                add_to_cache(uri, body)
            elif status_code == "404":
                print("===== Status Code is 404 (not writing to cache) =====")
            elif status_code != "404":
                print("===== Status Code is not 200 or 404 (returning error response) =====")
                status_code = "500"
                body = "Internal Server Error"

            conn_socket.send(construct_response(0, status_code, body).encode())
        print("===== Response has been sent to client! Closing socket... =====")
        conn_socket.close()
    server_socket.close()


def request_from_web_server(method, host, path, port):
    """
    Opens a client socket to the web server and makes a request using the relative URI
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
    """Constructs a request message to the web server """
    req = f"{method.upper()} {path} HTTP/1.0\r\n" \
          f"Host: {host}\r\n" \
          f"Connection: close\r\n" \
          f"\r\n"

    return req


def construct_response(cache_hit, status_code, body):
    """Constructs  a response message to the client"""
    res = f"HTTP/1.0 {status_code} OK\r\n" \
          f"Cache-Hit: {cache_hit}\r\n" \
          f"{body}" \
          f"\r\n"

    return res


def uri_to_key(uri):
    """
    Encode URI to a valid filename
    """
    uri = uri.split('://')[1]
    uri = uri.replace('/', '_')
    return uri


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


def parse_status_code(response):
    status_code = response.split('\r\n')[0].split(' ')[1]
    return status_code


def parse_request(msg: str):
    """Parse HTTP message for method, uri. Validates method and http version"""
    method, uri, http_vers = msg.split(' ')
    if method != "GET":
        raise ValueError("Only GET is supported.")
    if http_vers.strip() != "HTTP/1.0":
        raise ValueError("Only HTTP/1.0 is supported.")
    return method, uri


def parse_response_body(msg: str):
    body = msg.split('\r\n\r\n')[1] + '\r\n'
    return body


def parse_uri(uri: str):
    """Parse URI into host, port, and path"""
    if "http" not in uri and "https" not in uri:
        raise ValueError("URI must be in absolute form")
    parsed_url = urlparse(uri)
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 80
    path = parsed_url.path if parsed_url.path else '/'

    return host, port, path


def is_cached(uri: str):
    """Checks cache folder for encoded URI"""
    return Path(f'./cache/{uri_to_key(uri)}.html').exists()


def get_cached_file(uri):
    path = Path(f'./cache/{uri_to_key(uri)}.html')
    return path.read_text()


def add_to_cache(uri, value):
    filename = uri_to_key(uri) + '.html'
    path = Path(f'./cache/{filename}')
    with path.open(mode='w', encoding='utf-8') as f:
        f.write(value)
    f.close()


def init_cache():
    """Initialize cache, if folder doesn't exist"""
    path = Path('./cache')
    if not path.exists():
        path.mkdir()


if __name__ == '__main__':
    init_cache()
    listen(parse_port())

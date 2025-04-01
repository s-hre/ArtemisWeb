import socket
import threading
import select
import urllib.parse

def handle_client(client_socket):
    """Handles client requests and forwards them to the remote server."""
    try:
        request = client_socket.recv(4096).decode()
        if not request:
            return

        # Parse the request to get the host and port
        try:
          lines = request.split('\n')
          url_line = lines[0].split(' ')
          url = url_line[1]
          url_parsed = urllib.parse.urlparse(url)
          host = url_parsed.hostname
          port = url_parsed.port if url_parsed.port else 80 # default to 80
          if url_parsed.scheme == 'https':
              port = 443
          path = url_parsed.path
          query = url_parsed.query

          #Reconstruct the request if needed.
          if url_parsed.scheme:
              request = url_line[0] + " " + path + "?" + query + " " + url_line[2] + "\r\n" + "\r\n".join(lines[1:])

        except Exception as e:
            print(f"Error parsing request: {e}")
            client_socket.close()
            return

        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, port))

            if url_parsed.scheme == 'https':
                client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n") # For HTTPS connect
                sockets = [client_socket, remote_socket]
                while True:
                    readable, _, exceptional = select.select(sockets, [], sockets)

                    if exceptional:
                        break

                    for sock in readable:
                        data = sock.recv(4096)
                        if not data:
                            break

                        if sock is client_socket:
                            remote_socket.sendall(data)
                        else:
                            client_socket.sendall(data)

            else:
                remote_socket.sendall(request.encode())
                while True:
                    data = remote_socket.recv(4096)
                    if not data:
                        break
                    client_socket.sendall(data)

        except Exception as e:
            print(f"Error connecting to remote server: {e}")

        finally:
            remote_socket.close()

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def proxy_server(host, port):
    """Listens for client connections and starts threads to handle them."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Proxy server listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8080
    proxy_server(host, port)

import socket
import threading
import select
import os

def handle_client(client_socket, remote_host, remote_port):
    """Handles data transfer between the client and remote server."""
    try:
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((remote_host, remote_port))

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

    except Exception as e:
        print(f"Error handling client: {e}")

    finally:
        client_socket.close()
        if 'remote_socket' in locals():
            remote_socket.close()

def vpn_server(local_host, local_port, remote_host, remote_port):
    """Listens for client connections and starts threads to handle them."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows reuse of local address
    server_socket.bind((local_host, local_port))
    server_socket.listen(5)

    print(f"VPN server listening on {local_host}:{local_port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, remote_host, remote_port))
            client_thread.start()

    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    local_host = "127.0.0.1"  # Local address to listen on
    local_port = 8080       # Local port to listen on
    remote_host = "www.google.com" # Remote server to connect to
    remote_port = 80          # Remote port to connect to

    vpn_server(local_host, local_port, remote_host, remote_port)

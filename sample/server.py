import socket
from time import sleep

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

print("Starting server...")
# Create a TCP/IP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print("Creating socket...")
    s.bind((HOST, PORT))
    print("Binding socket...")
    s.listen()
    print("Listening for connections...")
    conn, addr = s.accept()
    print("Connection accepted.")
    # Wait for a connection
    with conn:
        print(f"Connected by {addr}")
        for i in range(10):
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)

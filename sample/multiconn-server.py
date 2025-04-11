import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

print("Starting server...")
# Create a TCP/IP socket

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Creating socket...")
        s.bind((HOST, PORT))
        print("Binding socket...")
        s.listen()
        print("Listening for connections...")

        # Set the socket to non-blocking mode
        s.setblocking(False)

        # Register the socket with the selector
        sel.register(s, selectors.EVENT_READ, data=None)

        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    # Accept the connection
                    conn, addr = key.fileobj.accept()
                    print(f"Connection accepted from {addr}")
                    conn.setblocking(False)
                    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
                    events = selectors.EVENT_READ | selectors.EVENT_WRITE
                    sel.register(conn, events, data=data)
                else:
                    # Handle the connection
                    sock = key.fileobj
                    data = key.data
                    if mask & selectors.EVENT_READ:
                        recv_data = sock.recv(1024)  # Should be ready to read
                        if recv_data:
                            data.outb += recv_data
                        else:
                            print(f"Closing connection to {data.addr}")
                            sel.unregister(sock)
                            sock.close()
                    if mask & selectors.EVENT_WRITE:
                        if data.outb:
                            print(f"Echoing {data.outb!r} to {data.addr}")
                            sent = sock.send(data.outb)  # Should be ready to write
                            data.outb = data.outb[sent:]
except KeyboardInterrupt:
    print("Server stopped by user")
finally:
    sel.close()
    print("Selector closed")
    sys.exit(0)
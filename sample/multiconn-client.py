import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()
messages = [b"Message 1 from client.", b"Message 2 from client."]

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
NUM_CONNS = 2  # Number of connections to create

server_addr = (HOST, PORT)
for i in range(0, NUM_CONNS):
    connid = i + 1
    print(f"Starting connection {connid} to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=connid,
        msg_total=sum(len(m) for m in messages),
        recv_total=0,
        messages=messages.copy(),
        outb=b"",
    )
    sel.register(sock, events, data=data)

try:
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
                        print(f"Received {recv_data!r} from connection {data.connid}")
                        data.recv_total += len(recv_data)
                    if not recv_data or data.recv_total == data.msg_total:
                        print(f"Closing connection {data.connid}")
                        sel.unregister(sock)
                        sock.close()
                if mask & selectors.EVENT_WRITE:
                    if not data.outb and data.messages:
                        data.outb = data.messages.pop(0)
                    if data.outb:
                        print(f"Sending {data.outb!r} to connection {data.connid}")
                        sent = sock.send(data.outb)  # Should be ready to write
                        data.outb = data.outb[sent:]
except KeyboardInterrupt:
    print("Server stopped by user")
finally:
    sel.close()
    print("Selector closed")
    sys.exit(0)
#!/usr/bin/env python3

import socket
import sys
import time

from cps_client import slipp

HOST, PORT = "localhost", 8372

PACKETS = [
    slipp.Packet("LSCMD", contents={"args": []}),
    slipp.Packet("read_all_servo_positions"),
    slipp.Packet("read_all"),
    slipp.Packet("read_accel"),
]
for i, p in enumerate(PACKETS):
    p.seq = str(i)

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))

    retdata = b""
    for outpkt in PACKETS:
        print("Sending packet:", str(outpkt))
        sock.sendall(bytes(outpkt))

        inpkt = None
        while inpkt is None:
            retdata += sock.recv(4096)
            (inpkt, msg, retdata) = slipp.Packet.decode(retdata)
            if inpkt is None and msg is not None:
                print(msg)
                break

        if inpkt is not None:
            print("Received packet:", str(inpkt))
        time.sleep(3.0)

    sock.sendall(bytes(slipp.Packet("BYE")))

print("Done")

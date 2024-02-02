#!/usr/bin/env python3

import socket
import socketserver

from . import slipp
from .controllers.spider import SpiderController

CONNECTED_HOSTS = {
    "hosts": set()
}

class SpiderTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        this_host = f"[{self.client_address[0]}:{self.client_address[1]}]"
        CONNECTED_HOSTS["hosts"].add(this_host)

        controller = SpiderController()

        def logprint(*msgs, **kwargs):
            print(this_host, *msgs, **kwargs)

        # set a timeout value of 1 second, allow for at most 30 seconds without
        # any communication
        self.request.settimeout(1.0)
        N_MAX_TIMEOUTS = 30

        timeout_count = 0

        active = True
        data = b""
        while active:
            try:
                recv_data = self.request.recv(1024)
                data += recv_data
            except (TimeoutError, socket.timeout):
                timeout_count += 1
            else:
                timeout_count = 0
            if timeout_count >= N_MAX_TIMEOUTS:
                logprint(f"Did not get any data for {N_MAX_TIMEOUTS} seconds")
                active = False
            if timeout_count != 0:
                continue

            (inpkt, msg, data) = slipp.Packet.decode(data)
            outpkt = None

            if inpkt is None:
                if msg is not None:
                    logprint("Invalid packet:", msg)
                    outpkt = slipp.Packet("NAK")
            else:
                logprint("Received packet:", inpkt)
                # Special cases
                if inpkt.op == "BYE":
                    active = False
                elif inpkt.op == "PING":
                    outpkt = slipp.Packet("PONG", seq=inpkt.seq)
                else:
                    outpkt = controller.handle_incoming_packet(inpkt)

            if outpkt is not None:
                self.request.sendall(bytes(outpkt))

        CONNECTED_HOSTS["hosts"].remove(this_host)
        logprint("Done, terminating connection")


def run_spider(host="0.0.0.0", port=8372):
    print(f"Running server at {host}:{port}")
    with socketserver.ThreadingTCPServer((host, port), SpiderTCPHandler) as server:
        server.serve_forever()

#!/usr/bin/env python3

import signal
import socket
import socketserver

from . import slipp
from .controllers.spider import SpiderController


PREV_HANDLERS = dict()

def sighandler(sig, frame):
    print(f"Received signal \"{signal.strsignal(sig)}\" ({sig})", flush=True)
    return PREV_HANDLERS[sig](sig, frame)

def track_signal(sig):
    if sig not in PREV_HANDLERS:
        prev_handle = signal.signal(sig, sighandler)
        PREV_HANDLERS[sig] = prev_handle


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
            print(this_host, *msgs, flush=True, **kwargs)

        # set a timeout value of 1 second, allow for at most 30 seconds without
        # any communication
        timeout_s = 0.05
        max_timeout_s = 30.0

        self.request.settimeout(timeout_s)
        N_MAX_TIMEOUTS = int(max_timeout_s/timeout_s)

        timeout_count = 0

        active = True
        data = b""
        while active:
            try:
                recv_data = self.request.recv(2**16)
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

            can_read_packet = True

            while can_read_packet and active:
                prevlen = len(data)
                (inpkt, msg, data) = slipp.Packet.decode(data)
                outpkt = None
                can_read_packet = bool(prevlen != len(data))

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
                    elif inpkt.op == "LSCONN":
                        outpkt = slipp.Packet("CONNS", seq=inpkt.seq, contents={"hosts": list(CONNECTED_HOSTS["hosts"])})
                    else:
                        outpkt = controller.handle_incoming_packet(inpkt)

                if outpkt is not None:
                    self.request.sendall(bytes(outpkt))

        CONNECTED_HOSTS["hosts"].remove(this_host)
        logprint("Done, terminating connection")


def run_spider(host="0.0.0.0", port=8372):
    track_signal(signal.SIGINT)
    track_signal(signal.SIGHUP)
    track_signal(signal.SIGTERM)
    print(f"Running server at {host}:{port}", flush=True)
    with socketserver.TCPServer((host, port), SpiderTCPHandler) as server:
        server.serve_forever()

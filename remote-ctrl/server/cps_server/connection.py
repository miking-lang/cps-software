#!/usr/bin/env python3

import signal
import socket
import socketserver
import traceback

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
        TIMEOUT_S = 0.05
        MAX_TIMEOUT_S = 30.0

        self.request.settimeout(TIMEOUT_S)
        N_MAX_TIMEOUTS = int(MAX_TIMEOUT_S/TIMEOUT_S)

        timeout_count = 0

        active = True
        data = b""
        while active:
            timed_out = False
            try:
                recv_data = self.request.recv(2**16)
                data += recv_data
            except (TimeoutError, socket.timeout):
                timeout_count += 1
                timed_out = True
            if timeout_count >= N_MAX_TIMEOUTS:
                logprint(f"Did not get any packets for {MAX_TIMEOUT_S} seconds")
                active = False
            if timed_out:
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
                        outpkt = slipp.Packet("NAK", contents={"errmsg": "invalid packet"})
                        #outpkt = slipp.NAK(None, errmsg="invalid packet")
                    # else: received incomplete data
                else:
                    timeout_count = 0
                    logprint("Received packet:", inpkt)
                    # Special cases
                    if inpkt.op == "BYE":
                        active = False
                    elif inpkt.op == "PING":
                        outpkt = slipp.Packet("PONG", seq=inpkt.seq)
                    elif inpkt.op == "LSCONN":
                        outpkt = slipp.Packet("CONNS", seq=inpkt.seq, contents={"hosts": list(CONNECTED_HOSTS["hosts"])})
                    else:
                        try:
                            outpkt = controller.handle_incoming_packet(inpkt)
                        except Exception as e:
                            #outpkt = slipp.Packet("NAK", seq=inpkt.seq, contents={"errmsg": "internal error, see server logs"})
                            outpkt = slipp.NAK(inpkt, errmsg="internal error, see server logs")

                if outpkt is not None:
                    self.request.sendall(outpkt.encode())

        CONNECTED_HOSTS["hosts"].remove(this_host)
        logprint("Done, terminating connection")


def run_spider(host="0.0.0.0", port=8372):
    track_signal(signal.SIGINT)
    track_signal(signal.SIGHUP)
    track_signal(signal.SIGTERM)
    print(f"Running server at {host}:{port}", flush=True)
    with socketserver.TCPServer((host, port), SpiderTCPHandler) as server:
        server.serve_forever()

import socket
import threading

from collections import deque
from typing import Optional, Callable

from .. import slipp

def _run_threaded_client(client):
    client.run()

class ThreadedClientConnection:
    def __init__(self, host, port, logfn):
        """
        The logging function should take a title and a message.
        """
        self.host = host
        self.port = port
        self.logfn = logfn
        self.__active = False
        self.__failed = False
        self.__socket = None
        self.__seq_counter = 0

        self.__thread = threading.Thread(target=_run_threaded_client, args=(self,))
        self.__send_queue = deque()
        self.__send_lock = threading.BoundedSemaphore(value=1)
        self.__dict_lock = threading.BoundedSemaphore(value=1)

        self.__recv_callbacks = dict()

    def start(self):
        self.__thread.start()

    @property
    def is_active(self):
        return self.__active

    def send(self,
             packet : slipp.Packet,
             on_recv_callback : Optional[Callable[[slipp.Packet], None]] = None,
             on_timeout_callback : Optional[Callable[[], None]] = None,
             ttl=5.0):
        """
        Sends a packet, queues it up if socket is not open yet.

        on_recv_callback
          Performs a callback invokation when a response for this packet is
          received.
        ttl : float (positive)
          Time-to-live in seconds, specifies when a packet should be timed out.
        """
        with self.__send_lock:
            packet.seq = str(self.__seq_counter)
            self.__seq_counter += 1

            with self.__dict_lock:
                self.__recv_callbacks[packet.seq] = (on_recv_callback, on_timeout_callback, ttl)

            self.__send_queue.append(packet)
            if self.__active:
                while len(self.__send_queue) > 0:
                    outpkt = self.__send_queue.popleft()
                    try:
                        self._internal_send(self.__socket, outpkt)
                    except Exception as e:
                        self.__active = False

    def stop(self):
        self.__active = False

    def _internal_send(self, sock, packet : slipp.Packet):
        """
        Internal function for sending a packet, handling encoding and
        necessary callbacks, etc.
        """
        self.logfn("Sent Packet", str(packet))
        sock.sendall(bytes(packet))

    def _internal_recv(self, packet : slipp.Packet):
        """
        Internal function called when a packet is received.
        """
        self.logfn("Recieved Packet", str(packet))

        # Protect this part if we are sending at the same time...
        with self.__dict_lock:
            cb_entry = self.__recv_callbacks.get(packet.seq)
            if cb_entry is not None:
                del self.__recv_callbacks[packet.seq]

        if cb_entry is not None:
            cb = cb_entry[0]
            if cb is not None:
                cb(packet)

    def run(self):
        # Create a socket (SOCK_STREAM means a TCP socket)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect((self.host, self.port))
            self.__active = True
            self.__failed = False
            self.__socket = sock

            sock.settimeout(0.1)

            recvdata = b""
            while self.__active and not self.__failed:
                try:
                    d = sock.recv(4096)
                    recvdata += d
                except (TimeoutError, socket.timeout):
                    continue
                except Exception as e:
                    self.__failed = True
                    continue

                (inpkt, msg, recvdata) = slipp.Packet.decode(recvdata)
                if inpkt is None and msg is not None:
                    print(msg)
                    break
                elif inpkt is not None:
                    self._internal_recv(inpkt)

            with self.__send_lock:
                if not self.__failed:
                    try:
                        self._internal_send(sock, slipp.Packet("BYE"))
                    except Exception:
                        pass
                self.__active = False
                self.__socket = None

import socket
import threading

from collections import deque

from .. import slipp

def _run_threaded_client(client):
    client.run()

class ThreadedClientConnection:
    def __init__(self, host, port, on_packet):
        """
        on_packet : slipp.Packet -> ()
        """
        self.host = host
        self.port = port
        self.on_packet = on_packet
        self.__active = False
        self.__socket = None

        self.__thread = threading.Thread(target=_run_threaded_client, args=(self,))
        self.__send_queue = deque()
        self.__send_lock = threading.BoundedSemaphore(value=1)

    def start(self):
        self.__thread.start()

    def send(self, packet : slipp.Packet):
        """Sends a packet, queues it up if socket is not open yet."""
        with self.__send_lock:
            self.__send_queue.append(packet)
            if self.__active:
                while len(self.__send_queue) > 0:
                    outpkt = self.__send_queue.popleft()
                    self.__socket.sendall(bytes(outpkt))

    def stop(self):
        self.__active = False

    def run(self):
        # Create a socket (SOCK_STREAM means a TCP socket)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect((self.host, self.port))
            self.__active = True
            self.__socket = sock

            sock.settimeout(0.1)

            recvdata = b""
            while self.__active:
                try:
                    d = sock.recv(4096)
                    recvdata += d
                except (TimeoutError, socket.timeout):
                    continue

                (inpkt, msg, recvdata) = slipp.Packet.decode(recvdata)
                if inpkt is None and msg is not None:
                    print(msg)
                    break

                self.on_packet(inpkt)

            with self.__send_lock:
                sock.sendall(bytes(slipp.Packet("BYE")))
                self.__active = False
                self.__socket = None



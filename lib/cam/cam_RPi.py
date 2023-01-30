# picamera2 is based on libcamera which is implemented in c++
from picamera2 import Picamera2
import time
import socket

picam2 = Picamera2()
# still_configuration is optimized for taking still pictures that are not necessarily
# going to be previewed
camera_config = picam2.create_still_configuration({"format": "BGR888", "size": (640, 480)})
picam2.configure(camera_config)
picam2.start()

sock = socket.socket()
port = 12351
sock.bind(('', port))
sock.listen(5)
while True:
    # Establish connection with client.
    conn, addr = sock.accept()
    print ('Got connection from', addr )

    while (conn.recv(1)):
        stream = conn.makefile("wb")
        picam2.capture_file(stream, format="png")
        print("file captured")

    # Close the connection with the client
    conn.close()

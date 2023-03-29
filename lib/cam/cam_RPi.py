# picamera2 is based on libcamera which is implemented in c++
from picamera2 import Picamera2
import time
import socket

picam2 = Picamera2()
# still_configuration is optimized for taking still pictures that are not necessarily
# going to be previewed
camera_config = picam2.create_still_configuration({"format": "BGR888", "size": (128, 128)})
picam2.configure(camera_config)
picam2.start()
sock = socket.socket()
port = 12350
sock.bind(('', port))
sock.listen(5)
print("Listening...")
while True:
    # Establish connection with client.
    conn, addr = sock.accept()
    print ('Got connection from', addr )

    command = conn.recv(1)
    while (command):
        print("command: ", command)
        stream = conn.makefile("wb")
        if (command == b'\x01'):
            picam2.capture_file(stream, format="png")
            print("png captured")
        elif (command == b'\x02'):
            picam2.capture_file(stream, format="bmp")
            print("bmp captured")
        command = conn.recv(1)

    # Close the connection with the client
    conn.close()

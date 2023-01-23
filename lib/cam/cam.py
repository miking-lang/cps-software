# TODO: Fix the problem that the image file can be changed in the middle of a reading.
# Maybe extend the file and have some kind of delimiter.

# picamera2 is based on libcamera which is implemented in c++
from picamera2 import Picamera2
import time

# Takes images with as high fps as possible with the Raspberry Pi Camera Module and
# stores them in a specific file.
# Overrides the file with the new image.
def take_pictures(format, size, file_name):
    picam2 = Picamera2()
    # still_configuration is optimized for taking still pictures that are not necessarily
    # going to be previewed
    camera_config = picam2.create_still_configuration({"format": format, "size": size})
    picam2.configure(camera_config)
    picam2.start()
    # Getting the current date and time
    while True:
        picam2.capture_file(file_name)

take_pictures("BGR888", (640, 480), "image_stream23.jpg")
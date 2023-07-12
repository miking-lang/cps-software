from adafruit_servokit import ServoKit
import time

# Initialize the PCA9685, using I2C address 0x40 (default).
kit = ServoKit(channels=16)

# Control the servos.
# Assumes servos are connected to channels 0, 1, 2 and 3.
# Modify as needed for your setup.
# Note that MG90S servos typically operate in the range 0 to 180.



angles = [[120, 80, 70, 115], [0, 180, 180, 0]]
mode = 1

for i in range(5):
    mode = ~mode
    # Set servo at channel 0 to 90 degrees
    kit.servo[12].angle = angles[mode][0]

    # Set servo at channel 1 to 90 degrees
    kit.servo[13].angle = angles[mode][1]

    # Set servo at channel 2 to 90 degrees
    kit.servo[14].angle = angles[mode][2]

    # Set servo at channel 3 to 90 degrees
    kit.servo[15].angle = angles[mode][3]

    time.sleep(1)

# Then, to "turn off" the servos (make them go limp):
kit.servo[12].fraction = None
kit.servo[13].fraction = None
kit.servo[14].fraction = None
kit.servo[15].fraction = None
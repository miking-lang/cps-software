from adafruit_servokit import ServoKit

# Initialize the PCA9685
kit = ServoKit(channels=16)

# Control the servos.
# This code assumes servos are connected to channels 0, 1, 2, and 3.
# Set servos to 90 degrees
kit.servo[0].angle = 90
kit.servo[1].angle = 90
kit.servo[2].angle = 90
kit.servo[3].angle = 90

# Then, to "turn off" the servos (make them go limp):
kit.servo[0].fraction = None
kit.servo[1].fraction = None
kit.servo[2].fraction = None
kit.servo[3].fraction = None
from humanoid import Humanoid
import time

humanoid = Humanoid()

humanoid.sit()

voltages = humanoid.dynamixel_handler.read_servo_voltages(list(range(4, 24)))
print("Voltages: ", voltages)

command = input("Press any key to disable torque")

humanoid.disable_torques()
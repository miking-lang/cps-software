from humanoid import Humanoid
import time

humanoid = Humanoid()

print("Starting in 3 seconds...")
print()
for i in range(3):
    print(3 - i)
    time.sleep(1)

humanoid.stand()

voltages = humanoid.dynamixel_handler.read_servo_voltages([1, 2, 3, 20])
print("Voltages: ", voltages)

command = input("Press any key to disable torque")

humanoid.disable_torques()
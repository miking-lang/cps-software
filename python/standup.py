from helper_functions import *
import threading
import json

BR_INNER_SHOULDER = 1
BR_OUTER_SHOULDER = 2
FR_ELBOW = 3
FR_INNER_SHOULDER = 4
BR_ELBOW = 5
FR_OUTER_SHOULDER = 6
BL_OUTER_SHOULDER = 7
FL_INNER_SHOULDER = 8
BL_INNER_SHOULDER = 9
FL_ELBOW = 10
FL_OUTER_SHOULDER = 11
BL_ELBOW = 12

motor_dict = {
    1 : "BR_INNER_SHOULDER",
    2 : "BR_OUTER_SHOULDER",
    3 : "FR_ELBOW",
    4 : "FR_INNER_SHOULDER",
    5 : "BR_ELBOW",
    6 : "FR_OUTER_SHOULDER",
    7 : "BL_OUTER_SHOULDER",
    8 : "FL_INNER_SHOULDER",
    9 : "BL_INNER_SHOULDER",
    10 : "FL_ELBOW",
    11 : "FL_OUTER_SHOULDER",
    12 : "BL_ELBOW"
}

back_right_ids = [BR_INNER_SHOULDER, BR_OUTER_SHOULDER, BR_ELBOW]
front_right_ids = [FR_INNER_SHOULDER, FR_OUTER_SHOULDER, FR_ELBOW]
back_left_ids = [BL_INNER_SHOULDER, BL_OUTER_SHOULDER, BL_ELBOW]
front_left_ids = [FL_INNER_SHOULDER, FL_OUTER_SHOULDER, FL_ELBOW]
all_ids = back_right_ids + back_left_ids + front_right_ids + front_left_ids

dynamixel_handler = DynamixelHandler()
trajectory = []

# Contains tuples of (time command was sent, commanded position, duration)
motor_commands_history = [[] for _ in range(13)]

# Contains tuples (time stamp, position)
motor_positions_history = [[] for _ in range(13)]

print(dynamixel_handler.read_servo_positions(all_ids))

pos_1 = [2270, 1333, 795, 1729, 1159, 3797, 1746, 1132, 3635, 2329, 1052, 516]
pos_2 = [2205, 1964, 1007, 1782, 1867, 3320, 1855, 1909, 3278, 2367, 1763, 905]
pos_3 = [2313, 1357, 821, 1711, 1462, 3360, 1723, 1343, 3348, 2362, 1315, 831]
pos_4 = [2314, 1357, 821, 1711, 1462, 3360, 1723, 1344, 3348, 2362, 1316, 831]

positions = [pos_1, pos_2, pos_3, pos_4]

duration = 1000

finished = False

mutex = threading.Lock()

def read_motors():
    freq = 100

    while not finished:
        start_time = time.time()

        with mutex:
            start_read_time = time.time()
            positions = dynamixel_handler.read_servo_positions(all_ids)
            end_read_time = time.time()

        # Takes around 6ms to read motors. Take time stamp as the average between start and end of reading. 
        time_stamp = (end_read_time+start_read_time)/2
        for i in range(12):
            motor_positions_history[i+1].append((time_stamp, positions[i]))

        while time.time() - start_time < 1/freq:
            pass

read_motors_thread = threading.Thread(target=read_motors)
read_motors_thread.start()

for pos in positions:
    with mutex: 
        current_time = time.time()
        dynamixel_handler.move_many_servos(all_ids, pos, [duration]*12)
    for id in all_ids:
        motor_commands_history[id].append((current_time, pos[id-1], duration))
    time.sleep(duration/1000)

finished = True
read_motors_thread.join()

motor_data = {}
for i in range(12):
    motor_data[motor_dict[i+1]] = {
        "Position History": motor_positions_history[i+1],
        "Command History": motor_commands_history[i+1]
    }

with open('standup_data.json', 'w') as file:
    json.dump(motor_data, file, indent=4)
from humanoid import Humanoid

id_to_name = {
    1 : "neck_y",
    2 : "neck_x",
    3 : "neck_z",
    4 : "r_shoulder_y",
    5 : "r_shoulder_x",
    6 : "r_shoulder_z",
    7 : "r_elbow",
    8 : "l_shoulder_y",
    9 : "l_shoulder_x",
    10 : "l_shoulder_z",
    11 : "l_elbow",
    12 : "torso_z",
    13 : "torso_y",
    14 : "torso_x",
    15 : "r_hip_x",
    16 : "r_hip_z",
    17 : "r_hip_y",
    18 : "r_knee",
    19 : "r_foot",
    20 : "l_hip_x",
    21 : "l_hip_z",
    22 : "l_hip_y",
    23 : "l_knee",
    24 : "l_foot"
}

servo_positions = []

humanoid = Humanoid()

while 1:
    command = input()

    if command == 'q':
        break
    else:
        positions = humanoid.read_all_servos()

for id, position in enumerate(positions):
    print(f"pos[{id_to_name[id].upper()}] = {position}")
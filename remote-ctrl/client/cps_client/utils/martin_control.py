
import numpy as np

Lc = 0.0705  # Coxa length
Lf = 0.140125  # Femur length
Lt = 0.1805  # Tibia length

# Interraction rate in Hz
TROT_HZ = 800
CREEP_HZ = 150

def move_leg(leg, current_position, goal_position, num):
    position_trajectory = [
        list(np.linspace(current_position[i], goal_position[i], num)) for i in range(3)
    ]
    joint_trajectory = [0] * num
    for i in range(num):
        joint_trajectory[i] = position_function(
            [
                position_trajectory[0][i],
                position_trajectory[1][i],
                position_trajectory[2][i],
            ]
        )
    if "left" in leg:
        joint_trajectory = [[-x[0], x[1], x[2]] for x in joint_trajectory]
    return joint_trajectory


def combine_movements(x, z_movement_old, forward_movement_old):
    z_movement = []
    forward_movement = []

    for i in range(len(z_movement_old)):
        z_movement.append([z_movement_old[i][0], z_movement_old[i][1]])
    for i in range(len(forward_movement_old)):
        forward_movement.append(
            [forward_movement_old[i][0], forward_movement_old[i][1]]
        )

    res = []
    i = 1
    j = 1
    while i < len(z_movement) and j < len(forward_movement):
        if z_movement[i][0] == forward_movement[j][0]:
            res.append(
                (z_movement[i][0], [x, forward_movement[j][1], z_movement[i][1]])
            )
            return res
        elif z_movement[i][0] < forward_movement[j][0]:
            res.append(
                (
                    z_movement[i][0],
                    [
                        x,
                        forward_movement[j - 1][1]
                        + z_movement[i][0]
                        / forward_movement[j][0]
                        * (forward_movement[j][1] - forward_movement[j - 1][1]),
                        z_movement[i][1],
                    ],
                )
            )
            forward_movement[j][0] -= z_movement[i][0]
            i += 1
        elif forward_movement[j][0] < z_movement[i][0]:
            res.append(
                (
                    forward_movement[j][0],
                    [
                        x,
                        forward_movement[j][1],
                        z_movement[i - 1][1]
                        + forward_movement[j][0]
                        / z_movement[i][0]
                        * (z_movement[i][1] - z_movement[i - 1][1]),
                    ],
                )
            )
            z_movement[i][0] -= forward_movement[j][0]
            j += 1

    while i < len(z_movement):
        res.append(
            (z_movement[i][0], [x, forward_movement[j - 1][1], z_movement[i][1]])
        )
        i += 1

    while j < len(forward_movement):
        res.append(
            (forward_movement[j][0], [x, forward_movement[j][1], z_movement[i - 1][1]])
        )
        j += 1

    return res


def trot_gait():
    x = 1.1 * (Lc + Lf + Lt) / 3

    y_offset = 0.1
    y_base = 0.01
    y_range = 0.1

    front_y0 = y_base + y_offset - y_range
    front_y = y_base + y_offset
    back_y0 = -y_base - y_offset
    back_y = -y_base + y_range - y_offset
    z0 = 0.07
    z = 0.06

    factor = 2

    z_up = [[0, z0], [10 * factor, z], [80 * factor, z], [10 * factor, z0]]
    z_nothing = [[0, z0], [100 * factor, z0]]

    full_forward_front = [[0, front_y0], [100 * factor, front_y]]
    full_forward_back = [[0, back_y0], [100 * factor, back_y]]

    full_backward_front = [[0, front_y], [100 * factor, front_y0]]
    full_backward_back = [[0, back_y], [100 * factor, back_y0]]

    phase_1 = {
        "front_right": combine_movements(x, z_nothing, full_backward_front),
        "back_right": combine_movements(x, z_up, full_forward_back),
        "front_left": combine_movements(x, z_up, full_forward_front),
        "back_left": combine_movements(x, z_nothing, full_backward_back),
    }

    phase_2 = {
        "front_right": combine_movements(x, z_up, full_forward_front),
        "back_right": combine_movements(x, z_nothing, full_backward_back),
        "front_left": combine_movements(x, z_nothing, full_backward_front),
        "back_left": combine_movements(x, z_up, full_forward_back),
    }

    joint_trajectories = {
        "front_right": [],
        "back_right": [],
        "front_left": [],
        "back_left": [],
    }

    current_positions = {
        "front_right": [x, front_y, z0],
        "back_right": [x, back_y0, z0],
        "front_left": [x, front_y0, z0],
        "back_left": [x, back_y, z0],
    }

    movement_strings = {
        "back_right": phase_1["back_right"] + phase_2["back_right"],
        "back_left": phase_1["back_left"] + phase_2["back_left"],
        "front_right": phase_1["front_right"] + phase_2["front_right"],
        "front_left": phase_1["front_left"] + phase_2["front_left"],
    }

    for leg, movements in movement_strings.items():
        for movement in movements:
            joint_trajectories[leg].extend(
                move_leg(leg, current_positions[leg], movement[1], movement[0])
            )
            current_positions[leg] = movement[1]

    return (
        joint_trajectories["back_right"],
        joint_trajectories["back_left"],
        joint_trajectories["front_right"],
        joint_trajectories["front_left"],
    )


def creep_gait():
    x = 1.4 * (Lc + Lf + Lt) / 3

    front_y0 = -0.05
    front_y = 0.05
    back_y0 = -0.04
    back_y = 0.05
    z0 = 0.1
    z = 0.07

    factor = 3

    z_up = [[0, z0], [10 * factor, z0], [15 * factor, z], [50 * factor, z], [25 * factor, z0]]
    z_nothing = [[0, z0], [100 * factor, z0]]

    forward_1_front = [[0, front_y0], [100 * factor, front_y0]]
    forward_2_front = [[0, front_y0], [100 * factor, front_y]]
    forward_3_front = [[0, front_y], [33 * factor, front_y], [67 * factor, 0.5 * front_y]]
    forward_4_front = [[0, 0.5 * front_y], [100 * factor, front_y0]]

    forward_1_back = [[0, 1 / 3 * back_y], [100 * factor, back_y0]]
    forward_2_back = [[0, back_y0], [33 * factor, back_y0], [67 * factor, back_y]]
    forward_3_back = [[0, back_y], [33 * factor, back_y], [67 * factor, 2 / 3 * back_y]]
    forward_4_back = [[0, 2 / 3 * back_y], [100 * factor, 1 / 3 * back_y]]

    phase_1 = {
        'front_right': combine_movements(x, z_nothing, forward_1_front),
        'back_right': combine_movements(x, z_up, forward_2_back),
        'front_left': combine_movements(x, z_nothing, forward_3_front),
        'back_left': combine_movements(x, z_nothing, forward_4_back)
    }

    phase_2 = {
        'front_right': combine_movements(x, z_up, forward_2_front),
        'back_right': combine_movements(x, z_nothing, forward_3_back),
        'front_left': combine_movements(x, z_nothing, forward_4_front),
        'back_left': combine_movements(x, z_nothing, forward_1_back)
    }

    phase_3 = {
        'front_right': combine_movements(x, z_nothing, forward_3_front),
        'back_right': combine_movements(x, z_nothing, forward_4_back),
        'front_left': combine_movements(x, z_nothing, forward_1_front),
        'back_left': combine_movements(x, z_up, forward_2_back)
    }

    phase_4 = {
        'front_right': combine_movements(x, z_nothing, forward_4_front),
        'back_right': combine_movements(x, z_nothing, forward_1_back),
        'front_left': combine_movements(x, z_up, forward_2_front),
        'back_left': combine_movements(x, z_nothing, forward_3_back)
    }

    joint_trajectories = {
        'front_right': [],
        'back_right': [],
        'front_left': [],
        'back_left': []
    }

    current_positions = {
        'front_right': [x, front_y0, z0],
        'back_right': [x, front_y0, z0],
        'front_left': [x, front_y, z0],
        'back_left': [x, 2 / 3 * front_y, z0]
    }

    movement_strings = {
        'back_right': phase_1['back_right'] + phase_2['back_right'] + phase_3['back_right'] + phase_4['back_right'],
        'back_left': phase_1['back_left'] + phase_2['back_left'] + phase_3['back_left'] + phase_4['back_left'],
        'front_right': phase_1['front_right'] + phase_2['front_right'] + phase_3['front_right'] + phase_4[
            'front_right'],
        'front_left': phase_1['front_left'] + phase_2['front_left'] + phase_3['front_left'] + phase_4['front_left']
    }

    for leg, movements in movement_strings.items():
        for movement in movements:
            joint_trajectories[leg].extend(move_leg(leg, current_positions[leg], movement[1], movement[0]))
            current_positions[leg] = movement[1]

    return joint_trajectories['back_right'], joint_trajectories['back_left'], joint_trajectories['front_right'], \
    joint_trajectories['front_left']


def position_function(position):
    x, y, z = position
    Lc = 0.0705  # Coxa length
    Lf = 0.140125  # Femur length
    Lt = 0.1805  # Tibia length
    R = x - Lc
    theta_0 = np.arctan2(y, x)
    cos_arg = np.clip((R ** 2 + z ** 2 - Lf ** 2 - Lt ** 2) / (2 * Lf * Lt), -1, 1)
    theta_2 = np.arccos(cos_arg)
    theta_1 = np.arctan2(z, R) - np.arctan2(
        Lt * np.sin(theta_2), Lf + Lt * np.cos(-theta_2)
    )
    return [theta_0, -theta_1, theta_2]


from abc import ABC, abstractmethod

from math import pi
import numpy as np
import time
from numpy.linalg import norm
import traceback
from datetime import datetime
import pathlib
import json

zero_shift_dics = {
    "BR_INNER_SHOULDER": 0.0,
    "BR_OUTER_SHOULDER": -0.308,
    "BR_ELBOW": -0.211,
    "FR_INNER_SHOULDER": 0.0,
    "FR_OUTER_SHOULDER": -0.308,
    "FR_ELBOW": -0.231,
    "FL_INNER_SHOULDER": 0.0,
    "FL_OUTER_SHOULDER": -0.298,
    "FL_ELBOW": -0.191,
    "BL_INNER_SHOULDER": 0.0,
    "BL_OUTER_SHOULDER": -0.308,
    "BL_ELBOW": -0.231,
    "NO_KEY": 0.0,
}

POSITIVE_JOINTS = {
    "FR_ELBOW",
    "BL_ELBOW",
}

FIXED_ANGLE = None
# FIXED_ANGLE = 98.0

def dnx_to_mujoco(angle, motor_key):
    if motor_key in POSITIVE_JOINTS:
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        return float((angle-2048)*pi*0.087891/180 + zero_shift_dics[motor_key])
    else:
        return float((2048-angle)*pi*0.087891/180 + zero_shift_dics[motor_key])

def mujoco_to_dnx(angle, motor_key):
    if motor_key in POSITIVE_JOINTS:
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        v = int(2048 + round(180*(angle-zero_shift_dics[motor_key])/(pi*0.087891)))
    else:
        v = int(2048 - round(180*(angle-zero_shift_dics[motor_key])/(pi*0.087891)))

    while v < 0:
        v += 4096
    while v >= 4096:
        v -= 4096

    return v

def dnxvel_to_mujoco(vel, motor_key):
    if motor_key in POSITIVE_JOINTS:
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        return vel*6*0.229*pi/180
        # 1 mujoco unit = 0.229 rpm = 0.229*360 deg per minute = 0.229*360/60 = 0.229*6 deg/s = 0.229*6*pi/180 rad/s
    else:
        return -vel*6*0.229*pi/180
        # 1 mujoco unit = 0.229 rpm = 0.229*360 deg per minute = 0.229*360/60 = 0.229*6 deg/s = 0.229*6*pi/180 rad/s



class SensorReader(ABC):
    @property
    @abstractmethod
    def output_size(self):
        """Returns the size of the output array for this reader"""
        pass

    @abstractmethod
    def read(self, *args, **kwargs):
        """Returns an 1d array like object with the sensor readings"""
        pass

    @abstractmethod
    def step(self, dt):
        """Some readers needs to keep an internal state. This function is called
        once for each time-step in the environment, where `dt` is the size of the
        time-step."""
        pass

    @abstractmethod
    def reset(self):
        """Resets the sensor reader"""
        pass


class NoFilter(SensorReader):
    def __init__(self, data):
        self._data = data

    @property
    def output_size(self):
        return len(self._data)

    def read(self):
        return self._data.copy()

    def step(self, dt):
        pass

    def reset(self):
        pass


class AccelerometerFilter(SensorReader):
    def __init__(self, data):
        self._data = data

    @property
    def output_size(self):
        return len(self._data)

    def read(self):
        # transform to robot body coordinate
        return np.array([self._data[1], self._data[0], self._data[2]]) / 9.81

    def step(self, dt):
        pass

    def reset(self):
        pass


class GyroscopeFilter(SensorReader):
    def _transform_gyro_data(data):
        # transform to robot body coordinate
        return np.array([-data[1], -data[0], -data[2]])

    def _Rx(a):
        return np.array([
            [1, 0, 0],
            [0, np.cos(np.radians(a)), -np.sin(np.radians(a))],
            [0, np.sin(np.radians(a)), np.cos(np.radians(a))]
        ])

    def _Ry(a):
        return np.array([
            [np.cos(np.radians(a)), 0, np.sin(np.radians(a))],
            [0, 1, 0],
            [-np.sin(np.radians(a)), 0, np.cos(np.radians(a))]
        ])

    def _Rz(a):
        return np.array([
            [np.cos(np.radians(a)), -np.sin(np.radians(a)), 0],
            [np.sin(np.radians(a)), np.cos(np.radians(a)), 0],
            [0, 0, 1]
        ])

    # Higher s means more adapted to accelerometer data
    def _interpolate_orientation(Rg, a, s):
        aw = Rg@a
        cross = np.cross(aw,np.array([0,0,-1]))
        n = cross/norm(cross)
        theta = np.arcsin(norm(cross)/norm(aw))
        mat = np.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
        new_R = (np.eye(3) + np.sin(s*theta)*mat + (1-np.cos(s*theta))*mat@mat)@Rg
        return new_R

    def _IMU_sim(R, gyro, acc, dt):
        deltas = [val*dt for val in gyro]
        newR = (
            R
            @GyroscopeFilter._Rz(deltas[2])
            @GyroscopeFilter._Ry(deltas[1])
            @GyroscopeFilter._Rx(deltas[0])
        )
        newR = GyroscopeFilter._interpolate_orientation(newR, acc, 0.2)
        return newR

    _R = np.array([
            [0, -1, 0],
            [-1, 0, 0],
            [0, 0, -1]
    ], dtype=np.float64)

    def __init__(self, gyro_data, accel_data):
        self._accelerometer_filter = AccelerometerFilter(accel_data)
        self._gyro_data = gyro_data
        # Rotation matrix of the gyroscope. The assumption here is that the
        # simulation starts with the body level.
        self._R = GyroscopeFilter._R

    @property
    def output_size(self):
        return len(self._R.flatten())

    def step(self, dt):
        self._accelerometer_filter.step(dt)
        accel_data = self._accelerometer_filter.read()
        gyro_data = GyroscopeFilter._transform_gyro_data(self._gyro_data)
        self._R = GyroscopeFilter._IMU_sim(self._R, gyro_data, accel_data, dt)

    def read(self):
        return self._R.copy().flatten()

    def reset(self):
        self._R = GyroscopeFilter._R



def get_obs(ctrl : "SpiderController", state):
    # Gets an observation in the MuJoCo format
    src_accel = ctrl.read_accel()
    src_gyro = ctrl.read_gyro()
    spider_data = ctrl.read_all_servos_RAM()

    mj_accel = np.array([src_accel[1], src_accel[0], src_accel[2]]) * (9.81 / 2.0)
    mj_gyro = np.array([-src_gyro[1], -src_gyro[0], -src_gyro[2]])

    if state["gyro"] is None:
        state["gyro"] = GyroscopeFilter(mj_gyro, mj_accel)
    else:
        state["gyro"]._gyro_data = mj_gyro
        state["gyro"]._accelerometer_filter._data = mj_accel
        state["gyro"].step(dt=0.25)

    fl_gyro = state["gyro"].read()
    fl_accel = state["gyro"]._accelerometer_filter.read()
    assert fl_gyro.shape == (9,)
    assert fl_accel.shape == (3,)

    src_positions = spider_data["PRESENT_POSITION"]
    src_velocity = spider_data["PRESENT_VELOCITY"]

    SERVO_ORDER = ctrl.get_servos()

    mj_positions = np.zeros((12,))
    for i in range(12):
        mj_positions[i] = dnx_to_mujoco(src_positions[i], SERVO_ORDER[i])
        hwstat = spider_data["HARDWARE_ERROR_STATUS"][i]
        if hwstat != 0:
            add_info(state, f"Hardware error 0x{hwstat:02x} on servo {SERVO_ORDER[i]}")

    if state["velocity"] is None:
        state["velocity"] = np.zeros((12,))
        state["last_position"] = mj_positions
    else:
        state["velocity"] = (mj_positions - state["last_position"]) / 0.25
        state["last_position"] = mj_positions

    #mj_velocity = state["velocity"]
    mj_velocity = np.array([dnxvel_to_mujoco(src_velocity[i], SERVO_ORDER[i]) for i in range(12)])

    mj_servos = np.concatenate(tuple(zip(mj_positions,mj_velocity)))
    assert mj_servos.shape == (24,)

    #mujoco_obs = np.concatenate((fl_accel, fl_gyro, mj_servos))
    mujoco_obs = mj_servos

    add_to_trajectory(state, "observation", {"mujoco": mujoco_obs.tolist(), "raw": spider_data})

    return mujoco_obs

def apply_action(ctrl : "SpiderController", action, state):
    # Applies an action to the spider robot

    mj_action = action
    assert mj_action.shape == (12,), f"got action {mj_action}"

    SERVO_ORDER = ctrl.get_servos()
    assert len(SERVO_ORDER) == 12

    raw_action = [mujoco_to_dnx(a, sv) for a, sv in zip(mj_action.tolist(), SERVO_ORDER)]
    assert len(raw_action) == 12

    add_to_trajectory(state, "action", {"mujoco": mj_action.tolist(), "raw": raw_action})

    #ctrl.move_all_servos(*raw_action)
    ctrl.move_all_servos_steady(*raw_action)


def step(ctrl, state, model):
    if state["last_time"] is None:
        state["last_time"] = time.time()

    t_start = time.time()
    obs = get_obs(ctrl, state)

    # GEN ACTION FROM POLICY
    action, _states = model.predict(np.array([obs]), deterministic=True)
    if len(action.shape) > 1:
        action = action[0]

    assert action.shape == (12,)

    apply_action(ctrl, action, state)
    t_end = time.time()

    state["interaction_delays"].append(t_end - t_start)
    
    sleep_time = max(0.01, state["last_time"] + state["dt"] - t_end)
    time.sleep(sleep_time)
    state["last_time"] += state["dt"]


def load_model(agent_file):
    from stable_baselines3 import SAC, PPO
    import stable_baselines3 as sb3

    model = None
    load_errors = dict()
    for alg in ["SAC", "PPO", "RecurrentPPO"]:
        try:
            if alg == "SAC":
                from stable_baselines3 import SAC
                model = SAC.load(agent_file)
            elif alg == "PPO":
                from stable_baselines3 import PPO
                model = PPO.load(agent_file)
            elif alg == "RecurrentPPO":
                from sb3_contrib import RecurrentPPO
                model = RecurrentPPO.load(agent_file)
        except Exception as e:
            model = None
            load_errors[alg] = e
        if model is not None:
            break

    if model is None:
        lines = [f"Could not trained agent from {agent_file}"]
        for alg, alg_e in load_errors.items():
            lines.append(f"{alg} error: {alg_e}")
        raise RuntimeError("\n".join(lines))

    return model


# Some trajetory functions
def add_to_trajectory(state, kind, content):
    state["trajectory"].append({"time": time.time(), "kind": kind, "content": content})
def add_info(state, msg):
    add_to_trajectory(state, kind="info", content=msg)
    print(msg, flush=True)


def run_policy(file):
    import torch
    from .controllers import SpiderController

    model = load_model(file)

    state = {
        "gyro": None,
        "velocity": None,
        "last_position": None,
        "dt": 0.25,
        "last_time": None,
        "interaction_delays": [],
        "trajectory": [],
    }

    add_info(state, "Creating controller")
    ctrl = SpiderController()
    ctrl.set_baudrate(4_000_000)
    ctrl.set_duration(1000)
    ctrl.set_acceleration(500)
    ctrl.disable_torque()
    SERVO_ORDER = ctrl.get_servos()
    #print("Rebooting servos", flush=True)
    #for i, servo in enumerate(SERVO_ORDER):
    #    print(f" - rebooting servo for {servo}", flush=True)
    #    ctrl.reboot_single_servo(servo)
    #time.sleep(0.5)
    #ctrl.reboot_all_servos()
    #time.sleep(0.5)
    ctrl.setup_all_servos()
    time.sleep(0.25)
    ctrl.enable_torque()
    time.sleep(0.25)

    add_info(state, "Resetting legs")
    apply_action(ctrl, np.zeros((12,)), state)
    time.sleep(1.0)

    ctrl.set_duration(500)
    ctrl.set_acceleration(250)

    time.sleep(1.0)

    add_info(state, "Going into standup position")
    STANDUP_ACTIONS = [
        [   -0.52309,     1.3963, 0.00069025,
             0.52309,     1.3963, 0.00063209,
             0.52309,     1.3963, 0.00063209,
            -0.52309,     1.3955, 0.00074842],
        [   -0.52309,     1.3963,     2.2695,
             0.52309,     1.3963,     2.2694,
             0.52309,     1.3963,     2.2694,
            -0.52309,     1.3955,     2.2695],
        [   -0.52309,    0.70,     2.0946,
             0.52309,    0.70,     2.0945,
             0.52309,    0.70,     2.0945,
            -0.52309,    0.70,     2.0946],
        [   -0.52309,    0.70,     2.0946,
             0.52309,     1.1339,     2.15,
             0.52309,     1.1339,     2.15,
            -0.52309,    0.70,     2.0946],
        [   -0.52309,    0.70,     2.0946,
             0.52309,    0.70,     2.15,
             0.52309,    0.70,     2.15,
            -0.52309,    0.70,     2.0946],
        [   -0.52309,     1.1339,     2.15,
             0.52309,    0.70,     2.15,
             0.52309,    0.70,     2.15,
            -0.52309,     1.1347,     2.15],
        [   -0.52309,    0.70,     2.15,
             0.52309,    0.70,     2.15,
             0.52309,    0.70,     2.15,
            -0.52309,    0.70,     2.15],
        [
                -0.40, 0.70, 2.15,
                 0.40, 0.70, 2.15,
                 0.40, 0.70, 2.15,
                -0.40, 0.70, 2.15
        ]
    ]
    #stand_pos = [
    #    -0.40, 0.70, 2.15,
    #     0.40, 0.70, 2.15,
    #     0.40, 0.70, 2.15,
    #    -0.40, 0.70, 2.15,
    #]
    stand_pos = STANDUP_ACTIONS[-1]
    for action in STANDUP_ACTIONS:
        apply_action(ctrl, np.array(action), state)
        time.sleep(0.5)

    add_info(state, "NOW STANDING")
    time.sleep(3.0)

    had_error = False
    try:
        T_START = time.time()
        for i in range(16):
            step(ctrl, state, model)
    except Exception as e:
        had_error = True
        traceback.print_exc()

    add_info(state, "Model done")
    add_info(state, f"Interaction delays: {state['interaction_delays']}")

    if had_error:
        time.sleep(2.0)
        add_info(state, "Performing recovery read")
        get_obs(ctrl, state)
        #spider_data = ctrl.read_all_servos_RAM()
        #for k, entry in spider_data.items():
        #    print(f"{k}: {entry}")

    time.sleep(1.0)
    ctrl.set_duration(1000)
    ctrl.set_acceleration(500)
    time.sleep(1.0)
    apply_action(ctrl, np.array(stand_pos), state)


    time.sleep(2.0)
    add_info(state, "Resetting legs")
    apply_action(ctrl, np.zeros((12,)), state)
    time.sleep(1.0)

    ctrl.disable_torque()
    OUTPUT_PATH = pathlib.Path("/output")
    OUTPUT_JSON = OUTPUT_PATH / datetime.now().strftime("run_policy_trajectory_%Y-%m-%d_%H%M%S.json")

    add_info(state, f"Done, writing output to {OUTPUT_JSON}")
    with open(OUTPUT_JSON, "w+") as f:
        json.dump({"trajectory": state["trajectory"]}, f)

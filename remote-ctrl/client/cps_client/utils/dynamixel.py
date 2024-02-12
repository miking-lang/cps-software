
from math import pi
from typing import Optional

# Pre-processing of dynamixel data

zero_shift_dics = {
    #"BR_OUTER_SHOULDER": -0.202,
    #"FR_OUTER_SHOULDER": -0.202,
    #"FL_OUTER_SHOULDER": -0.273,
    #"BL_OUTER_SHOULDER": -0.272,
    # old values above
    "BR_INNER_SHOULDER": 0.00624,
    "BR_OUTER_SHOULDER": -0.142,
    "BR_ELBOW": -0.126,
    "FR_INNER_SHOULDER": 0.00992,
    "FR_OUTER_SHOULDER": -0.142,
    "FR_ELBOW": -0.126,
    "FL_INNER_SHOULDER": 0.00654,
    "FL_OUTER_SHOULDER": -0.143,
    "FL_ELBOW": -0.126,
    "BL_INNER_SHOULDER": 0.00988,
    "BL_OUTER_SHOULDER": -0.143,
    "BL_ELBOW": -0.126,
    "NO_KEY": 0.0,
}

POSITIVE_JOINTS = {
    "FR_ELBOW",
    "BL_ELBOW",
}

def dnx_to_mujoco(angle, motor_key):
    if motor_key in POSITIVE_JOINTS:
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        return float((angle-2048)*pi*0.087891/180 + zero_shift_dics[motor_key])
    else:
        return float((2048-angle)*pi*0.087891/180 + zero_shift_dics[motor_key])
    
def mujoco_to_dnx(angle, motor_key):
    if motor_key in POSITIVE_JOINTS:
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        return int(2048 + round(180*(angle-zero_shift_dics[motor_key])/(pi*0.087891)))
    else:
        return int(2048 - round(180*(angle-zero_shift_dics[motor_key])/(pi*0.087891)))



def raw_to_radians(raw : int, key : Optional[str] = None) -> float:
    """Converts a raw value into a float in radians"""
    if key is None:
        key = "NO_KEY"
    return dnx_to_mujoco(raw, key)


def raw_to_degrees(raw : int, key : Optional[str] = None) -> float:
    """Converts a raw value into a float in degrees"""
    rad = raw_to_radians(raw, key)
    return rad * (180/pi)


def radians_to_raw(rad : float, key : Optional[str] = None) -> int:
    """Converts a float in radians to a raw int value"""
    if key is None:
        key = "NO_KEY"
    return mujoco_to_dnx(rad, key)


def degrees_to_raw(deg : float, key : Optional[str] = None) -> int:
    """Converts a float in degrees to a raw int value"""
    rad = deg * (pi/180)
    return radians_to_raw(rad, key)

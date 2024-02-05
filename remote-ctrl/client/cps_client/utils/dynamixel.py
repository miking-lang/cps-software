
from math import pi
from typing import Optional

# Pre-processing of dynamixel data
zero_shift_dics = {
    "BR_INNER_SHOULDER": 0.00624,
    "BR_OUTER_SHOULDER": -0.142,
    "BR_ELBOW": -0.126,
    "FR_INNER_SHOULDER": 0.00992,
    "FR_OUTER_SHOULDER": -0.142,
    "FR_ELBOW": -0.126,
    "BL_INNER_SHOULDER": 0.00654,
    "BL_OUTER_SHOULDER": -0.143,
    "BL_ELBOW": -0.126,
    "FL_INNER_SHOULDER": 0.00988,
    "FL_OUTER_SHOULDER": -0.143,
    "FL_ELBOW": -0.126,
    "NO_KEY": 0.0,
}

def dnx_to_mujoco(angle, motor_key):
    if motor_key == "FR_ELBOW" or motor_key == "BL_ELBOW":
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        return (angle-2048)*pi*0.087891/180 + zero_shift_dics[motor_key]
    else:
        return (2048-angle)*pi*0.087891/180 + zero_shift_dics[motor_key]
    
def mujoco_to_dnx(angle, motor_key):
    if motor_key == "FR_ELBOW" or motor_key == "BL_ELBOW":
        # front_right_elbow and back_left_elbow are the only motors that don't have flipped sign
        return 2048 + round(180*(angle-zero_shift_dics[motor_key])/(pi*0.087891))
    else:
        return 2048 - round(180*(angle-zero_shift_dics[motor_key])/(pi*0.087891))



def raw_to_radians(raw : int, key : Optional[str] = None) -> float:
    """Converts a raw value into a float in radians"""
    if key is None:
        key = "NO_KEY"
    return dnx_to_mujoco(raw, key)
    #return (float(raw) / 4096.0) * (2.0 * pi)

def raw_to_degrees(raw : int, key : Optional[str] = None) -> float:
    """Converts a raw value into a float in degrees"""
    rad = raw_to_radians(raw, key)
    return rad * (180/pi)

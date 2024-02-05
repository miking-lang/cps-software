
from math import pi


def raw_to_radians(raw : int) -> float:
    """Converts a raw value into a float in radians"""
    return (float(raw) / 4096.0) * (2.0 * pi)


def raw_to_degrees(raw : int) -> float:
    """Converts a raw value into a float in degrees"""
    return (float(raw) / 4096.0) * 360.0

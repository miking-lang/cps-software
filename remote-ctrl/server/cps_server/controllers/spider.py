from .controllerbase import ControllerBase, register_command

SERVO_INDEX_LOOKUP = {
    "BR_INNER_SHOULDER": 1,
    "BR_OUTER_SHOULDER": 2,
    "FR_ELBOW":          3,
    "FR_INNER_SHOULDER": 4,
    "BR_ELBOW":          5,
    "FR_OUTER_SHOULDER": 6,
    "BL_OUTER_SHOULDER": 7,
    "FL_INNER_SHOULDER": 8,
    "BL_INNER_SHOULDER": 9,
    "FL_ELBOW":          10,
    "FL_OUTER_SHOULDER": 11,
    "BL_ELBOW":          12,
}

SERVO_ORDER = [
    "BR_INNER_SHOULDER",
    "BR_OUTER_SHOULDER",
    "BR_ELBOW",
    "FR_INNER_SHOULDER",
    "FR_OUTER_SHOULDER",
    "FR_ELBOW",
    "BL_INNER_SHOULDER",
    "BL_OUTER_SHOULDER",
    "BL_ELBOW",
    "FL_INNER_SHOULDER",
    "FL_OUTER_SHOULDER",
    "FL_ELBOW",
]

ALL_SERVO_IDS = [SERVO_INDEX_LOOKUP[name] for name in SERVO_ORDER]


REGISTRY = dict()
register_read = lambda *args, **kwargs: register_command(REGISTRY, *args, kind="read", **kwargs)
register_write = lambda *args, **kwargs: register_command(REGISTRY, *args, kind="write", **kwargs)


class SpiderController(ControllerBase):
    def __init__(self, dev_dxl="/dev/ttyUSB0", dev_accel="/dev/i2c-1"):
        super().__init__(REGISTRY)
        from ..interface.dynamixel import DynamixelHandler
        from mi_cps import Accelerometer
        self.dev_dxl = dev_dxl
        self.dev_accel = dev_accel
        self.dxl_handler = DynamixelHandler(dev_dxl)
        self.accel_handler = Accelerometer(dev_accel, 0x68)

        self.duration = 1500
        self.acceleration = 600
        self.MIN_DURATION = 100
        self.MIN_ACCELERATION = self.MIN_DURATION // 2

        # Sets up the position control registers
        self.dxl_handler.setup_position_control(ALL_SERVO_IDS)

    @register_read()
    def get_duration(self):
        return self.duration

    @register_write(argtypes=[int])
    def set_duration(self, duration):
        if duration < self.MIN_DURATION:
            raise ValueError(f"Expected a duration of at least {self.MIN_DURATION}")
        self.duration = duration
        return {"new_duration": self.duration}

    @register_read()
    def get_acceleration(self):
        return self.acceleration

    @register_write(argtypes=[int])
    def set_acceleration(self, acceleration):
        if acceleration < self.MIN_ACCELERATION:
            raise ValueError(f"Expected an acceleration of at least {self.MIN_ACCELERATION}")
        self.acceleration = acceleration
        return {"new_acceleration": self.acceleration}

    @register_read()
    def get_baudrate(self):
        """Returns the baud rate of the Dynamixel port handler."""
        return self.dxl_handler.get_baud_rate()

    @register_write(argtypes=[int])
    def set_baudrate(self, value):
        """
        Sets the baud rate of the Dynamixel port handler. The servos are not
        modified.
        """
        return self.dxl_handler.set_baud_rate(value)

    @register_read()
    def get_register_list(self):
        from ..interface.dynamixel import REGISTER_LIST
        return [reg.json for reg in REGISTER_LIST]

    @register_read()
    def get_servos(self):
        return SERVO_ORDER

    @register_read()
    def read_accel(self):
        return [
            self.accel_handler.read_accel_x(),
            self.accel_handler.read_accel_y(),
            self.accel_handler.read_accel_z()
        ]

    @register_read()
    def read_gyro(self):
        return [
            self.accel_handler.read_gyro_x(),
            self.accel_handler.read_gyro_y(),
            self.accel_handler.read_gyro_z()
        ]

    @register_write()
    def enable_torque(self):
        return self.dxl_handler.enable_torques(ALL_SERVO_IDS)

    @register_write()
    def disable_torque(self):
        return self.dxl_handler.disable_torques(ALL_SERVO_IDS)

    @register_read()
    def get_torque_enabled(self):
        return self.dxl_handler.get_torque_enabled(ALL_SERVO_IDS)

    @register_write()
    def setup_all_servos(self):
        return self.dxl_handler.setup_position_control(ALL_SERVO_IDS)

    @register_read()
    def read_all_servos_RAM(self):
        return self.dxl_handler.sync_read_all(ALL_SERVO_IDS)

    @register_read(argtypes=[str, str])
    def read_all_servo_registers(self, reg_start, reg_end):
        return self.dxl_handler.sync_read_registers(ALL_SERVO_IDS,
            reg_start=reg_start,
            reg_end=reg_end,
        )

    @register_read()
    def read_all_servo_goalplans(self):
        return self.dxl_handler.sync_read_registers(ALL_SERVO_IDS,
            reg_start="GOAL_POSITION",
            reg_end="POSITION_TRAJECTORY",
        )

    @register_read(argtypes=[str])
    def read_single_servo_position(self, name):
        POSREG = "PRESENT_POSITION"
        ret = self.dxl_handler.sync_read_registers([SERVO_INDEX_LOOKUP[name]],
            reg_start=POSREG, reg_end=POSREG,
        )
        return ret[POSREG][0]

    @register_write(argtypes=[int]*len(ALL_SERVO_IDS))
    def move_all_servos(self, *positions):
        for v in positions:
            if v not in range(0, 4096):
                raise ValueError(f"Servo values must be in range 0 to 4095")

        self.dxl_handler.position_control(
            ALL_SERVO_IDS,
            positions,
            duration=self.duration,
            acceleration=self.acceleration,
        )
        return dict()

    @register_write(argtypes=[str, int])
    def move_single_servo(self, name, position):
        self.dxl_handler.position_control(
            [SERVO_INDEX_LOOKUP[name]],
            [position],
            duration=self.duration,
            acceleration=self.acceleration,
        )
        return dict()

    @register_write(argtypes=[str, str, int])
    def write_single_servo_register(self, reg, name, value):
        self.dxl_handler.group_sync_write(
            reg,
            [SERVO_INDEX_LOOKUP[name]],
            value,
        )
        return dict()

    @register_write(argtypes=[str, int])
    def write_all_servo_registers(self, reg, value):
        self.dxl_handler.group_sync_write(
            reg,
            ALL_SERVO_IDS,
            value,
        )
        return dict()

    @register_write()
    def reboot_all_servos(self):
        self.dxl_handler.reboot_servos(ALL_SERVO_IDS)
        return dict()

    @register_write(argtypes=[str])
    def reboot_single_servo(self, name):
        self.dxl_handler.reboot_servos([SERVO_INDEX_LOOKUP[name]])
        return dict()

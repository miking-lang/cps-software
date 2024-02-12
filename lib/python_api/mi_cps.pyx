
from libc.stdint cimport *

# Get the bool type from libcpp
cimport libcpp
ctypedef libcpp.bool bool


# cps generic includes
cdef extern from "mi_cps/cps.h":
    ctypedef enum cps_err_t:
        CPS_ERR_OK = 0
        CPS_ERR_FAIL
        CPS_ERR_SYS
        CPS_ERR_DXL
        CPS_ERR_ARG
        CPS_ERR_NOT_READY
        CPS_ERR_DRIVE_MODE
        CPS_ERR_TORQUE_OFF
        CPS_ERR_TORQUE_ON
        CPS_ERR_NO_MEM
        CPS_ERR_RPC_SOCKET

    const char *cps_err_t_str[]


# accel specific includes
cdef extern from "mi_cps/accel.h":
    ctypedef enum cps_accel_range_t:
        ACC_SCALE_2_G   = 0 << 3
        ACC_SCALE_4_G   = 1 << 3
        ACC_SCALE_8_G   = 2 << 3
        ACC_SCALE_16_G  = 3 << 3

    ctypedef enum cps_gyro_range_t:
        GYRO_SCALE_250_DEG  = 0 << 3
        GYRO_SCALE_500_DEG  = 1 << 3
        GYRO_SCALE_1000_DEG = 2 << 3
        GYRO_SCALE_2000_DEG = 3 << 3

    ctypedef struct cps_accel_t:
        int fd
        cps_accel_range_t accel_range
        cps_gyro_range_t gyro_range

    ctypedef enum cps_accel_dir_t:
        ACC_DIR_X
        ACC_DIR_Y
        ACC_DIR_Z

    ctypedef enum cps_accel_cmd_t:
        ACC_CONFIG      = 0x1C
        GYRO_CONFIG     = 0x1B
        ACC_PWR_MGMT_1  = 0x6B

    cps_err_t cps_accel_init(
        cps_accel_t *acc,
        const char *device,
        int i2c_addr,
        cps_accel_range_t accel_range,
        cps_gyro_range_t gyro_range
    )

    cps_err_t cps_accel_release(cps_accel_t *acc)

    cps_err_t cps_accel_read_accel(
        cps_accel_t *acc,
        cps_accel_dir_t dir,
        float *result
    )

    cps_err_t cps_accel_read_gyro(
        cps_accel_t *acc,
        cps_accel_dir_t dir,
        float *result
    )

    cps_err_t cps_accel_read_angle(
        cps_accel_t *acc,
        cps_accel_dir_t axis,
        float *result
    )


# dxl specific includes
cdef extern from "mi_cps/dxl.h":
    cdef int DXL_PROTOCOL_VERSION = 2
    cdef int DXL_TIME_PROFILE =     4
    cdef int DXL_VELOCITY_PROFILE = 0

    cdef int DXL_EXTENDED_POSITION_CONTROL = 4
    cdef int DXL_POSITION_CONTROL =          3

    cdef int DXL_ADDR_BaudRate =  8
    cdef int DXL_ADDR_EnableTorque =  64
    cdef int DXL_ADDR_GoalPosition =  116
    cdef int DXL_ADDR_PresentPosition =  132
    cdef int DXL_ADDR_ProfileVelocity =  112
    cdef int DXL_ADDR_ProfileAcceleration =  108
    cdef int DXL_ADDR_MinPosition =  52
    cdef int DXL_ADDR_MaxPosition =  48
    cdef int DXL_ADDR_DriveMode =  10
    cdef int DXL_ADDR_OperatingMode = 11
    cdef int DXL_ADDR_Id =  7
    cdef int DXL_ADDR_SecondaryId =  12
    cdef int DXL_ADDR_PresentVelocity =  128
    cdef int DXL_ADDR_PresentInputVoltage =  144
    cdef int DXL_ADDR_Moving =  122

    cdef int DXL_MAX_SERVOS = 24

    ctypedef enum dxl_err_t:
        DXL_ERR_OK = 0
        DXL_ERR_FAIL
        DXL_ERR_PORT_BUSY
        DXL_ERR_TX_FAIL
        DXL_ERR_RX_FAIL
        DXL_ERR_TX_ERROR
        DXL_ERR_RX_WAITING
        DXL_ERR_RX_TIMEOUT
        DXL_ERR_RX_CORRUPT
        DXL_ERR_NOT_AVAILABLE

    ctypedef struct movedata_t:
        uint8_t id
        int angle
        int dur

    cdef extern int g_dxl_port_num

    cps_err_t dxl_init(const char *tty)
    dxl_err_t dxl_get_error()
    void dxl_print_error()
    cps_err_t dxl_servo_move_abs(movedata_t data)
    cps_err_t dxl_servo_move_duration_abs(movedata_t data)
    cps_err_t dxl_servo_move_velocity_abs(movedata_t data)
    cps_err_t dxl_servo_move(movedata_t data)
    cps_err_t dxl_servo_move_duration(movedata_t data)
    cps_err_t dxl_servo_move_velocity(movedata_t data)
    cps_err_t dxl_servo_move_many_abs(movedata_t data[], size_t count)
    cps_err_t dxl_servo_move_many_duration_abs(movedata_t data[], size_t count)
    cps_err_t dxl_servo_move_many_velocity_abs(movedata_t data[], size_t count)
    cps_err_t dxl_servo_move_many(movedata_t data[], size_t count)
    cps_err_t dxl_servo_move_many_duration(movedata_t data[], size_t count)
    cps_err_t dxl_servo_move_many_velocity(movedata_t data[], size_t count)
    cps_err_t dxl_set_id(uint8_t id)
    cps_err_t dxl_set_secondary_id(uint8_t id, uint8_t secondaryID)
    cps_err_t dxl_set_min_max_positions(uint8_t id, uint32_t minPos, uint32_t maxPos)
    cps_err_t dxl_get_torque(uint8_t id, bool *status)
    cps_err_t dxl_enable_torque(uint8_t id)
    cps_err_t dxl_disable_torque(uint8_t id)
    cps_err_t dxl_set_baudrate(uint8_t id, uint8_t baudRateVal)
    cps_err_t dxl_set_goal_position(uint8_t id, uint32_t goalPosition)
    cps_err_t dxl_set_profile_velocity(uint8_t id, uint32_t velocity)
    cps_err_t dxl_set_profile_acceleration(uint8_t id, uint32_t acceleration)
    cps_err_t dxl_set_drive_mode(uint8_t id, uint8_t driveMode)
    cps_err_t dxl_get_drive_mode(uint8_t id, uint8_t *result)
    cps_err_t dxl_set_drive_mode_safe(uint8_t id, uint8_t driveMode)
    cps_err_t dxl_set_operating_mode(uint8_t id, uint8_t operatingMode)
    cps_err_t dxl_get_current_position(uint8_t id, uint32_t *result)
    cps_err_t dxl_get_current_velocity(uint8_t id, uint32_t *result)
    cps_err_t dxl_get_current_input_voltage(uint8_t id, uint16_t *result)
    cps_err_t dxl_get_is_moving(uint8_t id, uint8_t *result)


# Specific Wrapper code
cdef class Accelerometer:
    """
    Accelerometer wrapper class
    """
    cdef cps_accel_t _acc

    cdef str _i2c_dev
    cdef int _i2c_addr
    cdef int _is_init

    def __init__(self, i2c_dev : str, i2c_addr : int):
        self._i2c_dev = i2c_dev
        self._i2c_addr = i2c_addr
        self._is_init = False
        ret = cps_accel_init(
            &self._acc,
            i2c_dev.encode("utf-8"),
            i2c_addr,
            ACC_SCALE_2_G,
            GYRO_SCALE_2000_DEG
        )
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))
        self._is_init = True

    def __del__(self):
        if self._is_init:
            self.release()

    def release(self):
        cps_accel_release(&self._acc)

    def i2c_dev(self): return self._i2c_dev
    def i2c_addr(self): return self._i2c_addr

    cdef _read_accel(self, dir):
        cdef float result
        ret = cps_accel_read_accel(&self._acc, dir, &result)
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))
        return result

    cdef _read_gyro(self, dir):
        cdef float result
        ret = cps_accel_read_gyro(&self._acc, dir, &result)
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))
        return result

    def read_accel_x(self): return self._read_accel(ACC_DIR_X)
    def read_accel_y(self): return self._read_accel(ACC_DIR_Y)
    def read_accel_z(self): return self._read_accel(ACC_DIR_Z)

    def read_gyro_x(self): return self._read_gyro(ACC_DIR_X)
    def read_gyro_y(self): return self._read_gyro(ACC_DIR_Y)
    def read_gyro_z(self): return self._read_gyro(ACC_DIR_Z)

# Note: Currently no DXL code here, using the dynamixel api instead.

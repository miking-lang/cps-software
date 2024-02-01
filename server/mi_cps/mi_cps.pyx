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

cdef class Accelerometer:
    cdef cps_accel_t acc

    cdef str _i2c_dev
    cdef int _i2c_addr

    def __init__(self, i2c_dev : str, i2c_addr : int):
        self._i2c_dev = i2c_dev
        self._i2c_addr = i2c_addr
        ret = cps_accel_init(
            &self.acc,
            i2c_dev.encode("utf-8"),
            i2c_addr,
            ACC_SCALE_2_G,
            GYRO_SCALE_2000_DEG
        )
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))

    def read_accel_x(self):
        cdef float result
        ret = cps_accel_read_accel(&self.acc, ACC_DIR_X, &result)
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))
        return result

    def read_accel_y(self):
        cdef float result
        ret = cps_accel_read_accel(&self.acc, ACC_DIR_Y, &result)
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))
        return result

    def read_accel_z(self):
        cdef float result
        ret = cps_accel_read_accel(&self.acc, ACC_DIR_Z, &result)
        if ret != CPS_ERR_OK:
            raise RuntimeError(cps_err_t_str[int(ret)].decode("utf-8"))
        return result

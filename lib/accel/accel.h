#pragma once

typedef struct {
    int fd;
} cps_accel_t;

typedef enum {
    CPS_ERR_OK = 0,
    CPS_ERR_FAIL,   /* generic error */
    CPS_ERR_SYS,    /* system error (check errno) */
} cps_err_t;

typedef enum {
    /* TODO: confirm names for ranges */
    ACC_RANGE_2  = 0x00,
    ACC_RANGE_4  = 0x08,
    ACC_RANGE_8  = 0x10,
    ACC_RANGE_16 = 0x18,
} cps_accel_range_t;

typedef enum {
    ACC_DIR_X = 0x3B,
    ACC_DIR_Y = 0x3D,
    ACC_DIR_Z = 0x3F,
} cps_accel_dir_t;

typedef enum {
    ACC_CONFIG      = 0x1C,
    ACC_PWR_MGMT_1  = 0x6B,
} cps_acc_cmd_t;

cps_err_t cps_accel_init(cps_accel_t *acc, const char *device, int i2c_addr,
    cps_accel_range_t range);
cps_err_t cps_accel_read_accel(cps_accel_t *acc, cps_accel_dir_t dir,
        cps_accel_range_t range, float *result);

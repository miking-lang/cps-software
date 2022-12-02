#pragma once
#include "cps.h"

typedef enum {
    ACC_SCALE_2_G   = 0 << 3,
    ACC_SCALE_4_G   = 1 << 3,
    ACC_SCALE_8_G   = 2 << 3,
    ACC_SCALE_16_G  = 3 << 3,
} cps_accel_range_t;

typedef enum {
    /* scale x1000 */
    GYRO_SCALE_250_DEG  = 0 << 3,
    GYRO_SCALE_500_DEG  = 1 << 3,
    GYRO_SCALE_1000_DEG = 2 << 3,
    GYRO_SCALE_2000_DEG = 3 << 3,
} cps_gyro_range_t;

typedef struct {
    int fd;
    cps_accel_range_t accel_range;
    cps_gyro_range_t gyro_range;
} cps_accel_t;

typedef enum {
    ACC_DIR_X,
    ACC_DIR_Y,
    ACC_DIR_Z,
} cps_accel_dir_t;

typedef enum {
    ACC_CONFIG      = 0x1C,
    GYRO_CONFIG     = 0x1B,
    ACC_PWR_MGMT_1  = 0x6B,
} cps_accel_cmd_t;

cps_err_t cps_accel_init(cps_accel_t *acc, const char *device, int i2c_addr,
    cps_accel_range_t accel_range, cps_gyro_range_t gyro_range);
cps_err_t cps_accel_read_accel(cps_accel_t *acc, cps_accel_dir_t dir,
    float *result);
cps_err_t cps_accel_read_gyro(cps_accel_t *acc, cps_accel_dir_t dir,
    float *result);
cps_err_t cps_accel_read_angle(cps_accel_t *acc, cps_accel_dir_t axis,
    float *result);

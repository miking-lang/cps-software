/**
 * @file accel.h
 * @brief Library for working with accelerometer ICs.
 */
#pragma once
#include "cps.h"

/** Accelerometer output scaling factor */
typedef enum {
    ACC_SCALE_2_G   = 0 << 3,
    ACC_SCALE_4_G   = 1 << 3,
    ACC_SCALE_8_G   = 2 << 3,
    ACC_SCALE_16_G  = 3 << 3,
} cps_accel_range_t;

/** Gyroscope output scaling factor */
typedef enum {
    /* scale x1000 */
    GYRO_SCALE_250_DEG  = 0 << 3,
    GYRO_SCALE_500_DEG  = 1 << 3,
    GYRO_SCALE_1000_DEG = 2 << 3,
    GYRO_SCALE_2000_DEG = 3 << 3,
} cps_gyro_range_t;

/** Accelerometer IC information struct */
typedef struct {
    int fd;
    cps_accel_range_t accel_range;
    cps_gyro_range_t gyro_range;
} cps_accel_t;

/** Accelerometer/gyroscope direction selectors */
typedef enum {
    ACC_DIR_X,
    ACC_DIR_Y,
    ACC_DIR_Z,
} cps_accel_dir_t;

/** Accelerometer i2c commands */
typedef enum {
    ACC_CONFIG      = 0x1C,
    GYRO_CONFIG     = 0x1B,
    ACC_PWR_MGMT_1  = 0x6B,
} cps_accel_cmd_t;

/**
 * @brief Initialize an accelerometer IC.
 * 
 * @param acc accelerometer IC struct
 * @param device path to i2c device
 * @param i2c_addr i2c address of the accelerometer IC
 * @param accel_range scaling for accelerometer output
 * @param gyro_range scaling for gyroscope output
 * 
 * @retval CPS_ERR_SYS i2c error
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_accel_init(cps_accel_t *acc, const char *device, int i2c_addr,
    cps_accel_range_t accel_range, cps_gyro_range_t gyro_range);

/**
 * @brief Releases the handle to accelerometer IC.
 *
 * Releases the I2C resources, such that others can use the accelerometer.
 *
 * @param acc accelerometer IC struct
 * 
 * @retval CPS_ERR_SYS i2c error
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_accel_release(cps_accel_t *acc);

/**
 * @brief Read accelerometer value.
 * 
 * @param acc accelerometer IC struct
 * @param dir accelerometer direction to query
 * @param[out] result storage for resulting value in g-forces
 * 
 * @retval CPS_ERR_ARG invalid direction
 * @retval CPS_ERR_SYS i2c error
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_accel_read_accel(cps_accel_t *acc, cps_accel_dir_t dir,
    float *result);

/**
 * @brief Read gyroscope value.
 * 
 * @param acc accelerometer IC struct
 * @param dir gyroscope direction to query
 * @param[out] result storage for resulting value in degrees per seconds (°/s)
 * 
 * @retval CPS_ERR_ARG invalid direction
 * @retval CPS_ERR_SYS i2c error
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_accel_read_gyro(cps_accel_t *acc, cps_accel_dir_t dir,
    float *result);

/**
 * @brief Determine current angle on a given axis.
 * 
 * @param acc accelerometer IC struct
 * @param axis selected axis (only #ACC_DIR_X or #ACC_DIR_Y)
 * @param[out] result storage for resulting value in degrees (°)
 * 
 * @retval CPS_ERR_ARG invalid axis
 * @retval CPS_ERR_SYS i2c error
 * @retval CPS_ERR_OK no error
 */
cps_err_t cps_accel_read_angle(cps_accel_t *acc, cps_accel_dir_t axis,
    float *result);

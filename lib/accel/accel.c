#include <math.h>
#include <stdio.h>
#include <stdint.h>

#include <fcntl.h>
#include <sys/ioctl.h>
#include <i2c/smbus.h>
#include <linux/i2c-dev.h>

#include "accel.h"

static float cps_accel_scale_mod(cps_accel_range_t range) {
    switch (range) {
    case ACC_SCALE_2_G   : return 0x4000;
    case ACC_SCALE_4_G   : return 0x2000;
    case ACC_SCALE_8_G   : return 0x1000;
    case ACC_SCALE_16_G  : return 0x0800;
    }
}

static float cps_gyro_scale_mod(cps_gyro_range_t range) {
    switch (range) {
    case GYRO_SCALE_250_DEG : return 131.0;
    case GYRO_SCALE_500_DEG : return  65.5;
    case GYRO_SCALE_1000_DEG: return  32.8;
    case GYRO_SCALE_2000_DEG: return  16.4;
    }
}

cps_err_t cps_i2c_read16(int fd, uint8_t command, uint16_t *result) {
    int32_t data;

    data = i2c_smbus_read_word_data(fd, command);
    if (data < 0)
        return CPS_ERR_SYS;
    /* byteswap */
    data = ((data & 0xFF) << 8) | ((data & 0xFF00) >> 8);

    *result = (int16_t)data;
    return CPS_ERR_OK;
}

cps_err_t cps_accel_init(cps_accel_t *acc, const char *device, int i2c_addr,
        cps_accel_range_t accel_range, cps_gyro_range_t gyro_range) {
    int fd;

    if ((fd = open(device, O_RDWR)) < 0) {
        /* file not found or permission error */
        return CPS_ERR_SYS;
    }

    if (ioctl(fd, I2C_SLAVE, i2c_addr) < 0) {
        return CPS_ERR_SYS;
    }

    if (i2c_smbus_write_word_data(fd, ACC_PWR_MGMT_1, 0) < 0) {
        /* check address/connection */
        return CPS_ERR_SYS;
    }

    /* setup accelerometer and gyroscope ranges */
    if (i2c_smbus_write_word_data(fd, ACC_CONFIG, accel_range) < 0) {
        return CPS_ERR_SYS;
    }
    if (i2c_smbus_write_word_data(fd, GYRO_CONFIG, gyro_range) < 0) {
        return CPS_ERR_SYS;
    }

    acc->fd = fd;
    acc->accel_range = accel_range;
    acc->gyro_range = gyro_range;

    return CPS_ERR_OK;
}

cps_err_t cps_accel_read_accel(cps_accel_t *acc, cps_accel_dir_t dir,
        float *result) {
    int16_t data;
    uint8_t cmd;

    switch (dir) {
    case ACC_DIR_X: cmd = 0x3B; break;
    case ACC_DIR_Y: cmd = 0x3D; break;
    case ACC_DIR_Z: cmd = 0x3F; break;
    default: return CPS_ERR_ARG;
    }

    if (cps_i2c_read16(acc->fd, dir, &data) < 0) {
        return CPS_ERR_SYS;
    }

    *result = (float)data / cps_accel_scale_mod(acc->accel_range);

    return CPS_ERR_OK;
}

cps_err_t cps_accel_read_gyro(cps_accel_t *acc, cps_accel_dir_t dir,
        float *result) {
    int16_t data;
    uint8_t cmd;

    switch (dir) {
    case ACC_DIR_X: cmd = 0x43; break;
    case ACC_DIR_Y: cmd = 0x45; break;
    case ACC_DIR_Z: cmd = 0x47; break;
    default: return CPS_ERR_ARG;
    }

    if (cps_i2c_read16(acc->fd, cmd, &data) < 0) {
        return CPS_ERR_SYS;
    }

    *result = (float)data / cps_gyro_scale_mod(acc->gyro_range);

    return CPS_ERR_OK;
}

cps_err_t cps_accel_read_angle(cps_accel_t *acc, cps_accel_dir_t axis,
        float *result) {
    float data;
    float angle_rad;
    cps_err_t ret = CPS_ERR_OK;

    switch (axis) {
    case ACC_DIR_X: {
        CPS_RET_ON_ERR(cps_accel_read_accel(acc, ACC_DIR_Y, &data));
        /* TODO: should this be clamped or scaled? */
        data = MAX(-1.0, MIN(1.0, data));
        angle_rad = asin(data);
        break;
    }
    case ACC_DIR_Y: {
        CPS_RET_ON_ERR(cps_accel_read_accel(acc, ACC_DIR_X, &data));
        data = MAX(-1.0, MIN(1.0, data));
        angle_rad = -asin(data);
        break;
    }
    default: return CPS_ERR_ARG;
    }

    *result = angle_rad * 180/M_PI;

    return ret;
}

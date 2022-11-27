#include <stdio.h>
#include <stdint.h>

#include <fcntl.h>
#include <sys/ioctl.h>
#include <i2c/smbus.h>
#include <linux/i2c-dev.h>

#include "accel.h"

static int cps_accel_scale_mod(cps_accel_range_t range) {
    return 0x8000 / range;
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
        cps_accel_range_t range) {
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

    if (i2c_smbus_write_word_data(fd, ACC_CONFIG, range) < 0) {
        return CPS_ERR_SYS;
    }

    acc->fd = fd;

    return CPS_ERR_OK;
}

cps_err_t cps_accel_read_accel(cps_accel_t *acc, cps_accel_dir_t dir,
        cps_accel_range_t range, float *result) {
    int16_t data;

    if (cps_i2c_read16(acc->fd, dir, &data) < 0) {
        return CPS_ERR_SYS;
    }

    *result = (float)data / cps_accel_scale_mod(range);

    return CPS_ERR_OK;
}

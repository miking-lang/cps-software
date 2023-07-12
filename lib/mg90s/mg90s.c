#include"mg90s.h"

cps_err_t setPWMFreq(int file, int freq) {
    int prescale = (int)(25000000.0f / (4096 * freq) - 0.5f);
    uint8_t oldmode = i2c_smbus_read_byte_data(file, PCA9685_MODE1);
    uint8_t newmode = (oldmode & 0x7F) | 0x10; // sleep

    i2c_smbus_write_byte_data(file, PCA9685_MODE1, newmode); // go to sleep
    i2c_smbus_write_byte_data(file, PCA9685_PRESCALE, prescale); // set the prescaler
    i2c_smbus_write_byte_data(file, PCA9685_MODE1, oldmode);
    usleep(5000);
    i2c_smbus_write_byte_data(file, PCA9685_MODE1, oldmode | 0x80);

    return CPS_ERR_OK;
}

cps_err_t setPWM(int file, int channel, int on, int off) {
    i2c_smbus_write_byte_data(file, 0x06 + 4 * channel, on & 0xFF);
    i2c_smbus_write_byte_data(file, 0x07 + 4 * channel, on >> 8);
    i2c_smbus_write_byte_data(file, 0x08 + 4 * channel, off & 0xFF);
    i2c_smbus_write_byte_data(file, 0x09 + 4 * channel, off >> 8);

    return CPS_ERR_OK;
}

cps_err_t initI2C(int *file){
    char filename[20];

    snprintf(filename, 19, "/dev/i2c-1");
    *file = open(filename, O_RDWR);
    if (*file < 0) {
        printf("Failed to open bus.\n");
        exit(1);
    }

    if (ioctl(*file, I2C_SLAVE, I2C_ADDR) < 0) {
        printf("Failed to acquire bus access or talk to slave.\n");
        exit(1);
    }

    return CPS_ERR_OK;
}

cps_err_t closeI2C(int file){
    //Close I2C channel
    close(file);

    return CPS_ERR_OK;
}
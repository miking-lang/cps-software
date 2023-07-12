#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <i2c/smbus.h>  // Include this for i2c_smbus_* functions
#include <stdint.h>  // Include this for uint8_t
#include <stdio.h>
#include "cps.h"

#define I2C_ADDR 0x40 // I2C address of PCA9685
#define MG90S_PWM_FREQ 50 // Frequency of PWM signals. In Hz. MG90s operates at 50Hz
#define PCA9685_MODE1 0x00
#define PCA9685_PRESCALE 0xFE

cps_err_t setPWMFreq(int file, int freq);

cps_err_t setPWM(int file, int channel, int on, int off);

cps_err_t initI2C(int *file);

cps_err_t closeI2C(int file);
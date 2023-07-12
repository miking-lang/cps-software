#include "mg90s.h"

int main(){
    cps_err_t ret;
    int file;

    //First initialize the I2C channel
    CPS_ERR_CHECK(initI2C(&file));

    //Set PWM frequency of the frequency corresponding to MG90S servos
    CPS_ERR_CHECK(setPWMFreq(file, MG90S_PWM_FREQ));

    //Move servos on channels 12-15 to angle specified by PWM duty cycle 200
    CPS_ERR_CHECK(setPWM(file, 12, 0, 200));
    CPS_ERR_CHECK(setPWM(file, 13, 0, 200));
    CPS_ERR_CHECK(setPWM(file, 14, 0, 200));
    CPS_ERR_CHECK(setPWM(file, 15, 0, 200));

    //Sleep for 0.1s
    usleep(100000);

    //Disable the torque on the servos by setting their duty cycle to 0
    CPS_ERR_CHECK(setPWM(file, 12, 0, 0));
    CPS_ERR_CHECK(setPWM(file, 13, 0, 0));
    CPS_ERR_CHECK(setPWM(file, 14, 0, 0));
    CPS_ERR_CHECK(setPWM(file, 15, 0, 0));

    //Close the I2C channel before terminating
    closeI2C(file);
}
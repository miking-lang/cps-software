#include <stdbool.h>

#include "dist.h"

/*

P1  Name  gpio    used for

 1  3.3V  ---     3.3V
 6  GND   ---     Ground
24  CE0   8       Sonar echo
26  CE1   7       Sonar trigger

*/

#define ECHO_PIN    8
#define TRIGGER_PIN 7
#define MM_PER_TICK 0.173

static void cps_dist_send_pulse(void) {
   /* trigger a sonar reading */

   gpioWrite(TRIGGER_PIN, PI_ON);
   gpioDelay(10); /* 10us trigger pulse */
   gpioWrite(TRIGGER_PIN, PI_OFF);
}

static void cps_dist_sonar_echo(int gpio, int level, uint32_t tick,
                             void *distanceP) {
    if (gpio == ECHO_PIN) {
        static bool valid = false;
        static uint32_t start;

        if (level == 1) {
            /* Rising edge, pulse is sent */
            start = tick;
            valid = true;
        } else if (level == 0 && valid) {
            /* Falling edge, pulse is received */
            /* tick can overflow, but that works out nonetheless */
            *(int32_t *)distanceP = (int32_t)((tick - start) * MM_PER_TICK);
        }
    }
}

cps_err_t cps_dist_init(cps_dist_t *dist) {
    if (gpioInitialise() < 0) return CPS_ERR_FAIL; //TODO: maybe change this
    // pigpio initialised okay.

    gpioSetMode(TRIGGER_PIN, PI_OUTPUT); //Set trigger to output
    gpioWrite(TRIGGER_PIN, PI_OFF); //Write 0 to trigger

    gpioSetMode(ECHO_PIN, PI_INPUT); //Set echo to input

    gpioSetTimerFunc(0, 50, cps_dist_send_pulse); /* send pulse every 50ms */

    dist->distance = -1;
    void* distanceP = (void*)&dist->distance;

    gpioSetAlertFuncEx(ECHO_PIN, cps_dist_sonar_echo, distanceP); //Run cps_dist_sonar_echo when echo pin changes state

    return CPS_ERR_OK;
}

cps_err_t cps_dist_get_distance(const cps_dist_t *dist, uint32_t *result) {

    if (dist->distance < 0) {
        return CPS_ERR_NOT_READY;
    }

    *result = dist->distance;
    return CPS_ERR_OK;
}

void cps_dist_terminate(void) {
    gpioTerminate();
}

#include "distance.h"

/*

P1  Name  gpio    used for

 1  3.3V  ---     3.3V
 6  GND   ---     Ground
24  CE0   8       Sonar echo
26  CE1   7       Sonar trigger

*/

#define ECHO_PIN    8
#define TRIGGER_PIN 7

/* forward prototypes */

void cps_distance_send_pulse(void);

void cps_distance_sonar_echo(int gpio, int level, uint32_t tick, void* distanceP);

cps_err_t cps_distance_init(cps_distance_t *dist) {
    if (gpioInitialise() < 0) return CPS_ERR_FAIL; //TODO: maybe change this
    // pigpio initialised okay.
    
    gpioSetMode(TRIGGER_PIN, PI_OUTPUT); //Set trigger to output
    gpioWrite(TRIGGER_PIN, PI_OFF); //Write 0 to trigger

    gpioSetMode(ECHO_PIN, PI_INPUT); //Set echo to input

    gpioSetTimerFunc(0, 50, cps_distance_send_pulse); /* send pulse every 50ms */

    dist->distance = -1;
    void* distanceP = (void*)&dist->distance;

    gpioSetAlertFuncEx(ECHO_PIN, cps_distance_sonar_echo, distanceP); //Run cps_distance_sonar_echo when echo pin changes state

    return CPS_ERR_OK;
}

cps_err_t cps_distance_get_distance(cps_distance_t *dist, uint32_t *result) {

    if (dist->distance < 0) {
        return CPS_ERR_NOT_READY;
    }

    *result = dist->distance;
    return CPS_ERR_OK;
}

void cps_distance_terminate() {
    gpioTerminate();
}

void cps_distance_send_pulse(void) {
   /* trigger a sonar reading */

   gpioWrite(TRIGGER_PIN, PI_ON);

   gpioDelay(10); /* 10us trigger pulse */

   gpioWrite(TRIGGER_PIN, PI_OFF);
}

void cps_distance_sonar_echo(int gpio, int level, uint32_t tick, void* distanceP) {//tick = number of millisecounds since boot
    static uint32_t startTick, firstTick = 0;

    int diffTick, distance;

    if (!firstTick) firstTick = tick; //initialize firstTick 

    if (level == PI_ON) {//Rising edge, pulse is sent
       startTick = tick;
    }
    else if (level == PI_OFF) {//Falling edge, pulse is recieved
        diffTick = tick - startTick;
        distance = (int)(diffTick * 0.173); //the one way distance
        *(int*)distanceP = distance;
    }
}
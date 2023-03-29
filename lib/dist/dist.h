#pragma once
#include "cps.h"

#include <unistd.h>
#include <pigpio.h>

typedef struct {
    unsigned pinNumber;
    int32_t distance;
} cps_dist_t;

cps_err_t cps_dist_init(cps_dist_t *dist);

//Returns the distance measured by the distance sensor in mm.
cps_err_t cps_dist_get_distance(const cps_dist_t *dist, uint32_t *result);

//Terminates GPIO.
void cps_dist_terminate(void);
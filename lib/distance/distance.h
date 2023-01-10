#pragma once
#include "cps.h"

#include <unistd.h>
#include <pigpio.h>

typedef struct {
    int pinNumber;
    int distance;
} cps_distance_t;

cps_err_t cps_distance_init(cps_distance_t *dist);

//Returns the distance measured by the distance sensor in mm.
cps_err_t cps_distance_get_distance(cps_distance_t *dist, uint32_t *result);

//Terminates GPIO.
void cps_distance_terminate();
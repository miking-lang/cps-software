#include <stdio.h>

#include "distance.h"

int main(void) {
    /* cps_err_t ret needs to be defined in functions that use CPS_ERR_CHECK
	 * or CPS_RET_ON_ERR.
	 */
    cps_err_t ret;
    cps_distance_t dist;
    
    CPS_ERR_CHECK(cps_distance_init(&dist));
    
    uint32_t result;
    for (int i = 0; i < 10; i++) {
        sleep(1);
        if (cps_distance_get_distance(&dist, &result) == CPS_ERR_NOT_READY) {
            printf("needs to wait for signal to come back\n");
        }
        printf("distance (mm): %d\n", result);
    }

    cps_distance_terminate();
    
}
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>

#include "dxl.h"

int main(void) {
    cps_err_t ret;
	int id = 3; //FR_ELBOW on spider
    int id2 = 5; //BR_ELBOW on spider
	uint32_t pos;

    CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));

    CPS_ERR_CHECK(dxl_get_current_position(id, &pos));
	printf("servo #%d is at %d (range 0-4096)\n", id, pos);
    CPS_ERR_CHECK(dxl_get_current_position(id2, &pos));
	printf("servo #%d is at %d (range 0-4096)\n", id2, pos);
    uint8_t driveMode;
    movedata_t data[] = {{id, 100, 1500}, {id2, 100, 2000}};
    CPS_ERR_CHECK(dxl_set_drive_mode_safe(id, DXL_TIME_PROFILE));
    CPS_ERR_CHECK(dxl_set_drive_mode_safe(id2, DXL_TIME_PROFILE));

    CPS_ERR_CHECK(dxl_enable_torque(id));
    CPS_ERR_CHECK(dxl_enable_torque(id2));

    CPS_ERR_CHECK(dxl_get_drive_mode(id, &driveMode));
    printf("driveMode: %d\n", driveMode);

    CPS_ERR_CHECK(dxl_get_drive_mode(id2, &driveMode));
    printf("driveMode: %d\n", driveMode);

    CPS_ERR_CHECK(dxl_servo_move_many_duration(data, 2));
    sleep(2);
    CPS_ERR_CHECK(dxl_servo_move_many_duration(data, 2));
    sleep(2);
    CPS_ERR_CHECK(dxl_servo_move_many_duration(data, 2));
    sleep(2);
}
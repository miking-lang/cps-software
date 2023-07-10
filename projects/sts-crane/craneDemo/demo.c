#include "dxl.h"
#include<stdio.h>

int main(){
    cps_err_t ret;
    int frontWheelsID = 1;
    int backWheelsID = 2;
	int backServoID = 3;
    int driverID = 4;
    int skewerID = 5;
    int numOfIDs = 2;
    uint8_t allIDs[5] = {1, 2, 3, 4, 5}; 
	uint32_t pos;
    uint8_t driveMode;

    CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));

    CPS_ERR_CHECK(dxl_disable_torque(frontWheelsID))
    CPS_ERR_CHECK(dxl_disable_torque(backWheelsID))

    for(int i = 0; i < numOfIDs; i++) {
        CPS_ERR_CHECK(dxl_set_operating_mode(allIDs[i], DXL_EXTENDED_POSITION_CONTROL));
        CPS_ERR_CHECK(dxl_get_current_position(allIDs[i], &pos));
        CPS_ERR_CHECK(dxl_set_drive_mode_safe(allIDs[i], DXL_TIME_PROFILE));
	    printf("servo #%d is at %d\n", allIDs[i], pos);

        CPS_ERR_CHECK(dxl_enable_torque(allIDs[i]));
        CPS_ERR_CHECK(dxl_get_drive_mode(allIDs[i], &driveMode));
        printf("servo #%d has driveMode: %d\n", allIDs[i], driveMode);
    }

    int length = 7500;
    int duration = length / 3;
    
    movedata_t wheelsMovement[2] = {{backWheelsID, length, duration}, {frontWheelsID, length, duration}};
    movedata_t wheelsMovement2[2] = {{backWheelsID, -length, duration}, {frontWheelsID, -length, duration}}; 
    // movedata_t trolleyMovement = {backServoID, 1000, 500};
    // movedata_t driverMovement = {driverID, 1000, 500};
    // movedata_t skewerMovement = {skewerID, 1000, 500};
    getc(stdin);
    //First move the whole crane
    CPS_ERR_CHECK(dxl_servo_move_many_duration(wheelsMovement, 2));
    getc(stdin);
    CPS_ERR_CHECK(dxl_servo_move_many_duration(wheelsMovement2, 2));
    getc(stdin);
    // //Then move the trolley
    // CPS_ERR_CHECK(dxl_servo_move_duration(trolleyMovement));
    // getc();
    // //Finally move the driver and skewer
    // CPS_ERR_CHECK(dxl_servo_move_duration(driverMovement))        //Driver
    // CPS_ERR_CHECK(dxl_servo_move_duration(skewerMovement))        //Skewer
    // getc();

    //Finally disable the torque
    CPS_ERR_CHECK(dxl_disable_torque(frontWheelsID))
    CPS_ERR_CHECK(dxl_disable_torque(backWheelsID))

    return 0;
}
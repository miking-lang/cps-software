/**
 * @file accel.h
 * @brief Library for working with Dynamixel motors.
 * 
 * @details
 * DynamixelSDK is used as the backend library.
 */
#pragma once

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>

#include "cps.h"

#define DXL_PROTOCOL_VERSION 2

//Drive modes. All bits except bit 2 (Profile Configuration) are always set to 0.
#define DXL_TIME_PROFILE     4
#define DXL_VELOCITY_PROFILE 0

//Operating modes
#define DXL_VELOCITY_CONTROL 1
#define DXL_EXTENDED_POSITION_CONTROL 4

#define DXL_POSITION_CONTROL 3

#define DXL_ADDR_BaudRate  8
#define DXL_ADDR_EnableTorque  64
#define DXL_ADDR_GoalPosition  116
#define DXL_ADDR_GoalVelocity  104
#define DXL_ADDR_PresentPosition  132
#define DXL_ADDR_HomingOffset 20
#define DXL_ADDR_ProfileVelocity  112
#define DXL_ADDR_ProfileAcceleration  108
#define DXL_ADDR_MinPosition  52
#define DXL_ADDR_MaxPosition  48
#define DXL_ADDR_DriveMode  10
#define DXL_ADDR_OperatingMode 11
#define DXL_ADDR_Id  7
#define DXL_ADDR_SecondaryId  12
#define DXL_ADDR_PresentVelocity  128
#define DXL_ADDR_PresentInputVoltage  144
#define DXL_ADDR_Moving  122

#ifndef DXL_MAX_SERVOS
    #define DXL_MAX_SERVOS 24
#endif

typedef enum {
    DXL_ERR_OK = 0,
    DXL_ERR_FAIL, /* generic error */
    DXL_ERR_PORT_BUSY,
    DXL_ERR_TX_FAIL,
    DXL_ERR_RX_FAIL,
    DXL_ERR_TX_ERROR,
    DXL_ERR_RX_WAITING,
    DXL_ERR_RX_TIMEOUT,
    DXL_ERR_RX_CORRUPT,
    DXL_ERR_NOT_AVAILABLE,
} dxl_err_t;

// Used in Position Control Mode and Extended Position Control Mode
typedef struct {
    uint8_t id;
    int angle;
    int dur; //TODO: Maybe change the name of this. Could be duration or velocity.
} movedata_t;

// Used in Velocity Control Mode
typedef struct {
    uint8_t id;
    int velocity;
} movedata_vel_t;

extern int g_dxl_port_num;

/**
 * @brief Initialize DynamixelSDK.
 * 
 * @param tty path to tty device mapped to the Dynamixel controller
 * 
 * @retval CPS_ERR_FAIL DynamixelSDK failed to initialize
 * @retval CPS_ERR_OK no error
 */
cps_err_t dxl_init(const char *tty);

/**
 * @brief Return the last DynamixelSDK error.
 * 
 * @return See source of #dxl_get_error
 */
dxl_err_t dxl_get_error(void);

/**
 * @brief Print last DynamixelSDK errors to stderr.
 */
void dxl_print_error(void);

/*
 * Higher-level functions, encapsulating several commands
 */

// Goes to the specified angle in without checking drive mode
cps_err_t dxl_servo_move_abs(movedata_t data);

// Changes the dynamixel servo's drive mode if necessary,
// and moves to the specified angle...
// ...during a specified time period (seconds)
cps_err_t dxl_servo_move_duration_abs(movedata_t data);
// ...or with a specified velicity
cps_err_t dxl_servo_move_velocity_abs(movedata_t data);

// Same as above but in Velocity Control Mode. It sets the Goal Velocity instead of the Goal Position.
cps_err_t dxl_servo_move_duration_velMode(movedata_vel_t data);

// Does the same thing as above but relatively
cps_err_t dxl_servo_move(movedata_t data);
cps_err_t dxl_servo_move_duration(movedata_t data);
cps_err_t dxl_servo_move_velocity(movedata_t data);

// Move multiple servos at once to absolute position,
// with durations or velocity specified for each servo
cps_err_t dxl_servo_move_many_abs(movedata_t data[], size_t count);
cps_err_t dxl_servo_move_many_duration_abs(movedata_t data[], size_t count);
cps_err_t dxl_servo_move_many_velocity_abs(movedata_t data[], size_t count);

// Same as above but in Velocity Control Mode.
cps_err_t dxl_servo_move_many_duration_velMode(movedata_vel_t data[], size_t count);

// Move multiple servos at once to relative position, with durations specified for each servo
cps_err_t dxl_servo_move_many(movedata_t data[], size_t count);
cps_err_t dxl_servo_move_many_duration(movedata_t data[], size_t count);
cps_err_t dxl_servo_move_many_velocity(movedata_t data[], size_t count);

/*
 * Lower-level functions, for directly communicating with the servos
 */
//Reboot a servo
cps_err_t dxl_reboot(uint8_t id);
//Set a unique ID for this servo. Before an ID is set it is assumed that the motor has ID 1, the default ID of Dynamixel motors
cps_err_t dxl_set_id(uint8_t id);

//Set a secondary to group specific servos. For example, all elbow joints could get the same secondary ID
cps_err_t dxl_set_secondary_id(uint8_t id, uint8_t secondaryID);

//TODO: Implement this
//Sets the minimum and maximum positions for the servo struct pointed to by the servo pointer
cps_err_t dxl_set_min_max_positions(uint8_t id, uint32_t minPos, uint32_t maxPos);

cps_err_t dxl_get_torque(uint8_t id, bool *status);

//Enable torque for the servo represented by the Servo struct servo
cps_err_t dxl_enable_torque(uint8_t id);

//Disable torque for the servo represented by the Servo struct servo
cps_err_t dxl_disable_torque(uint8_t id);

//Set the baud rate of this servo, which specifies how many times per second signals are transmitted/received to/from this servo from the controller
cps_err_t dxl_set_baudrate(uint8_t id, uint8_t baudRateVal);

//Returns the servo's Homing Offset. It is added to the Present Position after the servo is rebooted ot get the acctual position
cps_err_t dxl_set_homing_offset(uint8_t id, uint32_t homingOffset);

//Set the servo's goal position, the position to which it should move
cps_err_t dxl_set_goal_position(uint8_t id, uint32_t goalPosition);

//Set the servo's goal velocity, the velocity which it should reach after acceleration
cps_err_t dxl_set_goal_velocity(uint8_t id, uint32_t goalVelocity);

//Sets the profile velocity. For more info what effect this has on the servo's motion, check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#quick-start
cps_err_t dxl_set_profile_velocity(uint8_t id, uint32_t velocity);

//Sets the profile acceleration. For more info what effect this has on the servo's motion, check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#quick-start
cps_err_t dxl_set_profile_acceleration(uint8_t id, uint32_t acceleration);

//Sets the drive mode of this servo. For more info, check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#drive-mode10
cps_err_t dxl_set_drive_mode(uint8_t id, uint8_t driveMode);

cps_err_t dxl_get_drive_mode(uint8_t id, uint8_t *result);

cps_err_t dxl_set_drive_mode_safe(uint8_t id, uint8_t driveMode);

//Set the operating mode of this servo. Check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w210/#operating-mode11 
cps_err_t dxl_set_operating_mode(uint8_t id, uint8_t operatingMode);

cps_err_t dxl_get_operating_mode(uint8_t id, uint8_t *result);

//------------------------------------  The functions below are for getting parameters from the servo's addresses ----------------------------------

//Returns the servo's Homing Offset. It is added to the Present Position after the servo is rebooted ot get the acctual position
cps_err_t dxl_get_homing_offset(uint8_t id, uint32_t *result);

//Returns the servo's current angle, where 0 degrees = 0 and 360 degrees = 4095
cps_err_t dxl_get_current_position(uint8_t id, uint32_t *result);

//Returns the servo's current velocity, in rev/s
cps_err_t dxl_get_current_velocity(uint8_t id, uint32_t *result);

//Returns the servo's current input voltage, in V
cps_err_t dxl_get_current_input_voltage(uint8_t id, uint16_t *result);

//Returns 1 if this servo is currently moving, otherwise 0
cps_err_t dxl_get_is_moving(uint8_t id, uint8_t *result);

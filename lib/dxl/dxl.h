#pragma once

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

#define DXL_ERROR_CHECK(stmt) if ((stmt) != DXL_ERR_OK) { dxl_print_error(); abort(); }

#define DXL_PROTOCOL_VERSION 2
#define DXL_TIME_PROFILE     4
#define DXL_VELOCITY_PROFILE 0

#define DXL_ADDR_BaudRate  8
#define DXL_ADDR_EnableTorque  64
#define DXL_ADDR_GoalPosition  116
#define DXL_ADDR_PresentPosition  132
#define DXL_ADDR_ProfileVelocity  112
#define DXL_ADDR_ProfileAcceleration  108
#define DXL_ADDR_MinPosition  52
#define DXL_ADDR_MaxPosition  48
#define DXL_ADDR_DriveMode  10
#define DXL_ADDR_Id  7
#define DXL_ADDR_SecondaryId  12
#define DXL_ADDR_PresentVelocity  128
#define DXL_ADDR_PresentInputVoltage  144
#define DXL_ADDR_Moving  122

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
extern int g_dxl_port_num;

/* Initialize DynamixelSDK with the provided tty */
dxl_err_t dxl_init(const char *tty);

/* Return the last error, if any, otherwise DXL_ERR_OK */
dxl_err_t dxl_get_error(void);

/* Print last error to stderr */
void dxl_print_error(void);

/*
 * Higher-level functions, encapsulating several commands
 */
//Changes the dynamixel servo's profile to the time profile, and moves to the specified angle during a specified time period (seconds)
void dxl_servo_move_duration(uint8_t id, uint32_t angle, uint32_t duration, bool relative);

//Changes the dynamixel servo's profile to the velocity profile, and moves to the specified angle with a specified velocity (revolutions/min)
void dxl_servo_move_velocity(uint8_t id, uint32_t angle, uint32_t speed, bool relative);

//Moves the servo smoothly using the Dynamixel servo motor's Trapezoidal velocity profile
void dxl_servo_move(uint8_t id, uint32_t angle, bool relative);

//Move multiple servos smoothly, without caring about their duration or velocity
void dxl_servo_move_many(int numOfServos, uint8_t* idList, uint32_t* goalPositions, bool relative);

// Move multiple servos at once, with durations specified for each servo
void dxl_servo_move_many_duration(int numOfServos, uint8_t* idList, uint32_t* goalPositions, uint32_t* durations, bool relative);

// Move multiple servos at once, with velocities specified for each servo
void dxl_servo_move_many_velocity(int numOfServos, uint8_t* idList, uint32_t* goalPostions, uint32_t* velocities, bool relative);

/*
 * Lower-level functions, for directly communicating with the servos
 */
//Set a unique ID for this servo. Before an ID is set it is assumed that the motor has ID 1, the default ID of Dynamixel motors
dxl_err_t dxl_set_id(uint8_t id);

//Set a secondary to group specific servos. For example, all elbow joints could get the same secondary ID
dxl_err_t dxl_set_secondary_id(uint8_t id, uint8_t secondaryID);

//Sets the minimum and maximum positions for the servo struct pointed to by the servo pointer
dxl_err_t dxl_set_mix_max_positions(uint8_t id, uint32_t minPos, uint32_t maxPos);

//Enable torque for the servo represented by the Servo struct servo
dxl_err_t dxl_enable_torque(uint8_t id);

//Disable torque for the servo represented by the Servo struct servo
dxl_err_t dxl_disable_torque(uint8_t id);

//Set the baud rate of this servo, which specifies how many times per second signals are transmitted/received to/from this servo from the controller
dxl_err_t dxl_set_baudrate(uint8_t id, uint8_t baudRateVal);

//Set the servo's goal position, the position to which it should move
dxl_err_t dxl_set_goal_position(uint8_t id, uint32_t goalPosition);

//Sets the profile velocity. For more info what effect this has on the servo's motion, check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#quick-start
dxl_err_t dxl_set_profile_velocity(uint8_t id, uint32_t velocity);

//Sets the profile acceleration. For more info what effect this has on the servo's motion, check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#quick-start
dxl_err_t dxl_set_profile_acceleration(uint8_t id, uint32_t acceleration);

//Sets the drive mode of this servo. For more info, check: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#drive-mode10
dxl_err_t dxl_set_drive_mode(uint8_t id, uint8_t driveMode);


//------------------------------------  The functions below are for getting parameters from the servo's addresses ----------------------------------

//Returns the servo's current angle, where 0 degrees = 0 and 360 degrees = 4095
dxl_err_t dxl_get_current_position(uint8_t id, uint32_t *result);

//Returns the servo's current velocity, in rev/s
dxl_err_t dxl_get_current_velocity(uint8_t id, uint32_t *result);

//Returns the servo's current input voltage, in V
dxl_err_t dxl_get_current_input_voltage(uint8_t id, uint16_t *result);

//Returns 1 if this servo is currently moving, otherwise 0
dxl_err_t dxl_get_is_moving(uint8_t id, uint8_t *result);

#include <dynamixel_sdk/dynamixel_sdk.h>
#include <dynamixel_sdk/protocol2_packet_handler.h>
#include <string.h>
#include "dxl.h"

PacketData *packetData = {0};
int g_used_port_num = 0;
uint8_t *g_is_using = NULL;

int g_dxl_port_num = -1;

cps_err_t dxl_init(const char *tty) {
    // Initialize PortHandler Structs
    // Set the port path
    // Get methods and members of PortHandlerLinux
    g_dxl_port_num = portHandler(tty);

    // Initialize PacketHandler Structs
    packetHandler();

    if (!openPort(g_dxl_port_num))
        return CPS_ERR_FAIL;

    return CPS_ERR_OK;
}

dxl_err_t dxl_get_error(void) {
    switch (getLastTxRxResult2(g_dxl_port_num)) {
    case COMM_SUCCESS       : return DXL_ERR_OK;
    case COMM_PORT_BUSY     : return DXL_ERR_PORT_BUSY;
    case COMM_TX_FAIL       : return DXL_ERR_TX_FAIL;
    case COMM_RX_FAIL       : return DXL_ERR_RX_FAIL;
    case COMM_TX_ERROR      : return DXL_ERR_TX_ERROR;
    case COMM_RX_WAITING    : return DXL_ERR_RX_WAITING;
    case COMM_RX_TIMEOUT    : return DXL_ERR_RX_TIMEOUT;
    case COMM_RX_CORRUPT    : return DXL_ERR_RX_CORRUPT;
    case COMM_NOT_AVAILABLE : return DXL_ERR_NOT_AVAILABLE;
    /* some unknown error from DSDK, return generic failure */
    default                 : return DXL_ERR_FAIL;
    }
}

void dxl_print_error(void) {
    int comm_result = getLastTxRxResult2(g_dxl_port_num);
    int comm_error = getLastRxPacketError2(g_dxl_port_num);
    if (comm_result != COMM_SUCCESS) {
        fprintf(stderr, "comm_result: %s\n", getTxRxResult2(comm_result));
    }
    if (comm_error != 0) {
        fprintf(stderr, "comm_error: %s\n", getRxPacketError2(comm_error));
    }
}

cps_err_t dxl_servo_move_abs(movedata_t servo) {
    cps_err_t ret;
    // Set the duration or velocity
    CPS_RET_ON_ERR(dxl_set_profile_velocity(servo.id, servo.dur));

    // Set the angle
    CPS_RET_ON_ERR(dxl_set_goal_position(servo.id, servo.angle));

    return CPS_ERR_OK;
}

cps_err_t dxl_check_drive_mode_and_torque_on(uint8_t id, uint8_t wantedDriveMode) {
    cps_err_t ret;

    uint8_t driveMode;
    CPS_RET_ON_ERR(dxl_get_drive_mode(id, &driveMode));

    bool torque;
    CPS_RET_ON_ERR(dxl_get_torque(id, &torque));

    if (driveMode != wantedDriveMode) {
        return CPS_ERR_DRIVE_MODE;
    }
    if (!torque) {
        return CPS_ERR_TORQUE_OFF;
    }

    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_duration_abs(movedata_t servo) {
    cps_err_t ret;
    CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo.id, DXL_TIME_PROFILE));
    CPS_RET_ON_ERR(dxl_servo_move_abs(servo));
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_velocity_abs(movedata_t servo) {
    cps_err_t ret;
    CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo.id, DXL_VELOCITY_PROFILE));
    CPS_RET_ON_ERR(dxl_servo_move_abs(servo));
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move(movedata_t data) {
    cps_err_t ret;
    uint32_t current_pos;
    uint32_t dest;

    CPS_RET_ON_ERR(dxl_get_current_position(data.id, &current_pos));
    data.angle = current_pos + data.angle;
    CPS_RET_ON_ERR(dxl_servo_move_abs(data));

    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_duration(movedata_t servo) {
    cps_err_t ret;
    CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo.id, DXL_TIME_PROFILE));
    CPS_RET_ON_ERR(dxl_servo_move(servo));
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_velocity(movedata_t servo) {
    cps_err_t ret;
    CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo.id, DXL_VELOCITY_PROFILE));
    CPS_RET_ON_ERR(dxl_servo_move(servo));
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_many_abs(movedata_t data[], size_t count) {
    cps_err_t ret;

    //TODO add error handling for groupwrite_num, also add define for length of goal position address

    int groupwrite_num = groupSyncWrite(g_dxl_port_num, DXL_PROTOCOL_VERSION, DXL_ADDR_GoalPosition, 4);

    for (size_t i = 0; i < count; i++) {
        movedata_t *servo = &data[i];

        CPS_RET_ON_ERR(dxl_set_profile_velocity(servo->id, servo->dur));

        uint8_t dxl_addparam_result = groupSyncWriteAddParam(groupwrite_num, servo->id, servo->angle, 4);
        assert(dxl_addparam_result);                //TODO: add error handling here
    }

    groupSyncWriteTxPacket(groupwrite_num);
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    groupSyncWriteClearParam(groupwrite_num);

    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_many_duration_abs(movedata_t data[], size_t count) {
    cps_err_t ret;
    for (size_t i = 0; i < count; i++) {
        movedata_t *servo = &data[i];
        CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo->id, DXL_TIME_PROFILE));
    }

    CPS_RET_ON_ERR(dxl_servo_move_many_abs(data, count));
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_many_velocity_abs(movedata_t data[], size_t count) {
    cps_err_t ret;
    for (size_t i = 0; i < count; i++) {
        movedata_t *servo = &data[i];
        CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo->id, DXL_VELOCITY_PROFILE));
    }

    CPS_RET_ON_ERR(dxl_servo_move_many_abs(data, count));
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_many(movedata_t data[], size_t count) {
    cps_err_t ret;
    uint32_t current_pos;
    uint32_t dest;

    movedata_t abs_data[DXL_MAX_SERVOS];
    if (count > DXL_MAX_SERVOS) {
        return CPS_ERR_ARG;
    }
    memcpy(abs_data, data, sizeof(*data)*count);
    for (size_t i = 0; i < count; i++) {
        CPS_RET_ON_ERR(dxl_get_current_position(abs_data[i].id, &current_pos));
        abs_data[i].angle += current_pos;
    }

    return dxl_servo_move_many_abs(abs_data, count);
}

cps_err_t dxl_servo_move_many_duration(movedata_t data[], size_t count) {
    cps_err_t ret;
    uint32_t current_pos;
    uint32_t dest;

    movedata_t abs_data[DXL_MAX_SERVOS];
    if (count > DXL_MAX_SERVOS) {
        return CPS_ERR_ARG;
    }
    memcpy(abs_data, data, sizeof(*data)*count);
    for (size_t i = 0; i < count; i++) {
        CPS_RET_ON_ERR(dxl_get_current_position(abs_data[i].id, &current_pos));
        abs_data[i].angle += current_pos;
    }

    return dxl_servo_move_many_duration_abs(abs_data, count);
}

cps_err_t dxl_servo_move_many_velocity(movedata_t data[], size_t count) {
    cps_err_t ret;
    uint32_t current_pos;
    uint32_t dest;

    movedata_t abs_data[DXL_MAX_SERVOS];
    if (count > DXL_MAX_SERVOS) {
        return CPS_ERR_ARG;
    }
    memcpy(abs_data, data, sizeof(*data)*count);
    for (size_t i = 0; i < count; i++) {
        CPS_RET_ON_ERR(dxl_get_current_position(abs_data[i].id, &current_pos));
        abs_data[i].angle += current_pos;
    }

    return dxl_servo_move_many_velocity_abs(abs_data, count);
}

cps_err_t dxl_set_id(uint8_t id) {
    write1ByteTxRx2(g_dxl_port_num, 1, DXL_ADDR_Id, id);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_secondary_id(uint8_t id, uint8_t secondaryID) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_SecondaryId, secondaryID);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_min_max_positions(uint8_t id, uint32_t minPos, uint32_t maxPos) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_MinPosition, minPos);
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_MaxPosition, maxPos);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_get_torque(uint8_t id, bool *status) {
    uint8_t tmp;
    tmp = read1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_EnableTorque);
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    if (tmp == 1) {
        *status = true;
    }
    else if (tmp == 0) {
        *status = false;
    }
    else {
        return CPS_ERR_DXL;
    }
    return CPS_ERR_OK;
}

cps_err_t dxl_enable_torque(uint8_t id) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_EnableTorque, 1);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_disable_torque(uint8_t id) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_EnableTorque, 0);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_baudrate(uint8_t id, uint8_t baudRateVal) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_BaudRate, baudRateVal);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_goal_position(uint8_t id, uint32_t goalPosition) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_GoalPosition, goalPosition);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_profile_velocity(uint8_t id, uint32_t velocity) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_ProfileVelocity, velocity);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_profile_acceleration(uint8_t id, uint32_t acceleration) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_ProfileAcceleration, acceleration);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_set_drive_mode(uint8_t id, uint8_t driveMode) {
    bool torque;
    dxl_get_torque(id, &torque);
    if (torque)
        return CPS_ERR_TORQUE_ON;
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_DriveMode, driveMode);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}

cps_err_t dxl_get_drive_mode(uint8_t id, uint8_t *result) {
    uint8_t tmp;

    tmp = read1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_DriveMode);
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    *result = tmp;
    return CPS_ERR_OK;
}

cps_err_t dxl_get_current_position(uint8_t id, uint32_t *result) {
    uint32_t tmp;

    tmp = read4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_PresentPosition);
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    *result = tmp;
    return CPS_ERR_OK;
}

cps_err_t dxl_get_current_velocity(uint8_t id, uint32_t *result) {
    uint32_t tmp;

    tmp = read4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_PresentVelocity);
    // TODO: why div 12?
    tmp /= 12;
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    *result = tmp;
    return CPS_ERR_OK;
}

cps_err_t dxl_get_current_input_voltage(uint8_t id, uint16_t *result) {
    uint16_t tmp;

    tmp = read2ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_PresentInputVoltage);
    // TODO: why mul 10?
    tmp *= 10;
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    *result = tmp;
    return CPS_ERR_OK;
}

cps_err_t dxl_get_is_moving(uint8_t id, uint8_t *result) {
    uint8_t tmp;

    tmp = read1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_Moving);
    // TODO: why mul 10?
    tmp *= 10;
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    *result = tmp;
    return CPS_ERR_OK;
}

cps_err_t dxl_set_drive_mode_safe(uint8_t id, uint8_t driveMode) {
    cps_err_t ret;

    bool torque;
    CPS_RET_ON_ERR(dxl_get_torque(id, &torque));

    if (torque) {
        // In order to change drive mode, which is located in the EEPROM data storage, we need to disable torqe
        CPS_RET_ON_ERR(dxl_disable_torque(id));
    }
    CPS_RET_ON_ERR(dxl_set_drive_mode(id, driveMode));
    if (torque) {
        // Enable torque again
        CPS_RET_ON_ERR(dxl_enable_torque(id));
    }

    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
}
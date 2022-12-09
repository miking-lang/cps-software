#include <dynamixel_sdk/dynamixel_sdk.h>
#include <dynamixel_sdk/protocol2_packet_handler.h>
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

cps_err_t dxl_get_error(void) {
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
        fprintf(stderr, "comm_result:  %d, %s\n", getTxRxResult2(comm_result));
    }
    if (comm_error != 0) {
        fprintf(stderr, "comm_error: %s\n", getRxPacketError2(comm_error));
    }
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
    cps_err_t ret = DXL_ERR_OK;

    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_MinPosition, minPos);
    if ((ret = dxl_get_error()) != DXL_ERR_OK)
        return ret;
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_MaxPosition, maxPos);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
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
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_DriveMode, driveMode);
    return (dxl_get_error() == DXL_ERR_OK) ? CPS_ERR_OK : CPS_ERR_DXL;
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
    tmp *= 10;
    if (dxl_get_error() != DXL_ERR_OK)
        return CPS_ERR_DXL;

    *result = tmp;
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_duration(uint8_t id, uint32_t angle, uint32_t duration) {
    cps_err_t ret;
    uint32_t current_pos;

    CPS_RET_ON_ERR(dxl_get_current_position(id, &current_pos));
    angle += current_pos;

    // In order to change drive mode, which is located in the EEPROM data storage, we need to disable torqe
    CPS_RET_ON_ERR(dxl_disable_torque(id));

    //Set current drive mode to time profile
    CPS_RET_ON_ERR(dxl_set_drive_mode(id, DXL_TIME_PROFILE));

    // Enable torque again
    CPS_RET_ON_ERR(dxl_enable_torque(id));
    // Set the duration, which is the profile velocity when in time profile
    CPS_RET_ON_ERR(dxl_set_profile_velocity(id, duration));

    // Profile acceleration represents the time during which to accelerate, I set this to 1/5th of the total time:
    CPS_RET_ON_ERR(dxl_set_profile_acceleration(id, duration/5));

    CPS_RET_ON_ERR(dxl_set_goal_position(id, angle));

    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_duration_abs(uint8_t id, uint32_t angle, uint32_t duration) {
    cps_err_t ret;

    // In order to change drive mode, which is located in the EEPROM data storage, we need to disable torqe
    CPS_RET_ON_ERR(dxl_disable_torque(id));

    //Set current drive mode to time profile
    CPS_RET_ON_ERR(dxl_set_drive_mode(id, DXL_TIME_PROFILE));

    // Enable torque again
    CPS_RET_ON_ERR(dxl_enable_torque(id));
    // Set the duration, which is the profile velocity when in time profile
    CPS_RET_ON_ERR(dxl_set_profile_velocity(id, duration));

    // Profile acceleration represents the time during which to accelerate, I set this to 1/5th of the total time:
    CPS_RET_ON_ERR(dxl_set_profile_acceleration(id, duration/5));

    CPS_RET_ON_ERR(dxl_set_goal_position(id, angle));

    return CPS_ERR_OK;
}

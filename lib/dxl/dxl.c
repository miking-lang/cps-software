#include <dynamixel_sdk/dynamixel_sdk.h>
#include <dynamixel_sdk/protocol2_packet_handler.h>
#include "dxl.h"

PacketData *packetData = {0};
int g_used_port_num = 0;
uint8_t *g_is_using = NULL;

int g_dxl_port_num = -1;

dxl_err_t dxl_init(const char *tty) {
    // Initialize PortHandler Structs
    // Set the port path
    // Get methods and members of PortHandlerLinux
    g_dxl_port_num = portHandler(tty);

    // Initialize PacketHandler Structs
    packetHandler();

    if (!openPort(g_dxl_port_num))
        return DXL_ERR_FAIL;

    return DXL_ERR_OK;
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
        fprintf(stderr, "comm_result:  %d, %s\n", getTxRxResult2(comm_result));
    }
    if (comm_error != 0) {
        fprintf(stderr, "comm_error: %s\n", getRxPacketError2(comm_error));
    }
}

dxl_err_t dxl_set_id(uint8_t id) {
    write1ByteTxRx2(g_dxl_port_num, 1, DXL_ADDR_Id, id);
    return dxl_get_error();
}

dxl_err_t dxl_set_secondary_id(uint8_t id, uint8_t secondaryID) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_SecondaryId, secondaryID);
    return dxl_get_error();
}

dxl_err_t dxl_set_min_max_positions(uint8_t id, uint32_t minPos, uint32_t maxPos) {
    dxl_err_t ret = DXL_ERR_OK;

    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_MinPosition, minPos);
    if ((ret = dxl_get_error()) != DXL_ERR_OK)
        return ret;
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_MaxPosition, maxPos);
    return dxl_get_error();
}

dxl_err_t dxl_enable_torque(uint8_t id) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_EnableTorque, 1);
    return dxl_get_error();
}

dxl_err_t dxl_disable_torque(uint8_t id) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_EnableTorque, 0);
    return dxl_get_error();
}

dxl_err_t dxl_set_baudrate(uint8_t id, uint8_t baudRateVal) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_BaudRate, baudRateVal);
    return dxl_get_error();
}

dxl_err_t dxl_set_goal_position(uint8_t id, uint32_t goalPosition) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_GoalPosition, goalPosition);
    return dxl_get_error();
}

dxl_err_t dxl_set_profile_velocity(uint8_t id, uint32_t velocity) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_ProfileVelocity, velocity);
    return dxl_get_error();
}

dxl_err_t dxl_set_profile_acceleration(uint8_t id, uint32_t acceleration) {
    write4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_ProfileAcceleration, acceleration);
    return dxl_get_error();
}

dxl_err_t dxl_set_drive_mode(uint8_t id, uint8_t driveMode) {
    write1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_DriveMode, driveMode);
    return dxl_get_error();
}

dxl_err_t dxl_get_current_position(uint8_t id, uint32_t *result) {
    dxl_err_t ret;
    uint32_t tmp;

    tmp = read4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_PresentPosition);
    if ((ret = dxl_get_error()) != DXL_ERR_OK)
        return ret;
    else
        *result = tmp;
}

dxl_err_t dxl_get_current_velocity(uint8_t id, uint32_t *result) {
    dxl_err_t ret;
    uint32_t tmp;

    tmp = read4ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_PresentVelocity);
    // TODO: why div 12?
    tmp /= 12;
    if ((ret = dxl_get_error()) != DXL_ERR_OK)
        return ret;
    else
        *result = tmp;
}

dxl_err_t dxl_get_current_input_voltage(uint8_t id, uint16_t *result) {
    dxl_err_t ret;
    uint16_t tmp;

    tmp = read2ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_PresentInputVoltage);
    // TODO: why mul 10?
    tmp *= 10;
    if ((ret = dxl_get_error()) != DXL_ERR_OK)
        return ret;
    else
        *result = tmp;
}

dxl_err_t dxl_get_is_moving(uint8_t id, uint8_t *result) {
    dxl_err_t ret;
    uint8_t tmp;

    tmp = read1ByteTxRx2(g_dxl_port_num, id, DXL_ADDR_Moving);
    tmp *= 10;
    if ((ret = dxl_get_error()) != DXL_ERR_OK)
        return ret;
    else
        *result = tmp;
}

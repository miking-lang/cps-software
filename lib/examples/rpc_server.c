#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>

#include "rpc.h"
#include "dxl.h"

#ifdef MOCK_DXL

cps_err_t dxl_check_drive_mode_and_torque_on(uint8_t id, uint8_t wantedDriveMode);

// mock
bool servo_torques[12] = {0};
uint8_t servo_modes[12] = {0};
uint32_t servo_profiles[12] = {0};
uint32_t servo_positions[12] = {0};

cps_err_t dxl_init(const char *tty) {
    (void)tty;
    return CPS_ERR_OK;
}

cps_err_t dxl_get_current_position(uint8_t id, uint32_t *result) {
    *result = servo_positions[id];

    return CPS_ERR_OK;
}

cps_err_t dxl_get_torque(uint8_t id, bool *status) {
    *status = servo_torques[id];
    return CPS_ERR_OK;
}

cps_err_t dxl_disable_torque(uint8_t id) {
    servo_torques[id] = false;
    return CPS_ERR_OK;
}

cps_err_t dxl_enable_torque(uint8_t id) {
    servo_torques[id] = true;
    return CPS_ERR_OK;
}

cps_err_t dxl_set_drive_mode(uint8_t id, uint8_t driveMode) {
    bool torque;
    dxl_get_torque(id, &torque);
    if (torque)
        return CPS_ERR_TORQUE_ON;
    servo_modes[id] = driveMode;
    return CPS_ERR_OK;
}

cps_err_t dxl_get_drive_mode(uint8_t id, uint8_t *result) {
    *result = servo_modes[id];
    return CPS_ERR_OK;
}

cps_err_t dxl_set_profile_velocity(uint8_t id, uint32_t velocity) {
    servo_profiles[id] = velocity;
    return CPS_ERR_OK;
}

cps_err_t dxl_servo_move_many_abs(movedata_t data[], size_t count) {
    cps_err_t ret;

    for (size_t i = 0; i < count; i++) {
        movedata_t *servo = &data[i];
        printf("%d: id: %d angle: %d dur: %d\n", i, servo->id, servo->angle, servo->dur);

        CPS_RET_ON_ERR(dxl_set_profile_velocity(servo->id, servo->dur));
    }

    return CPS_ERR_OK;
}
// end mock

// copied in
cps_err_t dxl_servo_move_many_duration(movedata_t data[], size_t count) {
    cps_err_t ret;
    uint32_t current_pos;

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

cps_err_t dxl_servo_move_many_duration_abs(movedata_t data[], size_t count) {
    cps_err_t ret;
    for (size_t i = 0; i < count; i++) {
        movedata_t *servo = &data[i];
        CPS_RET_ON_ERR(dxl_check_drive_mode_and_torque_on(servo->id, DXL_TIME_PROFILE));
    }

    CPS_RET_ON_ERR(dxl_servo_move_many_abs(data, count));
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
// end copied in
#endif

int main(void) {
    cps_err_t ret;

    CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
    puts("DXL connected");

    CPS_ERR_CHECK(cps_rpc_server_init("0.0.0.0", 27272));
    puts("server initialized");
    CPS_ERR_CHECK(cps_rpc_server_accept());
    puts("client accepted");

    while (true) {
        uint32_t fn;
        CPS_ERR_CHECK(cps_rpc_read_fn(&fn));
        printf("fn: 0x%x\n", fn);
        CPS_ERR_CHECK(cps_rpc_handle(fn));
    }

    return 0;
}
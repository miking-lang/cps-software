#include "dxl.h"
#include "ctrl.h"
#include "positions.h"

#include "rpc.h"

#define NUM_SERVOS 12

cps_err_t spider_init(void) {
    cps_err_t ret;
    for (int id = 1; id <= NUM_SERVOS; id++) {
        /* make sure torque is disabled */
        CPS_RET_ON_ERR(dxl_disable_torque(id));
        CPS_RET_ON_ERR(dxl_set_drive_mode(id, DXL_TIME_PROFILE));
        CPS_RET_ON_ERR(dxl_enable_torque(id));
    }

    return CPS_ERR_OK;
}

void do_pushups(int count) {
    cmd_exec(lay_limbs, sizeof(lay_limbs)/sizeof(*lay_limbs));
    cmd_exec(prepare_push_up, sizeof(prepare_push_up)/sizeof(*prepare_push_up));
    for(int i = 0; i < count; i++){
        cmd_exec(push_up, sizeof(push_up)/sizeof(*push_up));
    }
    cmd_exec(exit_push_up, sizeof(exit_push_up)/sizeof(*exit_push_up));
}

void do_wave(void) {
    cmd_exec(lay_limbs, sizeof(lay_limbs)/sizeof(*lay_limbs));
    cmd_exec(lay2stand, sizeof(lay2stand)/sizeof(*lay2stand));
    cmd_exec(wave_shoulder, sizeof(wave_shoulder)/sizeof(*wave_shoulder));
    cmd_exec(stand2lay, sizeof(stand2lay)/sizeof(*stand2lay));
}

int main(void) {
    cps_err_t ret;
    // RPC
    CPS_ERR_CHECK(cps_rpc_client_init("127.0.0.1", 27272));
    // TODO: RPC cannot handle C-string yet
    // CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
    CPS_ERR_CHECK(spider_init());

    // uncomment ONE of these to perform the desired action sequence
    // do_pushups(3);
    do_wave();

    return 0;
}

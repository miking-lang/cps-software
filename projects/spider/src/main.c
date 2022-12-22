#include <stdio.h>
#include <stdlib.h>
// #include <unistd.h>
#include <errno.h>
#include <time.h>
// #include <string.h>
#include "dxl.h"
#include "positions.h"

int msdelay(long tms) {
    struct timespec ts;
    int ret;

    if (tms < 0)
    {
        errno = EINVAL;
        return -1;
    }

    ts.tv_sec = tms / 1000;
    ts.tv_nsec = (tms % 1000) * 1000000;

    do {
        ret = nanosleep(&ts, &ts);
    } while (ret && errno == EINTR);

    return ret;
}

uint8_t all_ids[12] = {
    FL_ROTATE_SHOULDER, FR_ROTATE_SHOULDER, BL_ROTATE_SHOULDER, BR_ROTATE_SHOULDER,
    FL_LIFT_SHOULDER, FR_LIFT_SHOULDER, BL_LIFT_SHOULDER, BR_LIFT_SHOULDER,
    FL_ELBOW, FR_ELBOW, BL_ELBOW, BR_ELBOW};

void spider_disable_all_torques(void) {
    cps_err_t ret;
    for (uint8_t i = 1; i <= 12; i++) {
        CPS_ERR_CHECK(dxl_disable_torque(i));
    }
}

int spider_init(uint8_t driveMode) {
    cps_err_t ret;
    for (int i = 0; i < 12; i++) {
        CPS_RET_ON_ERR(dxl_set_drive_mode(all_ids[i], driveMode));
        CPS_RET_ON_ERR(dxl_enable_torque(all_ids[i]));
    }
    return 0;
}

int spider_get_drive_mode() {
    cps_err_t ret;
    for (int i = 0; i < 12; i++) {
        uint8_t driveMode;
        CPS_RET_ON_ERR(dxl_get_drive_mode(all_ids[i], &driveMode));
        //printf("driveMode %d: %d\n", all_ids[i], driveMode);
    }
    //printf("\n");
    return 0;
}

#include <dynamixel_sdk/dynamixel_sdk.h>
#include <dynamixel_sdk/protocol2_packet_handler.h>

void ask_quit(const char *prompt) {
    //return; //uncomment to make it skip waiting for input
    puts(prompt);
    if (getc(stdin) == 'q')
        exit(0);
    return;
}

void cmd_exec(cmd_t commands[], size_t count) {
    cps_err_t ret;
    for (size_t i = 0; i < count; i++) {
        cmd_t *cmd = &commands[i];
        switch (cmd->cmd_id) {
        case CMD_ID_MOVE_SYNC_ABS: {
            CPS_ERR_CHECK(dxl_servo_move_many_duration_abs((movedata_t *)cmd->argv, cmd->argc));
            break;
        }
        case CMD_ID_MOVE_SYNC_REL:
            CPS_ERR_CHECK(dxl_servo_move_many_duration((movedata_t *)cmd->argv, cmd->argc));
            break;
        case CMD_ID_INPUT:
            ask_quit((const char *)cmd->argv);
            break;
        case CMD_ID_DELAY:
            msdelay(*(size_t*)cmd->argv);
            break;
        default:
            abort();
        }
    }
}


int read_all(int duration){
	cps_err_t ret;
	uint32_t current_pos;

	uint32_t positions[12];

	//Outer Shoulders 
	CPS_RET_ON_ERR(dxl_get_current_position(FL_ROTATE_SHOULDER, &current_pos));
	positions[0] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(FR_ROTATE_SHOULDER, &current_pos));
	positions[1] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(BL_ROTATE_SHOULDER, &current_pos));
	positions[2] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(BR_ROTATE_SHOULDER, &current_pos));
	positions[3] = current_pos;


	//Inner Shoulders
	CPS_RET_ON_ERR(dxl_get_current_position(FL_LIFT_SHOULDER, &current_pos));
	positions[4] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(FR_LIFT_SHOULDER, &current_pos));
	positions[5] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(BL_LIFT_SHOULDER, &current_pos));
	positions[6] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(BR_LIFT_SHOULDER, &current_pos));
	positions[7] = current_pos;

	//Elbows
	CPS_RET_ON_ERR(dxl_get_current_position(FL_ELBOW, &current_pos));
	positions[8] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(FR_ELBOW, &current_pos));
	positions[9] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(BL_ELBOW, &current_pos));
	positions[10] = current_pos;

	CPS_RET_ON_ERR(dxl_get_current_position(BR_ELBOW, &current_pos));
	positions[11] = current_pos;

	printf("uint32_t positions[12] = {%d", positions[0]);
	for(int i = 1; i < 12; i++){
		printf(", %d", positions[i]);
	}
	printf("};\n");

	printf("uint32_t durations[12] = {%d", duration);
	for(int i = 1; i < 12; i++){
		printf(", %d", duration);
	}
	printf("};\n");

	return 0;
}

/*
int martin() {
	cps_err_t ret;
	char c;
    size_t rest_duration = 700;
    size_t duration = 700;
    uint32_t restDurations[12] = {rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration};
	uint32_t restPositions[12] = {2384, 1684, 1759, 2332, 1235, 1307, 1316, 1376, 429, 3443, 3642, 687};

    uint32_t standPositions[8] = {2486, 2534, 2475, 2516, 1497, 2499, 2732, 1508};
    uint32_t standDurations[8] = {duration, duration, duration, duration, duration, duration, duration, duration};

	c = getc(stdin);
	if(c == 'q'){
		spider_disable_all_torques();
		return 0;
	}
	
	CPS_ERR_CHECK(dxl_servo_move_many_duration_abs(12, all_ids, restPositions, restDurations));
	
	c = getc(stdin);
	if(c == 'q'){
		spider_disable_all_torques();
		return 0;
    }
    do {
        CPS_ERR_CHECK(dxl_servo_move_many_duration_abs(8, all_ids+4, standPositions, standDurations));
        c = getc(stdin);
        if(c == 'q'){
            spider_disable_all_torques();
            return 0;
        }

        //Back to resting position
        CPS_ERR_CHECK(dxl_servo_move_many_duration_abs(12, all_ids, restPositions, restDurations));
        c = getc(stdin);
    } while(c != 'q');

    spider_disable_all_torques();

	return 0;
}
*/
/*
void martin_repeat(int repetitions){
    cps_err_t ret;
	char c;
    size_t rest_duration = 700;
    size_t duration = 700;
    uint32_t restDurations[12] = {rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration, rest_duration};
	uint32_t restPositions[12] = {2384, 1684, 1759, 2332, 1235, 1307, 1316, 1376, 429, 3443, 3642, 687};

    uint32_t standPositions[8] = {2486, 2534, 2475, 2516, 1497, 2499, 2732, 1508};
    uint32_t standDurations[8] = {duration, duration, duration, duration, duration, duration, duration, duration};

	sleep(1);
	
	CPS_ERR_CHECK(dxl_servo_move_many_duration_abs(12, all_ids, restPositions, restDurations));
	sleep(1);


    for(int i = 0; i < repetitions; i++){
        CPS_ERR_CHECK(dxl_servo_move_many_duration_abs(8, all_ids+4, standPositions, standDurations));
        sleep(1);

        //Back to resting position
        CPS_ERR_CHECK(dxl_servo_move_many_duration_abs(12, all_ids, restPositions, restDurations));
        sleep(1);
    }
}
*/


void push_up_x3(void) {
    cmd_exec(prepare_push_up, sizeof(prepare_push_up)/sizeof(*prepare_push_up));
    for(int i = 0; i < 3; i++){
        cmd_exec(push_up, sizeof(push_up)/sizeof(*push_up));
    }
    cmd_exec(exit_push_up, sizeof(exit_push_up)/sizeof(*exit_push_up));
    return;
}

void nr1(void) {
    for (int i = 0; i < 2; i++) {
        cmd_exec(lay2stand, sizeof(lay2stand)/sizeof(*lay2stand));
        printf("starting");
        spider_get_drive_mode();
        printf("ending");
        cmd_exec(wave_shoulder, sizeof(wave_shoulder)/sizeof(*wave_shoulder));
        //cmd_exec(wave_elbow, sizeof(wave_elbow)/sizeof(*wave_elbow));
        cmd_exec(stand2lay, sizeof(stand2lay)/sizeof(*stand2lay));
    }
    return;
}
/*
void nr2(void) {
    cps_err_t ret;
    cmd_exec(base_position, sizeof(base_position)/sizeof(*base_position));
    martin_repeat(5);
    cmd_exec(lay_limbs, sizeof(lay_limbs)/sizeof(*lay_limbs));
    return;
}
*/

int main(void) {
    cps_err_t ret;
    CPS_ERR_CHECK(dxl_init("/dev/ttyUSB0"));
    spider_init(DXL_TIME_PROFILE);
    cmd_exec(lift_FR_ELBOW, sizeof(lift_FR_ELBOW)/sizeof(*lift_FR_ELBOW));
    return 0;
}
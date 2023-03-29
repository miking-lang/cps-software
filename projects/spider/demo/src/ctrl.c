#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>

#include "dxl.h"
#include "ctrl.h"

/**
 * Uses the time.h function nanosleep to sleep for tms milliseconds.
 * 
 * @param tms milliseconds to sleep
 * @return int 0 on successfully sleeping for tms milliseconds, -1 otherwise. errno is set to indicate the error.
 */
int msdelay(long tms) {
    struct timespec ts;
    int ret;

    if (tms < 0) {
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

/**
 * Waits for input before continuing.
 * 
 * Exits the program if q is inserted. Continues with the commands on any other input.
 * 
 * @param prompt message to prompt before waiting for input
 */
void ask_quit(const char *prompt) {
    //return; //uncomment to make it skip waiting for input
    puts(prompt);
    if (getc(stdin) == 'q')
        exit(0);
    return;
}

/**
 * Executes an array of cmd_t commands.
 * 
 * The commands are executed in the order they appear in the array.
 * 
 * @param commands an array of cmd_t commands
 * @param count number of cmd_t commands
 */
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

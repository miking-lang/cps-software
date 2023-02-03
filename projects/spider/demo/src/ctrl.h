#pragma once
typedef enum {
    BR_ROTATE_SHOULDER = 1,
    BR_LIFT_SHOULDER,
    FR_ELBOW,
    FR_ROTATE_SHOULDER,
    BR_ELBOW,
    FR_LIFT_SHOULDER, 
    BL_LIFT_SHOULDER,
    FL_ROTATE_SHOULDER,
    BL_ROTATE_SHOULDER,
    FL_ELBOW,
    FL_LIFT_SHOULDER,
    BL_ELBOW,
} servos;

typedef struct {
    uint8_t cmd_id;
    size_t argc;
    void *argv;
} cmd_t;

enum {
    CMD_ID_MOVE_SYNC_ABS,
    CMD_ID_MOVE_SYNC_REL,
    CMD_ID_INPUT,
    CMD_ID_DELAY,
};

void cmd_exec(cmd_t commands[], size_t count);

#define COUNT_VARARGS(type, _argv...) (sizeof((type[]){_argv})/sizeof(*(type[]){_argv}))
#define CMD_MOVE_SYNC_ABS(_argv...) \
{   .cmd_id = CMD_ID_MOVE_SYNC_ABS, \
    .argc = COUNT_VARARGS(movedata_t, _argv), \
    .argv = &(movedata_t[]){_argv} }

#define CMD_MOVE_SYNC_REL(_argv...) \
{   .cmd_id = CMD_ID_MOVE_SYNC_REL, \
    .argc = COUNT_VARARGS(movedata_t, _argv), \
    .argv = &(movedata_t[]){_argv} }

#define CMD_INPUT(prompt) { \
    .cmd_id = CMD_ID_INPUT, .argv = prompt }

#define CMD_DELAY(ms) { \
    .cmd_id = CMD_ID_DELAY, .argv = (size_t[]){ms} }

// Turn on or off debug-delays
// #define CMD_DELAYDBG
#define CMD_DELAYDBG CMD_DELAY
